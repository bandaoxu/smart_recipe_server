"""
用户模块视图

本模块定义了用户相关的 API 视图，包括注册、登录、用户信息管理等功能。

视图：
    - UserRegisterView: 用户注册
    - UserLoginView: 用户登录
    - UserProfileView: 获取和更新用户档案
    - ChangePasswordView: 修改密码
    - UserLogoutView: 用户登出
"""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from common.response import success_response, error_response
from .models import UserProfile
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer
)


class UserRegisterView(APIView):
    """
    用户注册视图

    允许新用户注册账号。
    注册成功后自动创建用户档案。

    请求方法：POST
    权限：所有人可访问（AllowAny）

    请求参数：
        username (str): 用户名，3-30 个字符，必填
        password (str): 密码，至少 6 个字符，必填
        password_confirm (str): 确认密码，必填
        email (str): 邮箱，可选
        nickname (str): 昵称，可选
        phone (str): 手机号，可选

    响应格式：
        成功：
        {
            "code": 200,
            "message": "注册成功",
            "data": {
                "user_id": 1,
                "username": "zhangsan",
                "nickname": "张三"
            }
        }

        失败：
        {
            "code": 400,
            "message": "注册失败",
            "data": {
                "username": ["该用户名已被注册"]
            }
        }

    使用示例：
        POST /api/user/register
        {
            "username": "zhangsan",
            "password": "123456",
            "password_confirm": "123456",
            "nickname": "张三",
            "phone": "13800138000"
        }
    """

    permission_classes = [AllowAny]  # 所有人都可以注册

    def post(self, request):
        """
        处理用户注册请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 注册结果
        """
        # 使用序列化器验证数据
        serializer = UserRegisterSerializer(data=request.data)

        if serializer.is_valid():
            # 创建用户
            user = serializer.save()

            # 返回用户基本信息
            return success_response(
                data={
                    'user_id': user.id,
                    'username': user.username,
                    'nickname': user.userprofile.nickname
                },
                message='注册成功'
            )
        else:
            # 返回验证错误信息
            return error_response(
                message='注册失败',
                data=serializer.errors,
                code=400
            )


class UserLoginView(APIView):
    """
    用户登录视图

    验证用户名和密码，登录成功后返回 JWT Token。

    请求方法：POST
    权限：所有人可访问（AllowAny）

    请求参数：
        username (str): 用户名，必填
        password (str): 密码，必填

    响应格式：
        成功：
        {
            "code": 200,
            "message": "登录成功",
            "data": {
                "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",  # 访问令牌
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",  # 刷新令牌
                "user": {
                    "id": 1,
                    "username": "zhangsan",
                    "email": "zhangsan@example.com"
                },
                "profile": {
                    "nickname": "张三",
                    "avatar": "http://...",
                    "age": 25,
                    ...
                }
            }
        }

        失败：
        {
            "code": 400,
            "message": "登录失败",
            "data": {
                "non_field_errors": ["用户名或密码错误"]
            }
        }

    JWT Token 说明：
        - access: 访问令牌，有效期较短（如 30 分钟），用于访问受保护的 API
        - refresh: 刷新令牌，有效期较长（如 7 天），用于获取新的访问令牌

    使用示例：
        POST /api/user/login
        {
            "username": "zhangsan",
            "password": "123456"
        }

        # 在后续请求中使用 Token
        GET /api/user/profile
        Headers: {
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    """

    permission_classes = [AllowAny]  # 所有人都可以登录

    def post(self, request):
        """
        处理用户登录请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 登录结果，包含 JWT Token 和用户信息
        """
        # 使用序列化器验证数据
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            # 获取验证通过的用户对象
            user = serializer.validated_data['user']

            # 生成 JWT Token
            refresh = RefreshToken.for_user(user)

            # 获取用户档案
            try:
                profile = user.userprofile
                profile_data = UserProfileSerializer(profile).data
            except UserProfile.DoesNotExist:
                # 如果用户档案不存在，创建一个默认档案
                profile = UserProfile.objects.create(
                    user=user,
                    nickname=user.username
                )
                profile_data = UserProfileSerializer(profile).data

            # 返回 Token 和用户信息
            return success_response(
                data={
                    'access': str(refresh.access_token),  # 访问令牌
                    'refresh': str(refresh),  # 刷新令牌
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    },
                    'profile': profile_data
                },
                message='登录成功'
            )
        else:
            # 返回验证错误信息
            return error_response(
                message='登录失败',
                data=serializer.errors,
                code=400
            )


class UserProfileView(APIView):
    """
    用户档案视图

    获取和更新当前登录用户的档案信息。

    请求方法：GET, PUT, PATCH
    权限：需要登录（IsAuthenticated）

    GET - 获取用户档案：
        响应格式：
        {
            "code": 200,
            "message": "获取用户档案成功",
            "data": {
                "id": 1,
                "user": {
                    "id": 1,
                    "username": "zhangsan",
                    "email": "zhangsan@example.com",
                    "date_joined": "2025-01-01T00:00:00Z"
                },
                "nickname": "张三",
                "avatar": "http://...",
                "gender": "male",
                "age": 25,
                "phone": "13800138000",
                "dietary_preference": ["素食", "低脂"],
                "allergies": ["花生", "海鲜"],
                "health_goal": "lose_weight",
                "daily_calories_target": 1800,
                "age_group": "青年",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-02T00:00:00Z"
            }
        }

    PUT/PATCH - 更新用户档案：
        请求参数（所有字段可选）：
            nickname (str): 昵称
            avatar (str): 头像 URL
            gender (str): 性别（male/female/other）
            age (int): 年龄
            dietary_preference (list): 饮食偏好列表
            allergies (list): 过敏食材列表
            health_goal (str): 健康目标
            daily_calories_target (int): 每日卡路里目标

        响应格式：同 GET 请求

    使用示例：
        # 获取用户档案
        GET /api/user/profile
        Headers: {"Authorization": "Bearer <access_token>"}

        # 更新用户档案
        PATCH /api/user/profile
        Headers: {"Authorization": "Bearer <access_token>"}
        {
            "nickname": "张三三",
            "age": 26,
            "dietary_preference": ["素食", "低糖"],
            "allergies": ["花生"],
            "health_goal": "lose_weight",
            "daily_calories_target": 1600
        }
    """

    permission_classes = [IsAuthenticated]  # 需要登录

    def get(self, request):
        """
        获取当前用户的档案信息

        参数：
            request: HTTP 请求对象

        返回：
            Response: 用户档案数据
        """
        try:
            # 获取当前用户的档案
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            # 如果档案不存在，创建一个默认档案
            profile = UserProfile.objects.create(
                user=request.user,
                nickname=request.user.username
            )

        # 序列化档案数据
        serializer = UserProfileSerializer(profile)

        return success_response(
            data=serializer.data,
            message='获取用户档案成功'
        )

    def put(self, request):
        """
        完整更新用户档案

        参数：
            request: HTTP 请求对象

        返回：
            Response: 更新后的用户档案数据
        """
        return self._update_profile(request, partial=False)

    def patch(self, request):
        """
        部分更新用户档案

        参数：
            request: HTTP 请求对象

        返回：
            Response: 更新后的用户档案数据
        """
        return self._update_profile(request, partial=True)

    def _update_profile(self, request, partial=False):
        """
        更新用户档案的内部方法

        参数：
            request: HTTP 请求对象
            partial: 是否为部分更新

        返回：
            Response: 更新后的用户档案数据
        """
        try:
            profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=request.user,
                nickname=request.user.username
            )

        # 使用序列化器验证和更新数据
        serializer = UserProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=partial
        )

        if serializer.is_valid():
            serializer.save()

            # 返回完整的用户档案数据
            full_serializer = UserProfileSerializer(profile)
            return success_response(
                data=full_serializer.data,
                message='更新用户档案成功'
            )
        else:
            return error_response(
                message='更新失败',
                data=serializer.errors,
                code=400
            )


class ChangePasswordView(APIView):
    """
    修改密码视图

    允许已登录用户修改密码。

    请求方法：POST
    权限：需要登录（IsAuthenticated）

    请求参数：
        old_password (str): 旧密码，必填
        new_password (str): 新密码，至少 6 个字符，必填
        new_password_confirm (str): 确认新密码，必填

    响应格式：
        成功：
        {
            "code": 200,
            "message": "密码修改成功",
            "data": null
        }

        失败：
        {
            "code": 400,
            "message": "密码修改失败",
            "data": {
                "old_password": ["旧密码错误"]
            }
        }

    使用示例：
        POST /api/user/change-password
        Headers: {"Authorization": "Bearer <access_token>"}
        {
            "old_password": "123456",
            "new_password": "654321",
            "new_password_confirm": "654321"
        }
    """

    permission_classes = [IsAuthenticated]  # 需要登录

    def post(self, request):
        """
        处理修改密码请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 修改结果
        """
        # 使用序列化器验证数据
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # 保存新密码
            serializer.save()

            return success_response(
                message='密码修改成功'
            )
        else:
            return error_response(
                message='密码修改失败',
                data=serializer.errors,
                code=400
            )


class UserLogoutView(APIView):
    """
    用户登出视图

    登出当前用户（将 Refresh Token 加入黑名单）。

    请求方法：POST
    权限：需要登录（IsAuthenticated）

    请求参数：
        refresh (str): 刷新令牌，必填

    响应格式：
        成功：
        {
            "code": 200,
            "message": "登出成功",
            "data": null
        }

        失败：
        {
            "code": 400,
            "message": "登出失败",
            "data": {
                "refresh": ["该字段不能为空"]
            }
        }

    使用示例：
        POST /api/user/logout
        Headers: {"Authorization": "Bearer <access_token>"}
        {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
        }
    """

    permission_classes = [IsAuthenticated]  # 需要登录

    def post(self, request):
        """
        处理用户登出请求

        参数：
            request: HTTP 请求对象

        返回：
            Response: 登出结果
        """
        try:
            # 获取 Refresh Token
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return error_response(
                    message='缺少 refresh token',
                    code=400
                )

            # 将 Refresh Token 加入黑名单（需要启用 simplejwt 的 token blacklist）
            token = RefreshToken(refresh_token)
            token.blacklist()

            return success_response(
                message='登出成功'
            )
        except Exception as e:
            return error_response(
                message='登出失败',
                data={'error': str(e)},
                code=400
            )
