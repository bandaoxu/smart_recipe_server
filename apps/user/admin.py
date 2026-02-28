"""
用户模块后台管理配置

本模块配置了用户模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from .models import UserProfile, Follow


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    用户档案管理类

    配置用户档案在 Django Admin 后台的显示和操作方式。

    功能：
        - 列表页显示关键字段
        - 支持搜索和过滤
        - 只读字段保护
        - 详细的字段分组
    """

    # 列表页显示的字段
    list_display = [
        'id',
        'user',
        'nickname',
        'gender',
        'age',
        'health_goal',
        'daily_calories_target',
        'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user', 'nickname']

    # 列表页右侧过滤器
    list_filter = [
        'gender',
        'health_goal',
        'created_at'
    ]

    # 搜索字段
    search_fields = [
        'user__username',
        'nickname',
        'phone'
    ]

    # 只读字段（不可编辑）
    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    # 字段分组（在详情页中分组显示）
    fieldsets = [
        ('关联用户', {
            'fields': ['user']
        }),
        ('基本信息', {
            'fields': ['nickname', 'avatar', 'gender', 'age', 'phone']
        }),
        ('健康档案', {
            'fields': [
                'dietary_preference',
                'allergies',
                'health_goal',
                'daily_calories_target'
            ]
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']  # 默认折叠
        })
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['id', 'follower', 'following', 'created_at']
    search_fields = ['follower__username', 'following__username']
    list_per_page = 30
    ordering = ['-created_at']
