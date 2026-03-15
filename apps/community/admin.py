"""
社区模块后台管理配置

本模块配置了社区相关模型在 Django Admin 后台的显示和管理方式。
"""

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

    # 列表页显示字段
    list_display = [
        'id', 'user', 'content_preview', 'likes', 'comments_count', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 筛选器
    list_filter = ['created_at']

    # 搜索字段
    search_fields = ['user__username', 'content']

    # 只读字段
    readonly_fields = ['likes', 'comments_count', 'created_at', 'images_display']

    # 字段分组
    fieldsets = [
        ('用户信息', {
            'fields': ['user']
        }),
        ('动态内容', {
            'fields': ['content', 'images', 'images_display', 'recipe']
        }),
        ('统计信息', {
            'fields': ['likes', 'comments_count'],
            'classes': ['collapse']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]

    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    actions = ['sync_likes']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')

    content_preview.short_description = '内容预览'

    def images_display(self, obj):
        """将 JSON 图片列表渲染为可点击的缩略图链接"""
        if not obj.images:
            return '（无图片）'
        links = []
        for i, url in enumerate(obj.images, 1):
            links.append(
                f'<a href="{url}" target="_blank" style="margin-right:8px;">'
                f'图片{i}</a>'
            )
        return format_html(''.join(links))

    images_display.short_description = '图片预览'

    def sync_likes(self, request, queryset):
        """以 PostLike 实际记录数重新计算 likes 字段，修正不同步问题"""
        count = 0
        for post in queryset:
            actual = PostLike.objects.filter(post=post).count()
            if post.likes != actual:
                post.likes = actual
                post.save(update_fields=['likes'])
                count += 1
        self.message_user(request, f'已同步 {count} 条动态的点赞数')

    sync_likes.short_description = '同步点赞数（以实际记录为准）'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    评论管理类

    支持按目标类型筛选，显示父评论回复关系。
    """

    # 列表页显示字段
    list_display = [
        'id', 'user', 'target_type', 'target_id', 'content_preview', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 筛选器
    list_filter = ['target_type', 'created_at']

    # 搜索字段
    search_fields = ['user__username', 'content']

    # 只读字段
    readonly_fields = ['created_at']

    # 字段分组
    fieldsets = [
        ('基本信息', {
            'fields': ['user', 'target_type', 'target_id']
        }),
        ('评论内容', {
            'fields': ['content', 'parent']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]

    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'parent')

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')

    content_preview.short_description = '内容预览'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    """
    动态点赞管理类

    列表页顶部显示热门动态统计（按点赞数 Top 10）。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = 'admin/community/postlike/change_list.html'

    # 列表页显示字段
    list_display = ['id', 'user', 'post', 'created_at']

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 筛选器（补充时间筛选）
    list_filter = ['created_at']

    # 搜索字段
    search_fields = ['user__username']

    list_per_page = 30
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'post')

    def changelist_view(self, request, extra_context=None):
        """注入热门动态统计数据"""
        hot_posts = list(
            PostLike.objects
            .values('post__id', 'post__user__username', 'post__content')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )
        # 截断内容预览
        for item in hot_posts:
            content = item.get('post__content') or ''
            item['content_preview'] = content[:40] + ('...' if len(content) > 40 else '')

        extra_context = extra_context or {}
        extra_context['hot_posts'] = hot_posts
        return super().changelist_view(request, extra_context=extra_context)
