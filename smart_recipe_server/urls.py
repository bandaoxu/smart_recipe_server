"""
URL configuration for smart_recipe_server project.

智能食谱后端 API 路由配置

API 路由：
    - /admin/                       Django 管理后台
    - /api/user/                    用户模块
    - /api/ingredient/              食材模块
    - /api/recipe/                  食谱模块
    - /api/shopping-list/           购物清单模块
    - /api/community/               社区模块
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Django Admin 后台管理
    path('admin/', admin.site.urls),

    # JWT Token 刷新
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 用户模块
    # 包含：注册、登录、用户档案管理、修改密码等
    path('api/user/', include('apps.user.urls')),

    # 食材模块
    # 包含：食材列表、详情、搜索、识别、应季食材、营养计算等
    path('api/ingredient/', include('apps.ingredient.urls')),

    # 食谱模块
    # 包含：食谱 CRUD、点赞、收藏、搜索、推荐等
    path('api/recipe/', include('apps.recipe.urls')),

    # 购物清单模块
    # 包含：购物清单管理、基于食谱生成清单等
    path('api/shopping-list/', include('apps.shopping.urls')),

    # 社区模块
    # 包含：美食动态、评论等
    path('api/community/', include('apps.community.urls')),
]
