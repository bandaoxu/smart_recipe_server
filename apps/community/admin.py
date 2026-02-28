"""
社区模块后台管理配置
"""

from django.contrib import admin
from .models import FoodPost, Comment, PostLike


@admin.register(FoodPost)
class FoodPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'content_preview', 'likes', 'comments_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['likes', 'comments_count', 'created_at']
    list_per_page = 20

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = '内容预览'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'target_type', 'target_id', 'content_preview', 'created_at']
    list_filter = ['target_type', 'created_at']
    search_fields = ['user__username', 'content']
    readonly_fields = ['created_at']
    list_per_page = 50

    def content_preview(self, obj):
        return obj.content[:50]
    content_preview.short_description = '内容预览'


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    search_fields = ['user__username']
    list_per_page = 30
    ordering = ['-created_at']
