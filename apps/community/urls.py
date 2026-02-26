"""
社区模块路由配置
"""

from django.urls import path
from .views import (
    FoodPostListView,
    FoodPostCreateView,
    FoodPostDetailView,
    CommentListView,
    CommentCreateView,
    FoodPostsView
)

app_name = 'community'

urlpatterns = [
    # 美食动态
    path('feed/', FoodPostListView.as_view(), name='feed'),
    path('post/', FoodPostCreateView.as_view(), name='post'),
    path('post/<int:post_id>/', FoodPostDetailView.as_view(), name='post-detail'),

    # posts 别名（前端兼容，支持 GET + POST）
    path('posts/', FoodPostsView.as_view(), name='posts-list'),

    # 评论
    path('comment/', CommentListView.as_view(), name='comment-list'),
    path('comment/create/', CommentCreateView.as_view(), name='comment-create'),
]
