"""
社区模块路由配置
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
    FoodPostDeleteView,
    FoodPostUpdateView,
    CommentDeleteView,
)

app_name = "community"

urlpatterns = [
    # 动态列表和发布（GET 支持 ?author= 过滤，POST 发布）
    path("posts/", FoodPostsView.as_view(), name="posts-list"),
    # 动态详情
    path("posts/<int:post_id>/", FoodPostDetailView.as_view(), name="posts-detail"),
    # 动态点赞
    path("posts/<int:post_id>/like/", FoodPostLikeView.as_view(), name="posts-like"),
    # 动态删除
    path("posts/<int:post_id>/delete/", FoodPostDeleteView.as_view(), name="posts-delete"),
    # 动态编辑
    path("posts/<int:post_id>/update/", FoodPostUpdateView.as_view(), name="posts-update"),
    # 动态评论（GET 获取评论，POST 发表评论）
    path("posts/<int:target_id>/comments/", PostCommentsView.as_view(), name="posts-comments"),
    # 通用评论接口
    path("comment/", CommentListView.as_view(), name="comment-list"),
    path("comment/create/", CommentCreateView.as_view(), name="comment-create"),
    # 评论删除
    path("comments/<int:comment_id>/", CommentDeleteView.as_view(), name="comment-delete"),
]
