"""
社区模块后台管理配置

本模块配置了社区相关模型在 Django Admin 后台的显示和管理方式。
"""

import json

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import FoodPost, Comment, PostLike


@admin.register(FoodPost)
class FoodPostAdmin(admin.ModelAdmin):
    """
    美食动态管理类

    支持内容预览、图片列表展示、关联食谱显示。
    """

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["user", "recipe"]

    # 列表页显示字段
    list_display = [
        "id",
        "user",
        "content_preview",
        "likes",
        "comments_count",
        "created_at",
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user"]

    # 筛选器
    list_filter = ["created_at"]

    # 搜索字段
    search_fields = ["user__username", "content"]

    # 只读字段
    readonly_fields = ["likes", "comments_count", "created_at", "images_display"]

    # 字段分组
    fieldsets = [
        ("用户信息", {"fields": ["user"]}),
        ("动态内容", {"fields": ["content", "images", "images_display", "recipe"]}),
        ("统计信息", {"fields": ["likes", "comments_count"], "classes": ["collapse"]}),
        ("时间信息", {"fields": ["created_at"], "classes": ["collapse"]}),
    ]

    list_per_page = 20
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    actions = ["sync_likes"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "recipe")

    def content_preview(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")

    content_preview.short_description = "内容预览"

    def images_display(self, obj):
        """将 JSON 图片列表渲染为可点击的缩略图链接"""
        if not obj.images:
            return "（无图片）"
        links = []
        for i, url in enumerate(obj.images, 1):
            links.append(
                f'<a href="{url}" target="_blank" style="margin-right:8px;">'
                f"图片{i}</a>"
            )
        return format_html("".join(links))

    images_display.short_description = "图片预览"

    def sync_likes(self, request, queryset):
        """以 PostLike 实际记录数重新计算 likes 字段，修正不同步问题"""
        count = 0
        for post in queryset:
            actual = PostLike.objects.filter(post=post).count()
            if post.likes != actual:
                post.likes = actual
                post.save(update_fields=["likes"])
                count += 1
        self.message_user(request, f"已同步 {count} 条动态的点赞数")

    sync_likes.short_description = "同步点赞数（以实际记录为准）"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    评论管理类

    支持按目标类型筛选，显示父评论回复关系，显示回复数量。
    target_id 字段在编辑页面改为联动下拉选择。
    """

    # 自定义编辑页模板（实现字段联动 JavaScript）
    change_form_template = "admin/community/comment/change_form.html"

    # user 使用 autocomplete（同时确保页面加载 Select2 供 target_id 使用）
    autocomplete_fields = ["user"]

    # 列表页显示字段
    list_display = [
        "id",
        "user",
        "target_type",
        "target_display",
        "content_preview",
        "parent_display",
        "replies_count",
        "created_at",
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user"]

    # 筛选器
    list_filter = ["target_type", "created_at"]

    # 搜索字段
    search_fields = ["user__username", "content"]

    # 只读字段
    readonly_fields = ["created_at", "replies_count_display", "parent_preview"]

    # 字段分组
    fieldsets = [
        ("基本信息", {"fields": ["user", "target_type", "target_id", "parent"]}),
        ("评论内容", {"fields": ["content"]}),
        ("回复统计", {"fields": ["replies_count_display"], "classes": ["collapse"]}),
        ("时间信息", {"fields": ["created_at"], "classes": ["collapse"]}),
    ]

    list_per_page = 50
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "parent")
            .annotate(replies_count=Count("replies"))
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制 parent 候选为顶级评论，确保回复层级不超过两层"""
        if db_field.name == "parent":
            kwargs["queryset"] = (
                Comment.objects.filter(parent=None)
                .select_related("user")
                .order_by("-created_at")
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """注入食谱、动态、顶级评论的 JSON 数据，供编辑页 JavaScript 使用"""
        from apps.recipe.models import Recipe

        recipes = [
            {"id": r["id"], "display": f"食谱#{r['id']}: {r['name']}"}
            for r in Recipe.objects.values("id", "name").order_by("id")
        ]
        posts = [
            {
                "id": p["id"],
                "display": f"动态#{p['id']}: {p['content'][:40]}{'...' if len(p['content']) > 40 else ''}",
            }
            for p in FoodPost.objects.values("id", "content").order_by("id")
        ]
        top_comments = [
            {
                "id": c.id,
                "target_type": c.target_type,
                "target_id": c.target_id,
                "display": f"#{c.id} @{c.user.username}: {c.content[:50]}",
            }
            for c in Comment.objects.filter(parent=None)
            .select_related("user")
            .order_by("-created_at")[:500]
        ]
        context.update(
            {
                "recipes_json": json.dumps(recipes, ensure_ascii=False),
                "posts_json": json.dumps(posts, ensure_ascii=False),
                "comments_json": json.dumps(top_comments, ensure_ascii=False),
            }
        )
        return super().render_change_form(
            request, context, add=add, change=change, form_url=form_url, obj=obj
        )

    def content_preview(self, obj):
        return obj.content[:50] + ("..." if len(obj.content) > 50 else "")

    content_preview.short_description = "内容预览"

    def target_display(self, obj):
        """显示目标对象的链接"""
        if obj.target_type == "recipe":
            return format_html(
                '<a href="/admin/recipe/recipe/{}/">食谱 #{}</a>',
                obj.target_id,
                obj.target_id,
            )
        elif obj.target_type == "post":
            return format_html(
                '<a href="/admin/community/foodpost/{}/">动态 #{}</a>',
                obj.target_id,
                obj.target_id,
            )
        return f"{obj.target_id}"

    target_display.short_description = "目标对象"

    def parent_display(self, obj):
        """显示父评论信息"""
        if obj.parent:
            return format_html(
                '<a href="/admin/community/comment/{}/">回复 #{} - {}</a>',
                obj.parent.id,
                obj.parent.id,
                obj.parent.user.username,
            )
        return format_html('<span style="color: green;">顶级评论</span>')

    parent_display.short_description = "回复关系"

    def replies_count(self, obj):
        """显示回复数量"""
        count = obj.replies_count
        if count > 0:
            return format_html(
                '<span style="color: #1890ff; font-weight: bold;">{}</span>', count
            )
        return "-"

    replies_count.short_description = "回复数"

    def replies_count_display(self, obj):
        """详情页显示回复数量"""
        count = obj.replies.count()
        return format_html(
            '<span style="font-size: 16px; font-weight: bold;">{}</span> 条回复', count
        )

    replies_count_display.short_description = "回复统计"

    def parent_preview(self, obj):
        """详情页显示父评论预览"""
        if obj.parent:
            return format_html(
                '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px;">'
                "<strong>用户:</strong> {}<br>"
                "<strong>内容:</strong> {}<br>"
                "<strong>时间:</strong> {}"
                "</div>",
                obj.parent.user.username,
                obj.parent.content[:100]
                + ("..." if len(obj.parent.content) > 100 else ""),
                obj.parent.created_at.strftime("%Y-%m-%d %H:%M"),
            )
        return "（无父评论，这是顶级评论）"

    parent_preview.short_description = "父评论预览"


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    """
    动态点赞管理类

    列表页顶部显示热门动态统计（按点赞数 Top 10）。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = "admin/community/postlike/change_list.html"

    # 使用自动完成字段代替下拉选择框
    autocomplete_fields = ["user", "post"]

    # 列表页显示字段
    list_display = ["id", "user", "post", "created_at"]

    # 列表页可点击进入详情的字段
    list_display_links = ["id", "user"]

    # 筛选器（补充时间筛选）
    list_filter = ["created_at"]

    # 搜索字段
    search_fields = ["user__username"]

    list_per_page = 30
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "post")

    def changelist_view(self, request, extra_context=None):
        """注入热门动态统计数据"""
        hot_posts = list(
            PostLike.objects.values("post__id", "post__user__username", "post__content")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        # 截断内容预览
        for item in hot_posts:
            content = item.get("post__content") or ""
            item["content_preview"] = content[:40] + (
                "..." if len(content) > 40 else ""
            )

        extra_context = extra_context or {}
        extra_context["hot_posts"] = hot_posts
        return super().changelist_view(request, extra_context=extra_context)
