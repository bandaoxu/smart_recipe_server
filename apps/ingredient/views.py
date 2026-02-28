"""
食材模块视图

本模块定义了食材相关的 API 视图，包括食材列表、详情、搜索、识别等功能。

视图：
    - IngredientListView: 食材列表
    - IngredientDetailView: 食材详情
    - IngredientRecognizeView: 食材识别（上传图片识别）
    - IngredientRecognitionHistoryView: 识别历史记录
    - IngredientSearchView: 食材搜索
    - IngredientSeasonalView: 应季食材
    - IngredientNutritionCalculateView: 营养计算
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db.models import Q

from common.response import success_response, error_response
from common.pagination import StandardResultsSetPagination
from .models import Ingredient, IngredientRecognition
from .serializers import (
    IngredientSerializer,
    IngredientListSerializer,
    IngredientRecognitionSerializer,
    IngredientRecognizeRequestSerializer,
    IngredientNutritionCalculatorSerializer,
    IngredientCreateSerializer
)


class IngredientListView(APIView):
    """
    食材列表视图

    获取食材列表，支持分页、分类过滤。

    请求方法：GET
    权限：所有人可访问（AllowAny）

    查询参数：
        page (int): 页码，默认 1
        page_size (int): 每页数量，默认 20
        category (str): 分类过滤（可选）
        search (str): 搜索关键词（可选）

    响应格式：
        {
            "code": 200,
            "message": "获取食材列表成功",
            "data": {
                "count": 100,
                "next": "http://...?page=2",
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "name": "西红柿",
                        "category": "vegetable",
                        "category_display": "蔬菜",
                        "image_url": "http://...",
                        "calories": 18,
                        "is_seasonal_now": true
                    },
                    ...
                ]
            }
        }

    使用示例：
        GET /api/ingredient/?category=vegetable&page=1&page_size=20
        GET /api/ingredient/?search=西红柿
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        处理获取食材列表请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 食材列表数据
        """
        # 获取所有食材
        queryset = Ingredient.objects.all()

        # 分类过滤
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # 搜索过滤
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = IngredientListSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return success_response(
                data=result.data,
                message='获取食材列表成功'
            )

        # 如果没有分页（数据量很小），直接返回所有数据
        serializer = IngredientListSerializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message='获取食材列表成功'
        )


class IngredientDetailView(APIView):
    """
    食材详情视图

    获取指定食材的详细信息。

    请求方法：GET
    权限：所有人可访问（AllowAny）

    路径参数：
        ingredient_id (int): 食材 ID

    响应格式：
        {
            "code": 200,
            "message": "获取食材详情成功",
            "data": {
                "id": 1,
                "name": "西红柿",
                "category": "vegetable",
                "category_display": "蔬菜",
                "image_url": "http://...",
                "calories": 18,
                "protein": 0.9,
                "fat": 0.2,
                "carbohydrate": 3.9,
                "fiber": 1.2,
                "vitamin": {"C": 19, "A": 900},
                "description": "富含番茄红素和维生素C",
                "season": [5, 6, 7, 8, 9],
                "is_seasonal_now": true,
                "nutrition_summary": {...},
                "created_at": "2025-01-01T00:00:00Z"
            }
        }

    使用示例：
        GET /api/ingredient/1/
    """

    permission_classes = [AllowAny]

    def get(self, request, ingredient_id):
        """
        处理获取食材详情请求

        参数：
            request: HTTP 请求对象
            ingredient_id: 食材 ID

        返回：
            Response: 食材详情数据
        """
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return error_response(
                message='食材不存在',
                code=404
            )

        serializer = IngredientSerializer(ingredient)
        return success_response(
            data=serializer.data,
            message='获取食材详情成功'
        )


class IngredientRecognizeView(APIView):
    """
    食材识别视图

    上传图片识别食材（AI 功能）。

    请求方法：POST
    权限：需要登录（IsAuthenticated）

    请求参数：
        image_url (str): 图片 URL，必填

    响应格式：
        {
            "code": 200,
            "message": "识别成功",
            "data": {
                "recognition_id": 1,
                "ingredients": [
                    {
                        "name": "西红柿",
                        "confidence": 0.95,
                        "ingredient_id": 1
                    },
                    {
                        "name": "鸡蛋",
                        "confidence": 0.88,
                        "ingredient_id": 2
                    }
                ],
                "total_items": 2
            }
        }

    使用示例：
        POST /api/ingredient/recognize/
        Headers: {"Authorization": "Bearer <access_token>"}
        {
            "image_url": "http://example.com/food.jpg"
        }

    注意：
        这是一个示例实现，实际项目中需要集成真实的 AI 模型。
        目前使用模拟数据返回识别结果。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        处理食材识别请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 识别结果
        """
        # 验证请求数据
        serializer = IngredientRecognizeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='参数错误',
                data=serializer.errors,
                code=400
            )

        image_url = serializer.validated_data['image_url']

        # TODO: 调用 AI 模型识别食材
        # 这里使用模拟数据，实际项目中需要调用真实的 AI 识别服务
        # 例如：result = ai_model.recognize(image_url)

        # 模拟识别结果
        mock_result = {
            'ingredients': [
                {'name': '西红柿', 'confidence': 0.95, 'ingredient_id': 1},
                {'name': '鸡蛋', 'confidence': 0.88, 'ingredient_id': 2}
            ],
            'total_items': 2,
            'processing_time': 1.2
        }

        # 保存识别记录
        recognition = IngredientRecognition.objects.create(
            user=request.user,
            image_url=image_url,
            recognition_result=mock_result
        )

        return success_response(
            data={
                'recognition_id': recognition.id,
                'ingredients': mock_result['ingredients'],
                'total_items': mock_result['total_items']
            },
            message='识别成功'
        )


class IngredientRecognitionHistoryView(APIView):
    """
    食材识别历史记录视图

    获取当前用户的食材识别历史记录。

    请求方法：GET
    权限：需要登录（IsAuthenticated）

    查询参数：
        page (int): 页码，默认 1
        page_size (int): 每页数量，默认 20

    响应格式：
        {
            "code": 200,
            "message": "获取识别历史成功",
            "data": {
                "count": 10,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "id": 1,
                        "user": {"id": 1, "username": "zhangsan"},
                        "image_url": "http://...",
                        "recognition_result": {...},
                        "recognized_ingredients": ["西红柿", "鸡蛋"],
                        "top_ingredient": {"name": "西红柿", "confidence": 0.95},
                        "created_at": "2025-01-01T00:00:00Z"
                    },
                    ...
                ]
            }
        }

    使用示例：
        GET /api/ingredient/history/?page=1
        Headers: {"Authorization": "Bearer <access_token>"}
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        处理获取识别历史请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 识别历史数据
        """
        # 获取当前用户的识别记录
        queryset = IngredientRecognition.objects.filter(user=request.user)

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = IngredientRecognitionSerializer(page, many=True)
            result = paginator.get_paginated_response(serializer.data)
            return success_response(
                data=result.data,
                message='获取识别历史成功'
            )

        serializer = IngredientRecognitionSerializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            message='获取识别历史成功'
        )


class IngredientSearchView(APIView):
    """
    食材搜索视图

    根据关键词搜索食材。

    请求方法：GET
    权限：所有人可访问（AllowAny）

    查询参数：
        q (str): 搜索关键词，必填
        page (int): 页码，默认 1
        page_size (int): 每页数量，默认 20

    响应格式：
        {
            "code": 200,
            "message": "搜索成功",
            "data": {
                "keyword": "西红柿",
                "count": 2,
                "results": [...]
            }
        }

    使用示例：
        GET /api/ingredient/search/?q=西红柿
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        处理食材搜索请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 搜索结果
        """
        keyword = request.query_params.get('q', '').strip()

        if not keyword:
            return error_response(
                message='请输入搜索关键词',
                code=400
            )

        # 搜索食材（名称或描述包含关键词）
        queryset = Ingredient.objects.filter(
            Q(name__icontains=keyword) |
            Q(description__icontains=keyword)
        )

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = IngredientListSerializer(page, many=True)
            return success_response(
                data={
                    'keyword': keyword,
                    'count': paginator.page.paginator.count,
                    'results': serializer.data
                },
                message='搜索成功'
            )

        serializer = IngredientListSerializer(queryset, many=True)
        return success_response(
            data={
                'keyword': keyword,
                'count': queryset.count(),
                'results': serializer.data
            },
            message='搜索成功'
        )


class IngredientSeasonalView(APIView):
    """
    应季食材视图

    获取当前应季的食材列表。

    请求方法：GET
    权限：所有人可访问（AllowAny）

    查询参数：
        month (int): 月份（1-12），可选，默认使用当前月份
        page (int): 页码，默认 1
        page_size (int): 每页数量，默认 20

    响应格式：
        {
            "code": 200,
            "message": "获取应季食材成功",
            "data": {
                "month": 6,
                "count": 15,
                "results": [...]
            }
        }

    使用示例：
        GET /api/ingredient/seasonal/
        GET /api/ingredient/seasonal/?month=6
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        处理获取应季食材请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 应季食材列表
        """
        # 获取月份参数
        month_param = request.query_params.get('month')

        if month_param:
            try:
                month = int(month_param)
                if month < 1 or month > 12:
                    return error_response(
                        message='月份必须在 1-12 之间',
                        code=400
                    )
            except ValueError:
                return error_response(
                    message='月份格式不正确',
                    code=400
                )
        else:
            # 使用当前月份
            import datetime
            month = datetime.datetime.now().month

        # 查询应季食材
        queryset = Ingredient.objects.filter(season__contains=month)

        # 分页
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = IngredientListSerializer(page, many=True)
            return success_response(
                data={
                    'month': month,
                    'count': paginator.page.paginator.count,
                    'results': serializer.data
                },
                message='获取应季食材成功'
            )

        serializer = IngredientListSerializer(queryset, many=True)
        return success_response(
            data={
                'month': month,
                'count': queryset.count(),
                'results': serializer.data
            },
            message='获取应季食材成功'
        )


class IngredientNutritionCalculateView(APIView):
    """
    食材营养计算视图

    根据食材 ID 和重量计算营养成分。

    请求方法：POST
    权限：所有人可访问（AllowAny）

    请求参数：
        ingredient_id (int): 食材 ID，必填
        quantity_grams (float): 重量（克），必填

    响应格式：
        {
            "code": 200,
            "message": "计算成功",
            "data": {
                "ingredient": {
                    "id": 1,
                    "name": "西红柿"
                },
                "quantity_grams": 200,
                "nutrition": {
                    "calories": 36,
                    "protein": 1.8,
                    "fat": 0.4,
                    "carbohydrate": 7.8,
                    "fiber": 2.4
                }
            }
        }

    使用示例：
        POST /api/ingredient/nutrition-calculate/
        {
            "ingredient_id": 1,
            "quantity_grams": 200
        }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        处理营养计算请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 计算结果
        """
        # 验证请求数据
        serializer = IngredientNutritionCalculatorSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message='参数错误',
                data=serializer.errors,
                code=400
            )

        ingredient_id = serializer.validated_data['ingredient_id']
        quantity_grams = serializer.validated_data['quantity_grams']

        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            return error_response(
                message='食材不存在',
                code=404
            )

        # 计算营养成分
        nutrition = ingredient.calculate_nutrition(quantity_grams)

        return success_response(
            data={
                'ingredient': {
                    'id': ingredient.id,
                    'name': ingredient.name
                },
                'quantity_grams': quantity_grams,
                'nutrition': nutrition
            },
            message='计算成功'
        )


class IngredientRecommendView(APIView):
    """基于食材列表推荐食谱"""
    permission_classes = [AllowAny]

    def post(self, request):
        ingredient_names = request.data.get('ingredients', [])
        if not ingredient_names or not isinstance(ingredient_names, list):
            return error_response(message='请提供食材列表', code=400)

        from apps.recipe.models import Recipe, RecipeIngredient
        from apps.recipe.serializers import RecipeListSerializer

        matched_recipe_ids = RecipeIngredient.objects.filter(
            ingredient__name__in=ingredient_names
        ).values_list('recipe_id', flat=True)

        recipes = Recipe.objects.filter(
            id__in=matched_recipe_ids,
            is_published=True
        ).distinct().order_by('-views', '-likes')[:20]

        serializer = RecipeListSerializer(recipes, many=True, context={'request': request})
        return success_response(data=serializer.data)
