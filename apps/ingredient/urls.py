"""
食材模块路由配置

本模块定义了食材相关的 URL 路由。

路由列表：
    - GET /                        食材列表
    - GET /<id>/                   食材详情
    - POST /recognize/             食材识别
    - GET /history/                识别历史
    - GET /search/                 食材搜索
    - GET /seasonal/               应季食材
    - POST /nutrition-calculate/   营养计算
"""

from django.urls import path
from .views import (
    IngredientListView,
    IngredientDetailView,
    IngredientRecognizeView,
    IngredientRecognitionHistoryView,
    IngredientSearchView,
    IngredientSeasonalView,
    IngredientNutritionCalculateView,
    IngredientRecommendView
)

# 应用命名空间
app_name = 'ingredient'

urlpatterns = [
    # 食材列表
    # GET /api/ingredient/
    path('', IngredientListView.as_view(), name='list'),

    # 食材详情
    # GET /api/ingredient/<ingredient_id>/
    path('<int:ingredient_id>/', IngredientDetailView.as_view(), name='detail'),

    # 食材识别
    # POST /api/ingredient/recognize/
    path('recognize/', IngredientRecognizeView.as_view(), name='recognize'),

    # 识别历史
    # GET /api/ingredient/history/
    path('history/', IngredientRecognitionHistoryView.as_view(), name='history'),

    # 食材搜索
    # GET /api/ingredient/search/?q=关键词
    path('search/', IngredientSearchView.as_view(), name='search'),

    # 应季食材
    # GET /api/ingredient/seasonal/?month=6
    path('seasonal/', IngredientSeasonalView.as_view(), name='seasonal'),

    # 营养计算
    # POST /api/ingredient/nutrition-calculate/
    path('nutrition-calculate/', IngredientNutritionCalculateView.as_view(), name='nutrition-calculate'),

    # 基于食材推荐食谱
    # POST /api/ingredient/recommend/
    path('recommend/', IngredientRecommendView.as_view(), name='recommend'),
]
