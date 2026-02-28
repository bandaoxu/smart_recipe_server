"""
用户模块路由配置

本模块定义了用户相关的 URL 路由。

路由列表：
    - POST /register          用户注册
    - POST /login             用户登录
    - POST /logout            用户登出
    - GET /profile            获取用户档案
    - PUT /profile            完整更新用户档案
    - PATCH /profile          部分更新用户档案
    - POST /change-password   修改密码
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    ChangePasswordView,
    FollowView,
    FollowingListView,
    PublicUserProfileView,
    SendCodeView,
    HealthProfileView
)

# 应用命名空间
app_name = 'user'

urlpatterns = [
    # 用户注册
    # POST /api/user/register
    path('register/', UserRegisterView.as_view(), name='register'),

    # 用户登录
    # POST /api/user/login
    path('login/', UserLoginView.as_view(), name='login'),

    # 用户登出
    # POST /api/user/logout
    path('logout/', UserLogoutView.as_view(), name='logout'),

    # 用户档案（支持 GET, PUT, PATCH）
    # GET /api/user/profile - 获取用户档案
    # PUT /api/user/profile - 完整更新用户档案
    # PATCH /api/user/profile - 部分更新用户档案
    path('profile/', UserProfileView.as_view(), name='profile'),

    # 修改密码
    # POST /api/user/change-password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Token 刷新（别名，前端兼容）
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # 发送手机验证码
    # POST /api/user/send-code/
    path('send-code/', SendCodeView.as_view(), name='send-code'),

    # 健康档案
    # GET/POST /api/user/health-profile/
    path('health-profile/', HealthProfileView.as_view(), name='health-profile'),

    # 关注/取消关注用户
    # POST /api/user/<user_id>/follow/   - 关注
    # DELETE /api/user/<user_id>/follow/ - 取消关注
    path('<int:user_id>/follow/', FollowView.as_view(), name='follow'),

    # 获取当前用户关注列表
    # GET /api/user/following/
    path('following/', FollowingListView.as_view(), name='following'),

    # 获取他人公开档案（必须放在 follow 路由之后，避免路由冲突）
    # GET /api/user/<user_id>/
    path('<int:user_id>/', PublicUserProfileView.as_view(), name='public-profile'),
]
