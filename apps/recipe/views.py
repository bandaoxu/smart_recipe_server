"""
食谱模块视图

本模块定义了食谱相关的 API 视图。

视图：
    - RecipeListView: 食谱列表
    - RecipeDetailView: 食谱详情
    - RecipeCreateView: 创建食谱
    - RecipeUpdateView: 更新食谱
    - RecipeDeleteView: 删除食谱
    - RecipeLikeView: 点赞/取消点赞
    - RecipeFavoriteView: 收藏/取消收藏
    - UserFavoriteListView: 用户收藏列表
    - RecipeSearchView: 食谱搜索
    - RecipeRecommendView: 推荐食谱
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q

from common.response import success_response, error_response
from common.pagination import StandardResultsSetPagination
from common.permissions import IsOwnerOrReadOnly
from .models import Recipe, UserBehavior
from .serializers import (
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCreateSerializer
)


class RecipeListView(APIView):
    """
    食谱列表视图

    获取食谱列表，支持分页、分类过滤、排序。

    请求方法：GET
    权限：所有人可访问
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """获取食谱列表"""
        queryset = Recipe.objects.filter(is_published=True)

        # 分类过滤
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # 难度过滤
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # 菜系过滤
        cuisine_type = request.query_params.get('cuisine_type')
        if cuisine_type:
            queryset = queryset.filter(cuisine_type=cuisine_type)

        # 搜索
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__contains=search)
            )

        # 排序
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = RecipeListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return success_response(data=result.data, message='获取食谱列表成功')

        serializer = RecipeListSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='获取食谱列表成功')


class RecipeDetailView(APIView):
    """
    食谱详情视图

    获取指定食谱的详细信息，包括食材和步骤。

    请求方法：GET
    权限：所有人可访问
    """

    permission_classes = [AllowAny]

    def get(self, request, recipe_id):
        """获取食谱详情"""
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 增加浏览次数
        recipe.increment_views()

        # 记录用户浏览行为（如果已登录）
        if request.user.is_authenticated:
            UserBehavior.objects.create(
                user=request.user,
                recipe=recipe,
                behavior_type='view'
            )

        serializer = RecipeDetailSerializer(recipe)
        return success_response(data=serializer.data, message='获取食谱详情成功')


class RecipeCreateView(APIView):
    """
    创建食谱视图

    创建新食谱，包括食材和步骤。

    请求方法：POST
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """创建食谱"""
        serializer = RecipeCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            recipe = serializer.save()
            detail_serializer = RecipeDetailSerializer(recipe)
            return success_response(
                data=detail_serializer.data,
                message='创建食谱成功'
            )
        else:
            return error_response(
                message='创建失败',
                data=serializer.errors,
                code=400
            )


class RecipeUpdateView(APIView):
    """
    更新食谱视图

    更新指定食谱的信息。

    请求方法：PUT, PATCH
    权限：需要登录，且只有作者可以更新
    """

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def put(self, request, recipe_id):
        """完整更新食谱"""
        return self._update_recipe(request, recipe_id, partial=False)

    def patch(self, request, recipe_id):
        """部分更新食谱"""
        return self._update_recipe(request, recipe_id, partial=True)

    def _update_recipe(self, request, recipe_id, partial=False):
        """更新食谱的内部方法"""
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 检查权限
        if recipe.author != request.user:
            return error_response(message='无权限操作', code=403)

        serializer = RecipeCreateSerializer(
            recipe,
            data=request.data,
            partial=partial,
            context={'request': request}
        )

        if serializer.is_valid():
            recipe = serializer.save()
            detail_serializer = RecipeDetailSerializer(recipe)
            return success_response(
                data=detail_serializer.data,
                message='更新食谱成功'
            )
        else:
            return error_response(
                message='更新失败',
                data=serializer.errors,
                code=400
            )


class RecipeDeleteView(APIView):
    """
    删除食谱视图

    删除指定食谱。

    请求方法：DELETE
    权限：需要登录，且只有作者可以删除
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, recipe_id):
        """删除食谱"""
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 检查权限
        if recipe.author != request.user:
            return error_response(message='无权限操作', code=403)

        recipe.delete()
        return success_response(message='删除食谱成功')


class RecipeLikeView(APIView):
    """
    点赞视图

    点赞或取消点赞食谱。

    请求方法：POST
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        """点赞或取消点赞"""
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 检查是否已点赞
        behavior = UserBehavior.objects.filter(
            user=request.user,
            recipe=recipe,
            behavior_type='like'
        ).first()

        if behavior:
            # 已点赞，取消点赞
            behavior.delete()
            recipe.decrement_likes()
            return success_response(message='取消点赞成功')
        else:
            # 未点赞，添加点赞
            UserBehavior.objects.create(
                user=request.user,
                recipe=recipe,
                behavior_type='like'
            )
            recipe.increment_likes()
            return success_response(message='点赞成功')


class RecipeFavoriteView(APIView):
    """
    收藏视图

    收藏或取消收藏食谱。

    请求方法：POST
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, recipe_id):
        """收藏或取消收藏"""
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 检查是否已收藏
        behavior = UserBehavior.objects.filter(
            user=request.user,
            recipe=recipe,
            behavior_type='favorite'
        ).first()

        if behavior:
            # 已收藏，取消收藏
            behavior.delete()
            recipe.decrement_favorites()
            return success_response(message='取消收藏成功')
        else:
            # 未收藏，添加收藏
            UserBehavior.objects.create(
                user=request.user,
                recipe=recipe,
                behavior_type='favorite'
            )
            recipe.increment_favorites()
            return success_response(message='收藏成功')


class UserFavoriteListView(APIView):
    """
    用户收藏列表视图

    获取当前用户收藏的食谱列表。

    请求方法：GET
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取用户收藏列表"""
        # 获取用户收藏的食谱 ID 列表
        favorite_recipe_ids = UserBehavior.objects.filter(
            user=request.user,
            behavior_type='favorite'
        ).values_list('recipe_id', flat=True)

        # 获取食谱列表
        queryset = Recipe.objects.filter(
            id__in=favorite_recipe_ids,
            is_published=True
        )

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = RecipeListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return success_response(data=result.data, message='获取收藏列表成功')

        serializer = RecipeListSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='获取收藏列表成功')


class RecipeSearchView(APIView):
    """
    食谱搜索视图

    根据关键词搜索食谱。

    请求方法：GET
    权限：所有人可访问
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """搜索食谱"""
        keyword = request.query_params.get('q', '').strip()

        if not keyword:
            return error_response(message='请输入搜索关键词', code=400)

        # 搜索食谱（名称、描述、标签包含关键词）
        queryset = Recipe.objects.filter(
            Q(name__icontains=keyword) |
            Q(description__icontains=keyword) |
            Q(tags__contains=keyword),
            is_published=True
        )

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = RecipeListSerializer(page, many=True)
            return success_response(
                data={
                    'keyword': keyword,
                    'count': paginator.page.paginator.count,
                    'results': serializer.data
                },
                message='搜索成功'
            )

        serializer = RecipeListSerializer(queryset, many=True)
        return success_response(
            data={
                'keyword': keyword,
                'count': queryset.count(),
                'results': serializer.data
            },
            message='搜索成功'
        )


class RecipeRecommendView(APIView):
    """
    推荐食谱视图

    基于用户行为推荐食谱（简单实现）。

    请求方法：GET
    权限：所有人可访问
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """获取推荐食谱"""
        # 简单实现：返回最热门的食谱
        queryset = Recipe.objects.filter(is_published=True).order_by('-views', '-likes')[:20]

        serializer = RecipeListSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='获取推荐食谱成功')
