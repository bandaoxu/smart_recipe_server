"""
用户模块数据模型

本模块定义了用户相关的数据模型，包括用户健康档案。
使用 Django 自带的 User 模型进行用户认证，UserProfile 存储额外的用户信息。

模型：
    - UserProfile: 用户健康档案，存储昵称、头像、饮食偏好、健康目标等信息
"""

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    用户健康档案模型

    扩展 Django 自带的 User 模型，存储用户的个人信息和健康数据。
    与 User 模型是一对一关系（OneToOne）。

    字段说明：
        user: 关联到 Django User 模型（OneToOne）
        nickname: 用户昵称
        avatar: 头像 URL
        gender: 性别（male/female/other）
        age: 年龄
        phone: 手机号
        dietary_preference: 饮食偏好（JSONField，如：素食、低糖、低脂等）
        allergies: 过敏食材列表（JSONField）
        health_goal: 健康目标（如：减肥、增肌、保持健康）
        daily_calories_target: 每日卡路里目标（千卡）
        created_at: 创建时间
        updated_at: 更新时间

    使用示例：
        # 创建用户档案
        user = User.objects.create_user(username='zhangsan', password='123456')
        profile = UserProfile.objects.create(
            user=user,
            nickname='张三',
            age=25,
            gender='male',
            dietary_preference=['低脂', '高蛋白'],
            allergies=['花生', '海鲜'],
            health_goal='减肥',
            daily_calories_target=1800
        )

        # 通过 User 访问 UserProfile
        user = User.objects.get(username='zhangsan')
        print(user.userprofile.nickname)  # 输出：张三
    """

    # 性别选项
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    ]

    # 健康目标选项
    HEALTH_GOAL_CHOICES = [
        ('lose_weight', '减肥'),
        ('gain_muscle', '增肌'),
        ('maintain', '保持健康'),
        ('improve_nutrition', '改善营养'),
    ]

    # 关联到 Django 自带的 User 模型（一对一关系）
    # on_delete=models.CASCADE：当用户被删除时，关联的档案也会被删除
    # related_name='userprofile'：允许通过 user.userprofile 访问档案
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile',
        verbose_name='用户',
        help_text='关联的 Django 用户'
    )

    # 用户昵称（可以与用户名不同）
    nickname = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='昵称',
        help_text='用户的显示名称'
    )

    # 头像 URL（存储图片的 URL 地址）
    avatar = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='头像',
        help_text='用户头像的 URL 地址'
    )

    # 性别
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name='性别',
        help_text='用户性别'
    )

    # 年龄
    age = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='年龄',
        help_text='用户年龄'
    )

    # 手机号
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='手机号',
        help_text='用户手机号码'
    )

    # 饮食偏好（JSON 格式，存储多个偏好标签）
    # 例如：["素食", "低糖", "低脂", "高蛋白"]
    dietary_preference = models.JSONField(
        default=list,
        blank=True,
        verbose_name='饮食偏好',
        help_text='用户的饮食偏好标签列表（如：素食、低糖、低脂等）'
    )

    # 过敏食材（JSON 格式，存储过敏食材列表）
    # 例如：["花生", "海鲜", "牛奶"]
    allergies = models.JSONField(
        default=list,
        blank=True,
        verbose_name='过敏食材',
        help_text='用户对哪些食材过敏'
    )

    # 健康目标
    health_goal = models.CharField(
        max_length=50,
        choices=HEALTH_GOAL_CHOICES,
        blank=True,
        null=True,
        verbose_name='健康目标',
        help_text='用户的健康目标（如：减肥、增肌、保持健康）'
    )

    # 每日卡路里目标（单位：千卡）
    daily_calories_target = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='每日卡路里目标',
        help_text='用户每日摄入卡路里的目标值（单位：千卡）'
    )

    # 创建时间（自动设置为创建时的时间）
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='用户档案创建的时间'
    )

    # 更新时间（每次保存时自动更新）
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='用户档案最后更新的时间'
    )

    class Meta:
        """
        模型元数据配置

        db_table: 指定数据库表名
        verbose_name: 模型的可读名称（单数）
        verbose_name_plural: 模型的可读名称（复数）
        ordering: 默认排序方式
        """
        db_table = 'user_profile'
        verbose_name = '用户档案'
        verbose_name_plural = '用户档案'
        ordering = ['-created_at']  # 按创建时间倒序排列

    def __str__(self):
        """
        模型的字符串表示

        在 Django Admin 和 Shell 中显示时使用。
        返回用户昵称或用户名。
        """
        return self.nickname or self.user.username

    def get_age_group(self):
        """
        获取用户年龄段

        根据用户年龄返回年龄段标签，用于推荐算法。

        返回：
            str: 年龄段标签（如：青少年、青年、中年、老年）

        使用示例：
            profile = UserProfile.objects.get(user=request.user)
            age_group = profile.get_age_group()
            print(age_group)  # 输出：青年
        """
        if not self.age:
            return '未知'
        elif self.age < 18:
            return '青少年'
        elif self.age < 35:
            return '青年'
        elif self.age < 60:
            return '中年'
        else:
            return '老年'

    def is_allergic_to(self, ingredient_name):
        """
        检查用户是否对某种食材过敏

        参数：
            ingredient_name (str): 食材名称

        返回：
            bool: True 表示过敏，False 表示不过敏

        使用示例：
            profile = UserProfile.objects.get(user=request.user)
            if profile.is_allergic_to('花生'):
                print('警告：您对花生过敏！')
        """
        return ingredient_name in self.allergies

    def get_dietary_preference_display(self):
        """
        获取饮食偏好的可读字符串

        将饮食偏好列表转换为逗号分隔的字符串。

        返回：
            str: 饮食偏好字符串（如：素食, 低糖, 低脂）

        使用示例：
            profile = UserProfile.objects.get(user=request.user)
            print(profile.get_dietary_preference_display())
            # 输出：素食, 低糖, 低脂
        """
        if not self.dietary_preference:
            return '无'
        return ', '.join(self.dietary_preference)
