"""
社区模块数据模型

本模块定义了社区相关的数据模型。

模型：
    - FoodPost: 美食动态表，用户发布的美食分享
    - Comment: 评论表，对食谱或动态的评论
"""

from django.db import models
from django.contrib.auth.models import User
from apps.recipe.models import Recipe


class FoodPost(models.Model):
    """
    美食动态模型

    用户在社区发布的美食动态，可以关联食谱，也可以纯文字+图片分享。

    字段说明：
        user: 用户（外键）
        recipe: 关联食谱（可选）
        content: 动态内容
        images: 图片 URL 列表（JSON）
        likes: 点赞数
        comments_count: 评论数
        created_at: 创建时间
    """

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_posts',
        verbose_name='用户'
    )

    # 关联食谱（可选）
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_posts',
        verbose_name='关联食谱'
    )

    # 动态内容
    content = models.TextField(
        verbose_name='动态内容'
    )

    # 图片列表（JSON 格式）
    images = models.JSONField(
        default=list,
        blank=True,
        verbose_name='图片列表'
    )

    # 点赞数
    likes = models.IntegerField(
        default=0,
        verbose_name='点赞数'
    )

    # 评论数
    comments_count = models.IntegerField(
        default=0,
        verbose_name='评论数'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        db_table = 'food_post'
        verbose_name = '美食动态'
        verbose_name_plural = '美食动态'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.content[:30]}'


class Comment(models.Model):
    """
    评论模型

    用户对食谱或美食动态的评论，支持回复（父评论）。

    字段说明：
        user: 用户（外键）
        target_id: 目标 ID（食谱 ID 或动态 ID）
        target_type: 目标类型（recipe/post）
        content: 评论内容
        parent: 父评论（可选，用于回复评论）
        created_at: 创建时间
    """

    # 目标类型选项
    TARGET_TYPE_CHOICES = [
        ('recipe', '食谱'),
        ('post', '动态'),
    ]

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='用户'
    )

    # 目标 ID
    target_id = models.IntegerField(
        verbose_name='目标ID'
    )

    # 目标类型
    target_type = models.CharField(
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        verbose_name='目标类型'
    )

    # 评论内容
    content = models.TextField(
        verbose_name='评论内容'
    )

    # 父评论（用于回复）
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )

    class Meta:
        db_table = 'comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.content[:30]}'
