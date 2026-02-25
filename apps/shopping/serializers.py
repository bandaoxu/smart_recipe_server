"""
购物清单模块序列化器
"""

from rest_framework import serializers
from .models import ShoppingList
from apps.ingredient.serializers import IngredientListSerializer


class ShoppingListSerializer(serializers.ModelSerializer):
    """
    购物清单序列化器

    用于序列化购物清单项。
    """

    # 嵌套食材信息
    ingredient = IngredientListSerializer(read_only=True)

    # 食材 ID（用于创建）
    ingredient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ShoppingList
        fields = [
            'id', 'ingredient', 'ingredient_id', 'quantity', 'unit',
            'is_purchased', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """创建购物清单项"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
