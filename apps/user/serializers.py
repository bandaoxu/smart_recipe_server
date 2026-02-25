"""
用户模块序列化器

本模块定义了用户相关的序列化器，用于数据的序列化和反序列化。
包括用户注册、登录、用户档案等功能的序列化器。

序列化器：
    - UserSerializer: 用户基本信息序列化器
    - UserProfileSerializer: 用户档案序列化器
    - UserRegisterSerializer: 用户注册序列化器
    - UserLoginSerializer: 用户登录序列化器
    - ChangePasswordSerializer: 修改密码序列化器
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """
    用户基本信息序列化器

    用于序列化 Django User 模型的基本信息。
    包含用户名、邮箱等字段，但不包含密码。

    字段：
        id: 用户 ID（只读）
        username: 用户名
        email: 邮箱
        date_joined: 注册时间（只读）
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户档案序列化器

    用于序列化 UserProfile 模型，包含用户的详细信息。
    嵌套 UserSerializer，可以同时显示用户基本信息和档案信息。

    字段：
        user: 用户基本信息（嵌套 UserSerializer）
        nickname: 昵称
        avatar: 头像 URL
        gender: 性别
        age: 年龄
        phone: 手机号
        dietary_preference: 饮食偏好
        allergies: 过敏食材
        health_goal: 健康目标
        daily_calories_target: 每日卡路里目标
        created_at: 创建时间（只读）
        updated_at: 更新时间（只读）

    使用示例：
        # 序列化单个用户档案
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

        # 反序列化并更新用户档案
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
    """

    # 嵌套用户基本信息（只读）
    user = UserSerializer(read_only=True)

    # 年龄段（通过方法字段计算得出）
    age_group = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'nickname', 'avatar', 'gender', 'age', 'phone',
            'dietary_preference', 'allergies', 'health_goal',
            'daily_calories_target', 'age_group', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'age_group']

    def get_age_group(self, obj):
        """
        获取年龄段

        参数：
            obj: UserProfile 实例

        返回：
            str: 年龄段标签
        """
        return obj.get_age_group()


class UserRegisterSerializer(serializers.Serializer):
    """
    用户注册序列化器

    用于处理用户注册请求，验证输入数据并创建新用户。

    字段：
        username: 用户名（3-30 个字符）
        password: 密码（至少 6 个字符）
        password_confirm: 确认密码（必须与 password 相同）
        email: 邮箱（可选）
        nickname: 昵称（可选）
        phone: 手机号（可选）

    验证规则：
        - username 必须唯一
        - password 和 password_confirm 必须相同
        - password 长度至少 6 个字符

    使用示例：
        # 在视图中使用
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': '注册成功'})
        return Response(serializer.errors, status=400)
    """

    username = serializers.CharField(
        max_length=30,
        min_length=3,
        required=True,
        help_text='用户名，3-30 个字符'
    )

    password = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True,
        required=True,
        help_text='密码，至少 6 个字符'
    )

    password_confirm = serializers.CharField(
        max_length=128,
        min_length=6,
        write_only=True,
        required=True,
        help_text='确认密码，必须与密码相同'
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text='邮箱地址（可选）'
    )

    nickname = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='用户昵称（可选）'
    )

    phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text='手机号码（可选）'
    )

    def validate_username(self, value):
        """
        验证用户名是否已存在

        参数：
            value: 用户名

        返回：
            str: 验证通过的用户名

        异常：
            ValidationError: 用户名已存在
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('该用户名已被注册')
        return value

    def validate(self, data):
        """
        验证两次密码是否一致

        参数：
            data: 所有字段的数据

        返回：
            dict: 验证通过的数据

        异常：
            ValidationError: 两次密码不一致
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': '两次密码输入不一致'})
        return data

    def create(self, validated_data):
        """
        创建新用户和用户档案

        参数：
            validated_data: 验证通过的数据

        返回：
            User: 创建的用户实例
        """
        # 移除 password_confirm，不需要保存
        validated_data.pop('password_confirm')

        # 提取用户档案相关字段
        nickname = validated_data.pop('nickname', '')
        phone = validated_data.pop('phone', '')

        # 创建用户（使用 create_user 方法会自动加密密码）
        user = User.objects.create_user(**validated_data)

        # 创建用户档案
        UserProfile.objects.create(
            user=user,
            nickname=nickname or user.username,  # 如果没有昵称，使用用户名
            phone=phone
        )

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器

    用于处理用户登录请求，验证用户名和密码。

    字段：
        username: 用户名
        password: 密码

    使用示例：
        # 在视图中使用
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # 生成 JWT Token
            return Response({'token': token, 'user': user_data})
        return Response(serializer.errors, status=400)
    """

    username = serializers.CharField(
        required=True,
        help_text='用户名'
    )

    password = serializers.CharField(
        required=True,
        write_only=True,
        help_text='密码'
    )

    def validate(self, data):
        """
        验证用户名和密码

        参数：
            data: 包含 username 和 password 的字典

        返回：
            dict: 包含验证通过的用户对象

        异常：
            ValidationError: 用户名或密码错误
        """
        username = data.get('username')
        password = data.get('password')

        # 使用 Django 的 authenticate 方法验证用户
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError('用户名或密码错误')

        if not user.is_active:
            raise serializers.ValidationError('该账号已被禁用')

        # 将用户对象添加到验证后的数据中
        data['user'] = user
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器

    用于处理用户修改密码的请求。

    字段：
        old_password: 旧密码
        new_password: 新密码
        new_password_confirm: 确认新密码

    验证规则：
        - old_password 必须正确
        - new_password 和 new_password_confirm 必须相同
        - new_password 长度至少 6 个字符

    使用示例：
        # 在视图中使用
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '密码修改成功'})
        return Response(serializer.errors, status=400)
    """

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text='旧密码'
    )

    new_password = serializers.CharField(
        max_length=128,
        min_length=6,
        required=True,
        write_only=True,
        help_text='新密码，至少 6 个字符'
    )

    new_password_confirm = serializers.CharField(
        max_length=128,
        min_length=6,
        required=True,
        write_only=True,
        help_text='确认新密码，必须与新密码相同'
    )

    def validate_old_password(self, value):
        """
        验证旧密码是否正确

        参数：
            value: 旧密码

        返回：
            str: 验证通过的旧密码

        异常：
            ValidationError: 旧密码错误
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('旧密码错误')
        return value

    def validate(self, data):
        """
        验证两次新密码是否一致

        参数：
            data: 所有字段的数据

        返回：
            dict: 验证通过的数据

        异常：
            ValidationError: 两次新密码不一致
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': '两次密码输入不一致'})
        return data

    def save(self):
        """
        保存新密码

        返回：
            User: 更新后的用户实例
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    用户档案更新序列化器

    用于更新用户档案信息，字段较少，适合部分更新。

    字段：
        nickname: 昵称
        avatar: 头像 URL
        gender: 性别
        age: 年龄
        dietary_preference: 饮食偏好
        allergies: 过敏食材
        health_goal: 健康目标
        daily_calories_target: 每日卡路里目标

    使用示例：
        # 在视图中使用
        profile = UserProfile.objects.get(user=request.user)
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    """

    class Meta:
        model = UserProfile
        fields = [
            'nickname', 'avatar', 'gender', 'age',
            'dietary_preference', 'allergies', 'health_goal',
            'daily_calories_target'
        ]

    def validate_age(self, value):
        """
        验证年龄范围

        参数：
            value: 年龄

        返回：
            int: 验证通过的年龄

        异常：
            ValidationError: 年龄不合法
        """
        if value is not None and (value < 1 or value > 150):
            raise serializers.ValidationError('年龄必须在 1-150 之间')
        return value

    def validate_daily_calories_target(self, value):
        """
        验证每日卡路里目标范围

        参数：
            value: 每日卡路里目标

        返回：
            int: 验证通过的卡路里目标

        异常：
            ValidationError: 卡路里目标不合法
        """
        if value is not None and (value < 500 or value > 5000):
            raise serializers.ValidationError('每日卡路里目标必须在 500-5000 之间')
        return value
