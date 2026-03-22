"""
营养分析模块 Admin 配置
"""

from django.contrib import admin
from common.admin_mixins import ExportCsvMixin
from .models import DietaryLog


@admin.register(DietaryLog)
class DietaryLogAdmin(ExportCsvMixin, admin.ModelAdmin):
    """
    饮食记录管理类

    配置饮食日记在 Django Admin 后台的显示和操作方式。
    """

    # CSV 导出配置
    export_fields = [
        "id",
        "user",
        "food_name",
        "calories",
        "protein",
        "fat",
        "carbohydrate",
        "fiber",
        "meal_type",
        "date",
    ]
    export_filename = "dietary_logs"

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["user", "recipe"]

    # 列表页显示字段
    list_display = [
        "id",
        "user",
        "get_food_name",
        "calories",
        "meal_type",
        "date",
        "created_at",
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user"]

    # 筛选器
    list_filter = ["meal_type", "date"]

    # 搜索字段
    search_fields = ["user__username", "custom_name", "recipe__name"]

    # 批量操作
    actions = ["export_as_csv"]

    # 只读字段
    readonly_fields = ["created_at"]

    # 字段分组
    fieldsets = [
        ("用户信息", {"fields": ["user"]}),
        ("食物信息", {"fields": ["recipe", "custom_name"]}),
        (
            "营养成分",
            {"fields": ["calories", "protein", "fat", "carbohydrate", "fiber"]},
        ),
        ("记录信息", {"fields": ["meal_type", "date"]}),
        ("时间信息", {"fields": ["created_at"], "classes": ["collapse"]}),
    ]

    date_hierarchy = "date"
    list_per_page = 30
    ordering = ["-date", "meal_type"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "recipe")

    def get_food_name(self, obj):
        return obj.recipe.name if obj.recipe else obj.custom_name

    get_food_name.short_description = "食物名称"
