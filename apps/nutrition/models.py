"""
营养分析模块数据模型

模型：
    - DietaryLog: 用户饮食记录（日记）
"""

from django.db import models
from django.contrib.auth.models import User


class DietaryLog(models.Model):
    """
    用户饮食日记记录

    记录用户每天每餐的食物摄入，支持关联食谱或自定义食物名称。
    """

    MEAL_TYPES = [
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
        ('snack', '加餐'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dietary_logs',
        verbose_name='用户'
    )
    recipe = models.ForeignKey(
        'recipe.Recipe',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dietary_logs',
        verbose_name='关联食谱'
    )
    custom_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='自定义食物名称',
        help_text='未关联食谱时的自定义食物名称'
    )
    calories = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='卡路里（千卡）'
    )
    protein = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='蛋白质（g）'
    )
    fat = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='脂肪（g）'
    )
    carbohydrate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='碳水化合物（g）'
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPES,
        default='lunch',
        verbose_name='餐次'
    )
    date = models.DateField(verbose_name='日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'dietary_log'
        verbose_name = '饮食记录'
        verbose_name_plural = '饮食记录'
        ordering = ['date', 'meal_type', 'created_at']

    def __str__(self):
        name = self.recipe.name if self.recipe else self.custom_name
        return f"{self.user.username} - {self.date} {self.get_meal_type_display()} - {name}"

    @property
    def food_name(self):
        return self.recipe.name if self.recipe else self.custom_name
