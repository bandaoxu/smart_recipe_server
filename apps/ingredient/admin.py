"""
食材模块后台管理配置

本模块配置了食材模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from .models import Ingredient, IngredientRecognition


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    食材管理类

    配置食材在 Django Admin 后台的显示和操作方式。
    """

    # 列表页显示的字段
    list_display = [
        'id',
        'name',
        'category',
        'calories',
        'protein',
        'fat',
        'carbohydrate',
        'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'name']

    # 列表页右侧过滤器
    list_filter = [
        'category',
        'created_at'
    ]

    # 搜索字段
    search_fields = [
        'name',
        'description'
    ]

    # 只读字段
    readonly_fields = [
        'created_at'
    ]

    # 字段分组
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'category', 'image_url', 'description']
        }),
        ('营养成分（每100g）', {
            'fields': ['calories', 'protein', 'fat', 'carbohydrate', 'fiber', 'vitamin']
        }),
        ('其他信息', {
            'fields': ['season', 'created_at']
        })
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['category', 'name']


@admin.register(IngredientRecognition)
class IngredientRecognitionAdmin(admin.ModelAdmin):
    """
    食材识别记录管理类

    配置食材识别记录在 Django Admin 后台的显示和操作方式。
    """

    # 列表页显示的字段
    list_display = [
        'id',
        'user',
        'get_recognized_count',
        'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 列表页右侧过滤器
    list_filter = [
        'created_at'
    ]

    # 搜索字段
    search_fields = [
        'user__username',
        'image_url'
    ]

    # 只读字段
    readonly_fields = [
        'user',
        'image_url',
        'recognition_result',
        'created_at'
    ]

    # 字段分组
    fieldsets = [
        ('识别信息', {
            'fields': ['user', 'image_url', 'recognition_result']
        }),
        ('时间信息', {
            'fields': ['created_at']
        })
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']

    def get_recognized_count(self, obj):
        """
        获取识别到的食材数量

        参数：
            obj: IngredientRecognition 实例

        返回：
            int: 识别到的食材数量
        """
        return len(obj.get_recognized_ingredients())

    get_recognized_count.short_description = '识别数量'
