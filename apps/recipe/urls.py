"""
食谱模块路由配置

本模块定义了食谱相关的 URL 路由。

路由列表：
    - GET /                      食谱列表
    - POST /                     创建食谱
    - GET /<id>/                 食谱详情
    - PUT /<id>/                 完整更新食谱
    - PATCH /<id>/               部分更新食谱
    - DELETE /<id>/              删除食谱
    - POST /<id>/like/           点赞/取消点赞
    - POST /<id>/favorite/       收藏/取消收藏
    - GET /favorites/            用户收藏列表
    - GET /search/               搜索食谱
    - GET /recommend/            推荐食谱
"""

from django.urls import path
from .views import (
    RecipeListView,
    RecipeDetailView,
    RecipeCreateView,
    RecipeUpdateView,
    RecipeDeleteView,
    RecipeLikeView,
    RecipeFavoriteView,
    UserFavoriteListView,
    RecipeSearchView,
    RecipeRecommendView,
    MyRecipesView
)

# 应用命名空间
app_name = 'recipe'

urlpatterns = [
    # 食谱列表和创建
    # GET /api/recipe/ - 食谱列表
    # POST /api/recipe/ - 创建食谱
    path('', RecipeListView.as_view(), name='list'),
    path('create/', RecipeCreateView.as_view(), name='create'),

    # 食谱详情、更新、删除
    # GET /api/recipe/<recipe_id>/ - 食谱详情
    path('<int:recipe_id>/', RecipeDetailView.as_view(), name='detail'),

    # PUT /api/recipe/<recipe_id>/update/ - 完整更新
    # PATCH /api/recipe/<recipe_id>/update/ - 部分更新
    path('<int:recipe_id>/update/', RecipeUpdateView.as_view(), name='update'),

    # DELETE /api/recipe/<recipe_id>/delete/ - 删除食谱
    path('<int:recipe_id>/delete/', RecipeDeleteView.as_view(), name='delete'),

    # 点赞和收藏
    # POST /api/recipe/<recipe_id>/like/ - 点赞/取消点赞
    path('<int:recipe_id>/like/', RecipeLikeView.as_view(), name='like'),

    # POST /api/recipe/<recipe_id>/favorite/ - 收藏/取消收藏
    path('<int:recipe_id>/favorite/', RecipeFavoriteView.as_view(), name='favorite'),

    # 用户收藏列表
    # GET /api/recipe/favorites/
    path('favorites/', UserFavoriteListView.as_view(), name='favorites'),

    # 搜索和推荐
    # GET /api/recipe/search/?q=关键词
    path('search/', RecipeSearchView.as_view(), name='search'),

    # GET /api/recipe/recommend/
    path('recommend/', RecipeRecommendView.as_view(), name='recommend'),

    # 我的食谱
    # GET /api/recipe/my-recipes/
    path('my-recipes/', MyRecipesView.as_view(), name='my-recipes'),
]
