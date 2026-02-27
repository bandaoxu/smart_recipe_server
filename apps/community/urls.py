"""
社区模块路由配置

路由列表：
    GET/POST  /posts/                   - 获取动态列表 / 发布动态
    GET       /posts/<id>/              - 动态详情
    POST      /posts/<id>/like/         - 点赞/取消点赞
    GET/POST  /posts/<id>/comments/     - 获取评论 / 发表评论
    GET       /comment/                 - 评论列表（通用）
    POST      /comment/create/          - 发表评论（通用）
"""

from django.urls import path
from .views import (
    FoodPostDetailView,
    CommentListView,
    CommentCreateView,
    FoodPostsView,
    FoodPostLikeView,
    RecipeCommentsView,
    PostCommentsView,
)

app_name = "community"

urlpatterns = [
    # 动态列表和发布（GET 获取列表，POST 发布动态）
    path("posts/", FoodPostsView.as_view(), name="posts-list"),
    # 动态详情
    path("posts/<int:post_id>/", FoodPostDetailView.as_view(), name="posts-detail"),
    # 动态点赞
    path("posts/<int:post_id>/like/", FoodPostLikeView.as_view(), name="posts-like"),
    # 动态评论（GET 获取评论，POST 发表评论）
    path(
        "posts/<int:target_id>/comments/",
        PostCommentsView.as_view(),
        name="posts-comments",
    ),
    # 通用评论接口
    path("comment/", CommentListView.as_view(), name="comment-list"),
    path("comment/create/", CommentCreateView.as_view(), name="comment-create"),
]
