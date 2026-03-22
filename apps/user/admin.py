"""
用户模块后台管理配置

本模块配置了用户模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Q, Case, When, Value, F
from django.db.models.functions import TruncDate, Coalesce
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, date
from .models import UserProfile, Follow


class UserProfileInline(admin.StackedInline):
    """
    在 Django 内置 User 详情页中内联编辑用户档案。
    对已有 UserProfile 的用户直接展示；对无档案用户（如 admin）显示空表单，保存后自动创建。
    """

    model = UserProfile
    can_delete = False
    verbose_name_plural = "用户档案"
    extra = 0
    fields = [
        "nickname",
        "avatar",
        "gender",
        "age",
        "phone",
        "dietary_preference",
        "allergies",
        "health_goal",
        "daily_calories_target",
    ]


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
    注意：用户档案会在创建用户时自动创建，不支持手动添加。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = "admin/user/userprofile/change_list.html"

    # 批量操作
    actions = ["repair_missing_profiles"]

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["user"]

    # 列表页显示的字段
    list_display = [
        "id",
        "user",
        "nickname",
        "gender",
        "age",
        "health_goal",
        "daily_calories_target",
        "created_at",
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user", "nickname"]

    # 列表页右侧过滤器
    list_filter = ["gender", "health_goal", "created_at"]

    # 搜索字段
    search_fields = ["user__username", "nickname", "phone"]

    # 只读字段
    readonly_fields = ["created_at", "updated_at"]

    # 字段分组
    fieldsets = [
        (
            "关联用户",
            {
                "fields": ["user"],
                "description": '⚠️ 用户档案会在创建用户时自动创建，不支持手动添加。如需编辑档案，请在"用户"管理页面点击用户名进行编辑。',
            },
        ),
        ("基本信息", {"fields": ["nickname", "avatar", "gender", "age", "phone"]}),
        (
            "健康档案",
            {
                "fields": [
                    "dietary_preference",
                    "allergies",
                    "health_goal",
                    "daily_calories_target",
                ]
            },
        ),
        ("时间信息", {"fields": ["created_at", "updated_at"], "classes": ["collapse"]}),
    ]

    list_per_page = 20
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """禁止手动添加用户档案"""
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def repair_missing_profiles(self, request, queryset):
        """为没有档案的用户创建档案"""
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        count = 0
        for user in users_without_profile:
            UserProfile.objects.get_or_create(user=user)
            count += 1

        self.message_user(request, f"成功为 {count} 个用户创建了档案", messages.SUCCESS)

    repair_missing_profiles.short_description = "修复丢失的用户档案"

    def changelist_view(self, request, extra_context=None):
        """注入用户统计数据：健康目标分布、性别分布、近7日注册趋势"""
        # 健康目标分布
        health_goal_stats = list(
            UserProfile.objects.annotate(
                normalized_health_goal=Case(
                    When(
                        Q(health_goal__isnull=True) | Q(health_goal=""), then=Value("")
                    ),
                    default=F("health_goal"),
                )
            )
            .values("normalized_health_goal")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        health_goal_map = dict(UserProfile.HEALTH_GOAL_CHOICES)
        for item in health_goal_stats:
            goal_value = item["normalized_health_goal"]
            item["label"] = health_goal_map.get(goal_value) or "未设置"
            item["health_goal"] = goal_value

        # 合并所有"未设置"的条目
        unset_count = sum(
            item["count"] for item in health_goal_stats if item["label"] == "未设置"
        )
        if unset_count > 0:
            health_goal_stats = [
                item for item in health_goal_stats if item["label"] != "未设置"
            ]
            health_goal_stats.insert(
                0,
                {
                    "normalized_health_goal": "",
                    "health_goal": "",
                    "label": "未设置",
                    "count": unset_count,
                },
            )

        # 性别分布
        gender_stats = list(
            UserProfile.objects.annotate(
                normalized_gender=Case(
                    When(Q(gender__isnull=True) | Q(gender=""), then=Value("")),
                    default=F("gender"),
                )
            )
            .values("normalized_gender")
            .annotate(count=Count("id"))
            .order_by("normalized_gender")
        )
        gender_map = dict(UserProfile.GENDER_CHOICES)
        for item in gender_stats:
            gender_value = item["normalized_gender"]
            item["label"] = gender_map.get(gender_value) or "未知"
            item["gender"] = gender_value

        # 合并所有"未知"的条目
        unknown_count = sum(
            item["count"] for item in gender_stats if item["label"] == "未知"
        )
        if unknown_count > 0:
            gender_stats = [item for item in gender_stats if item["label"] != "未知"]
            gender_stats.insert(
                0,
                {
                    "normalized_gender": "",
                    "gender": "",
                    "label": "未知",
                    "count": unknown_count,
                },
            )

        # 近7日注册趋势
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=6)

        # 获取近7天的注册数据
        registration_data = dict(
            UserProfile.objects.filter(created_at__gte=seven_days_ago)
            .annotate(reg_date=TruncDate("created_at"))
            .values("reg_date")
            .annotate(count=Count("id"))
            .values_list("reg_date", "count")
        )

        # 生成近7天的完整数据（包括没有注册记录的日期）
        recent_registrations = []
        for i in range(7):
            current_date = seven_days_ago + timedelta(days=i)
            count = registration_data.get(current_date, 0)
            recent_registrations.append(
                {"reg_date": current_date.strftime("%Y-%m-%d"), "count": count}
            )

        extra_context = extra_context or {}
        extra_context["health_goal_stats"] = health_goal_stats
        extra_context["gender_stats"] = gender_stats
        extra_context["recent_registrations"] = recent_registrations

        total_users = User.objects.count()
        total_profiles = UserProfile.objects.count()
        missing_profiles = total_users - total_profiles

        extra_context["total_users"] = total_users
        extra_context["total_profiles"] = total_profiles
        extra_context["missing_profiles"] = missing_profiles

        if missing_profiles > 0:
            extra_context["warning_message"] = (
                f"⚠️ 警告：发现 {missing_profiles} 个用户没有档案！"
            )
        else:
            extra_context["success_message"] = "✅ 所有用户都有档案，数据完整！"

        extra_context["info_message"] = (
            '💡 提示：用户档案会在创建用户时自动创建。如需编辑档案，请在"用户"管理页面点击用户名进行编辑。'
        )
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    关注关系管理类

    列表页顶部显示：关注数 Top 10、粉丝数 Top 10。
    """

    # 自定义列表页模板
    change_list_template = "admin/user/follow/change_list.html"

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["follower", "following"]

    list_display = ["id", "follower", "following", "created_at"]

    list_display_links = ["id", "follower"]

    search_fields = ["follower__username", "following__username"]

    list_filter = ["created_at"]

    list_per_page = 30
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("follower", "following")

    def save_model(self, request, obj, form, change):
        """保存前调用full_clean进行验证"""
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        """注入关注/粉丝排行数据"""
        # 关注数最多的用户（主动关注他人最多）
        top_following = list(
            Follow.objects.values("follower__username")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # 粉丝数最多的用户（被关注最多）
        top_followed = list(
            Follow.objects.values("following__username")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        extra_context = extra_context or {}
        extra_context["top_following"] = top_following
        extra_context["top_followed"] = top_followed
        extra_context["total_follows"] = Follow.objects.count()
        return super().changelist_view(request, extra_context=extra_context)
