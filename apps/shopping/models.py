"""
购物清单模块数据模型

本模块定义了购物清单相关的数据模型。

模型：
    - ShoppingList: 购物清单表，存储用户的购物清单
"""

from django.db import models
from django.contrib.auth.models import User
from apps.ingredient.models import Ingredient


class ShoppingList(models.Model):
    """
    购物清单模型

    存储用户的购物清单，包括需要购买的食材和数量。
    用户可以手动添加食材，或基于食谱一键生成购物清单。

    字段说明：
        user: 用户（外键）
        ingredient: 食材（外键）
        quantity: 数量
        unit: 单位
        is_purchased: 是否已购买
        created_at: 创建时间
        updated_at: 更新时间

    使用示例：
        # 添加食材到购物清单
        shopping_item = ShoppingList.objects.create(
            user=request.user,
            ingredient=tomato,
            quantity=500,
            unit='克'
        )

        # 标记为已购买
        shopping_item.is_purchased = True
        shopping_item.save()

        # 获取用户的购物清单
        shopping_list = ShoppingList.objects.filter(user=request.user, is_purchased=False)
    """

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='用户',
        help_text='拥有该购物清单的用户'
    )

    # 关联食材
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='shopping_list',
        verbose_name='食材',
        help_text='需要购买的食材'
    )

    # 数量
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='数量',
        help_text='需要购买的数量'
    )

    # 单位
    unit = models.CharField(
        max_length=20,
        default='克',
        verbose_name='单位',
        help_text='食材的计量单位（克、个、勺等）'
    )

    # 是否已购买
    is_purchased = models.BooleanField(
        default=False,
        verbose_name='是否已购买',
        help_text='是否已经购买该食材'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='添加到购物清单的时间'
    )

    # 更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='最后更新的时间'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'shopping_list'
        verbose_name = '购物清单'
        verbose_name_plural = '购物清单'
        ordering = ['is_purchased', '-created_at']  # 未购买的优先，然后按创建时间倒序
        unique_together = ['user', 'ingredient', 'is_purchased']  # 同一用户对同一食材在未购买状态下只能有一条记录

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 用户、食材名称和数量
        """
        return f'{self.user.username} - {self.ingredient.name} {self.quantity}{self.unit}'

    def mark_as_purchased(self):
        """
        标记为已购买

        使用示例：
            item = ShoppingList.objects.get(id=1)
            item.mark_as_purchased()
        """
        self.is_purchased = True
        self.save(update_fields=['is_purchased'])

    def mark_as_unpurchased(self):
        """
        标记为未购买

        使用示例：
            item = ShoppingList.objects.get(id=1)
            item.mark_as_unpurchased()
        """
        self.is_purchased = False
        self.save(update_fields=['is_purchased'])
