"""
用户模块后台管理配置

本模块配置了用户模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import UserProfile, Follow


class UserProfileInline(admin.StackedInline):
    """
    在 Django 内置 User 详情页中内联编辑用户档案。
    对已有 UserProfile 的用户直接展示；对无档案用户（如 admin）显示空表单，保存后自动创建。
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户档案'
    extra = 0
    fields = ['nickname', 'avatar', 'gender', 'age', 'phone',
              'dietary_preference', 'allergies', 'health_goal', 'daily_calories_target']


# 扩展 Django 内置 UserAdmin，嵌入 UserProfileInline
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Django 内置用户管理，新增用户档案内联"""
    inlines = [UserProfileInline]

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    用户档案管理类

    列表页顶部显示：健康目标分布、性别分布、近7日注册趋势。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = 'admin/user/userprofile/change_list.html'

    # 列表页显示的字段
    list_display = [
        'id', 'user', 'nickname', 'gender', 'age',
        'health_goal', 'daily_calories_target', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user', 'nickname']

    # 列表页右侧过滤器
    list_filter = ['gender', 'health_goal', 'created_at']

    # 搜索字段
    search_fields = ['user__username', 'nickname', 'phone']

    # 只读字段
    readonly_fields = ['created_at', 'updated_at']

    # 字段分组
    fieldsets = [
        ('关联用户', {
            'fields': ['user']
        }),
        ('基本信息', {
            'fields': ['nickname', 'avatar', 'gender', 'age', 'phone']
        }),
        ('健康档案', {
            'fields': [
                'dietary_preference', 'allergies',
                'health_goal', 'daily_calories_target'
            ]
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def changelist_view(self, request, extra_context=None):
        """注入用户统计数据：健康目标分布、性别分布、近7日注册趋势"""
        # 健康目标分布
        health_goal_stats = list(
            UserProfile.objects
            .values('health_goal')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        health_goal_map = dict(UserProfile.HEALTH_GOAL_CHOICES)
        for item in health_goal_stats:
            item['label'] = health_goal_map.get(item['health_goal']) or '未设置'

        # 性别分布
        gender_stats = list(
            UserProfile.objects
            .values('gender')
            .annotate(count=Count('id'))
            .order_by('gender')
        )
        gender_map = dict(UserProfile.GENDER_CHOICES)
        for item in gender_stats:
            item['label'] = gender_map.get(item['gender']) or '未知'

        # 近7日注册趋势
        recent_registrations = list(
            UserProfile.objects
            .annotate(reg_date=TruncDate('created_at'))
            .values('reg_date')
            .annotate(count=Count('id'))
            .order_by('-reg_date')[:7]
        )

        extra_context = extra_context or {}
        extra_context['health_goal_stats'] = health_goal_stats
        extra_context['gender_stats'] = gender_stats
        extra_context['recent_registrations'] = recent_registrations
        extra_context['total_users'] = UserProfile.objects.count()
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    关注关系管理类

    列表页顶部显示：关注数 Top 10、粉丝数 Top 10。
    """

    # 自定义列表页模板
    change_list_template = 'admin/user/follow/change_list.html'

    list_display = ['id', 'follower', 'following', 'created_at']

    list_display_links = ['id', 'follower']

    search_fields = ['follower__username', 'following__username']

    list_filter = ['created_at']

    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('follower', 'following')

    def changelist_view(self, request, extra_context=None):
        """注入关注/粉丝排行数据"""
        # 关注数最多的用户（主动关注他人最多）
        top_following = list(
            Follow.objects
            .values('follower__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # 粉丝数最多的用户（被关注最多）
        top_followed = list(
            Follow.objects
            .values('following__username')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        extra_context = extra_context or {}
        extra_context['top_following'] = top_following
        extra_context['top_followed'] = top_followed
        extra_context['total_follows'] = Follow.objects.count()
        return super().changelist_view(request, extra_context=extra_context)
