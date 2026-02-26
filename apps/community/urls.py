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
    FoodPostsView,
    FoodPostLikeView,
    RecipeCommentsView
)

app_name = 'community'

urlpatterns = [
    # 美食动态
    path('feed/', FoodPostListView.as_view(), name='feed'),
    path('post/', FoodPostCreateView.as_view(), name='post'),
    path('post/<int:post_id>/', FoodPostDetailView.as_view(), name='post-detail'),

    # posts 别名（前端兼容，支持 GET + POST）
    path('posts/', FoodPostsView.as_view(), name='posts-list'),

    # 动态详情（前端调用 /community/posts/{id}/）
    path('posts/<int:post_id>/', FoodPostDetailView.as_view(), name='posts-detail'),

    # 动态点赞
    path('posts/<int:post_id>/like/', FoodPostLikeView.as_view(), name='posts-like'),

    # 食谱评论（前端调用 /community/posts/{recipeId}/comments/）
    path('posts/<int:target_id>/comments/', RecipeCommentsView.as_view(), name='recipe-comments'),

    # 评论
    path('comment/', CommentListView.as_view(), name='comment-list'),
    path('comment/create/', CommentCreateView.as_view(), name='comment-create'),
]
