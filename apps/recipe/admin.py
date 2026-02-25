"""
食谱模块后台管理配置

本模块配置了食谱相关模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from .models import Recipe, RecipeIngredient, CookingStep, UserBehavior


class RecipeIngredientInline(admin.TabularInline):
    """
    食谱食材内联编辑

    在食谱详情页中可以直接编辑食材列表。
    """
    model = RecipeIngredient
    extra = 1
    fields = ['ingredient', 'quantity', 'unit', 'is_main']


class CookingStepInline(admin.TabularInline):
    """
    烹饪步骤内联编辑

    在食谱详情页中可以直接编辑步骤列表。
    """
    model = CookingStep
    extra = 1
    fields = ['step_number', 'description', 'image_url', 'duration', 'tips']
    ordering = ['step_number']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    食谱管理类

    配置食谱在 Django Admin 后台的显示和操作方式。
    """

    # 内联编辑食材和步骤
    inlines = [RecipeIngredientInline, CookingStepInline]

    # 列表页显示的字段
    list_display = [
        'id', 'name', 'author', 'category', 'difficulty',
        'cooking_time', 'views', 'likes', 'favorites',
        'is_published', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'name']

    # 列表页右侧过滤器
    list_filter = [
        'category', 'difficulty', 'cuisine_type',
        'is_published', 'created_at'
    ]

    # 搜索字段
    search_fields = [
        'name', 'description', 'author__username'
    ]

    # 只读字段
    readonly_fields = [
        'views', 'likes', 'favorites', 'created_at', 'updated_at'
    ]

    # 字段分组
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'cover_image', 'author', 'description']
        }),
        ('分类信息', {
            'fields': ['category', 'cuisine_type', 'difficulty', 'tags']
        }),
        ('详细信息', {
            'fields': ['cooking_time', 'servings', 'total_calories']
        }),
        ('统计信息', {
            'fields': ['views', 'likes', 'favorites'],
            'classes': ['collapse']
        }),
        ('发布设置', {
            'fields': ['is_published']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    """
    用户行为管理类

    配置用户行为在 Django Admin 后台的显示和操作方式。
    """

    # 列表页显示的字段
    list_display = [
        'id', 'user', 'recipe', 'behavior_type', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 列表页右侧过滤器
    list_filter = [
        'behavior_type', 'created_at'
    ]

    # 搜索字段
    search_fields = [
        'user__username', 'recipe__name'
    ]

    # 只读字段
    readonly_fields = [
        'user', 'recipe', 'behavior_type', 'created_at'
    ]

    # 每页显示数量
    list_per_page = 50

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']
