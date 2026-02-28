"""
营养分析模块序列化器
"""

from rest_framework import serializers
from .models import DietaryLog


class DietaryLogSerializer(serializers.ModelSerializer):
    """饮食记录序列化器"""

    food_name = serializers.ReadOnlyField()
    meal_type_display = serializers.CharField(source='get_meal_type_display', read_only=True)

    class Meta:
        model = DietaryLog
        fields = [
            'id', 'recipe', 'custom_name', 'food_name',
            'calories', 'protein', 'fat', 'carbohydrate',
            'meal_type', 'meal_type_display', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
