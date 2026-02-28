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
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import os
import uuid

@api_view(['GET'])
def api_root(request):
    return Response({
        "code": 200,
        "message": "智能食谱 API 服务运行中",
        "data": {
            "user": "/api/user/",
            "ingredient": "/api/ingredient/",
            "recipe": "/api/recipe/",
            "shopping_list": "/api/shopping-list/",
            "community": "/api/community/",
            "token_refresh": "/api/token/refresh/",
        }
    })

@api_view(['POST'])
@parser_classes([MultiPartParser])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """文件上传视图"""
    file = request.FILES.get('file')
    if not file:
        return Response({"code": 400, "message": "未提供文件", "data": None}, status=400)

    ext = os.path.splitext(file.name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)

    url = request.build_absolute_uri(f"{settings.MEDIA_URL}uploads/{filename}")
    return Response({"code": 200, "message": "上传成功", "data": {"url": url}})

urlpatterns = [
    # API 根路径
    path('api/', api_root, name='api-root'),

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

    # 营养分析模块
    # 包含：饮食日记、营养报表、健康建议
    path('api/nutrition/', include('apps.nutrition.urls')),

    # 文件上传
    path('api/upload/', upload_file, name='upload'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
