"""
食材模块后台管理配置

本模块配置了食材模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from common.admin_mixins import ExportCsvMixin
from .models import Ingredient, IngredientRecognition


@admin.register(Ingredient)
class IngredientAdmin(ExportCsvMixin, admin.ModelAdmin):
    """
    食材管理类

    配置食材在 Django Admin 后台的显示和操作方式。
    启用 search_fields 以支持 RecipeIngredientInline 的 autocomplete_fields。
    """

    # CSV 导出配置
    export_fields = [
        "id",
        "name",
        "category",
        "calories",
        "protein",
        "fat",
        "carbohydrate",
        "fiber",
    ]
    export_filename = "ingredients"

    # 自定义编辑页模板（图片上传组件）
    change_form_template = "admin/ingredient/ingredient/change_form.html"

    # 列表页显示的字段
    list_display = [
        "id",
        "name",
        "category",
        "calories",
        "protein",
        "fat",
        "carbohydrate",
        "created_at",
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "name"]

    # 列表页右侧过滤器
    list_filter = ["category", "created_at"]

    # 搜索字段（同时支持 RecipeIngredientInline 的 autocomplete_fields）
    search_fields = ["name", "description"]

    # 批量操作
    actions = ["export_as_csv"]

    # 只读字段
    readonly_fields = ["created_at"]

    # 字段分组
    fieldsets = [
        ("基本信息", {"fields": ["name", "category", "image_url", "description"]}),
        (
            "营养成分（每100g）",
            {"fields": ["calories", "protein", "fat", "carbohydrate", "fiber"]},
        ),
        ("其他信息", {"fields": ["created_at"]}),
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = "created_at"

    # 排序方式
    ordering = ["category", "name"]


@admin.register(IngredientRecognition)
class IngredientRecognitionAdmin(admin.ModelAdmin):
    """
    食材识别记录管理类

    配置食材识别记录在 Django Admin 后台的显示和操作方式。
    列表页顶部显示识别成功率统计。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = "admin/ingredient/ingredientrecognition/change_list.html"

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["user"]

    # 列表页显示的字段
    list_display = ["id", "user", "get_recognized_count", "created_at"]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user"]

    # 列表页右侧过滤器
    list_filter = ["created_at"]

    # 搜索字段
    search_fields = ["user__username", "image_url"]

    # 只读字段
    readonly_fields = ["user", "image_url", "recognition_result", "created_at"]

    # 字段分组
    fieldsets = [
        ("识别信息", {"fields": ["user", "image_url", "recognition_result"]}),
        ("时间信息", {"fields": ["created_at"]}),
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = "created_at"

    # 排序方式
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def get_recognized_count(self, obj):
        return len(obj.get_recognized_ingredients())

    get_recognized_count.short_description = "识别数量"

    def changelist_view(self, request, extra_context=None):
        """注入识别统计数据"""
        total = IngredientRecognition.objects.count()
        if total > 0:
            # recognition_result 是 JSONField，需在 Python 层统计
            records = IngredientRecognition.objects.only("recognition_result")
            success_count = sum(1 for r in records if r.get_recognized_ingredients())
            success_rate = f"{success_count / total * 100:.1f}%"
        else:
            success_count = 0
            success_rate = "0%"

        extra_context = extra_context or {}
        extra_context["total_recognitions"] = total
        extra_context["success_count"] = success_count
        extra_context["success_rate"] = success_rate
        return super().changelist_view(request, extra_context=extra_context)
