"""
购物清单模块序列化器
"""

from rest_framework import serializers
from .models import ShoppingList
from apps.ingredient.serializers import IngredientListSerializer
from apps.ingredient.models import Ingredient


class ShoppingListSerializer(serializers.ModelSerializer):
    """
    购物清单序列化器

    用于序列化购物清单项。
    支持通过 ingredient_id 或 ingredient_name 添加食材。
    """

    # 嵌套食材信息
    ingredient = IngredientListSerializer(read_only=True)

    # 食材 ID（用于创建，可选）
    ingredient_id = serializers.IntegerField(write_only=True, required=False)

    # 食材名称（用于按名称创建，可选）
    ingredient_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ShoppingList
        fields = [
            'id', 'ingredient', 'ingredient_id', 'ingredient_name',
            'quantity', 'unit', 'is_purchased', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        # 仅在创建时（无 instance）才校验食材字段
        if not self.instance:
            if not attrs.get('ingredient_id') and not attrs.get('ingredient_name'):
                raise serializers.ValidationError('ingredient_id 或 ingredient_name 必须提供一个')
        return attrs

    def create(self, validated_data):
        """创建购物清单项，支持按名称自动 get_or_create 食材，重复添加则累加数量"""
        ingredient_name = validated_data.pop('ingredient_name', None)
        if ingredient_name and not validated_data.get('ingredient_id'):
            ingredient, _ = Ingredient.objects.get_or_create(name=ingredient_name)
            validated_data['ingredient_id'] = ingredient.id
        validated_data['user'] = self.context['request'].user

        # 已存在未购买的同一食材则累加数量
        existing = ShoppingList.objects.filter(
            user=validated_data['user'],
            ingredient_id=validated_data['ingredient_id'],
            is_purchased=False
        ).first()
        if existing:
            existing.quantity = float(existing.quantity) + float(validated_data.get('quantity', 0))
            existing.save()
            return existing
        return super().create(validated_data)
