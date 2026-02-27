"""
社区模块视图
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from common.response import success_response, error_response
from common.pagination import StandardResultsSetPagination
from .models import FoodPost, Comment, PostLike
from .serializers import FoodPostSerializer, CommentSerializer


class FoodPostListView(APIView):
    """美食动态列表视图"""

    permission_classes = [AllowAny]

    def get(self, request):
        """获取动态列表"""
        queryset = FoodPost.objects.all()

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = FoodPostSerializer(
                page, many=True, context={"request": request}
            )
            result = paginator.get_paginated_response(serializer.data)
            return success_response(data=result.data, message="获取动态列表成功")

        serializer = FoodPostSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data, message="获取动态列表成功")


class FoodPostCreateView(APIView):
    """发布美食动态视图"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """发布动态"""
        serializer = FoodPostSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="发布成功")
        else:
            return error_response(message="发布失败", data=serializer.errors, code=400)


class FoodPostDetailView(APIView):
    """动态详情视图"""

    permission_classes = [AllowAny]

    def get(self, request, post_id):
        """获取动态详情"""
        try:
            post = FoodPost.objects.get(id=post_id)
        except FoodPost.DoesNotExist:
            return error_response(message="动态不存在", code=404)

        serializer = FoodPostSerializer(post, context={"request": request})
        return success_response(data=serializer.data, message="获取动态详情成功")


class CommentListView(APIView):
    """评论列表视图"""

    permission_classes = [AllowAny]

    def get(self, request):
        """获取评论列表"""
        target_type = request.query_params.get("target_type")
        target_id = request.query_params.get("target_id")

        if not target_type or not target_id:
            return error_response(message="缺少参数", code=400)

        queryset = Comment.objects.filter(
            target_type=target_type, target_id=target_id, parent=None  # 只获取顶级评论
        )

        serializer = CommentSerializer(queryset, many=True)
        return success_response(data=serializer.data, message="获取评论列表成功")


class CommentCreateView(APIView):
    """发表评论视图"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """发表评论"""
        serializer = CommentSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            comment = serializer.save()

            # 更新评论数
            if comment.target_type == "post":
                post = FoodPost.objects.filter(id=comment.target_id).first()
                if post:
                    post.comments_count += 1
                    post.save()

            return success_response(data=serializer.data, message="评论成功")
        else:
            return error_response(message="评论失败", data=serializer.errors, code=400)


class FoodPostsView(APIView):
    """美食动态 posts 视图（GET 列表 + POST 发布，前端兼容）"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        """获取动态列表"""
        queryset = FoodPost.objects.all()

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = FoodPostSerializer(
                page, many=True, context={"request": request}
            )
            result = paginator.get_paginated_response(serializer.data)
            return success_response(data=result.data, message="获取动态列表成功")

        serializer = FoodPostSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data, message="获取动态列表成功")

    def post(self, request):
        """发布动态"""
        serializer = FoodPostSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="发布成功")
        else:
            return error_response(message="发布失败", data=serializer.errors, code=400)


class FoodPostLikeView(APIView):
    """动态点赞视图（toggle）"""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = FoodPost.objects.get(id=post_id)
        except FoodPost.DoesNotExist:
            return error_response(message="动态不存在", code=404)

        like = PostLike.objects.filter(user=request.user, post=post).first()
        if like:
            like.delete()
            post.likes = max(0, post.likes - 1)
            post.save()
            return success_response(
                message="取消点赞成功", data={"is_liked": False, "likes": post.likes}
            )
        else:
            PostLike.objects.create(user=request.user, post=post)
            post.likes += 1
            post.save()
            return success_response(
                message="点赞成功", data={"is_liked": True, "likes": post.likes}
            )


class RecipeCommentsView(APIView):
    """食谱评论视图（GET 获取评论列表，POST 发表评论）"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, target_id):
        """获取食谱评论列表"""
        queryset = Comment.objects.filter(
            target_type="recipe", target_id=target_id, parent=None
        ).order_by("created_at")

        serializer = CommentSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data, message="获取评论成功")

    def post(self, request, target_id):
        """发表食谱评论"""
        data = request.data.copy()
        data["target_type"] = "recipe"
        data["target_id"] = target_id

        serializer = CommentSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message="评论成功")
        return error_response(message="评论失败", data=serializer.errors, code=400)


class PostCommentsView(APIView):
    """动态评论视图（GET 获取评论列表，POST 发表评论）"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, target_id):
        """获取动态评论列表"""
        queryset = Comment.objects.filter(
            target_type="post", target_id=target_id, parent=None
        ).order_by("created_at")

        serializer = CommentSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(data=serializer.data, message="获取评论成功")

    def post(self, request, target_id):
        """发表动态评论"""
        data = request.data.copy()
        data["target_type"] = "post"
        data["target_id"] = target_id

        serializer = CommentSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            comment = serializer.save()

            # 更新动态的评论数
            post = FoodPost.objects.filter(id=target_id).first()
            if post:
                post.comments_count = Comment.objects.filter(
                    target_type="post", target_id=target_id, parent=None
                ).count()
                post.save()

            return success_response(data=serializer.data, message="评论成功")
        return error_response(message="评论失败", data=serializer.errors, code=400)
