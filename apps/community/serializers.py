"""
社区模块序列化器
"""

from rest_framework import serializers
from .models import FoodPost, Comment, PostLike
from apps.recipe.serializers import RecipeListSerializer


class FoodPostSerializer(serializers.ModelSerializer):
    """美食动态序列化器"""

    user = serializers.SerializerMethodField()
    recipe = RecipeListSerializer(read_only=True)
    recipe_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = FoodPost
        fields = [
            'id', 'user', 'recipe', 'recipe_id', 'content', 'images',
            'likes', 'comments_count', 'is_liked', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'likes', 'comments_count', 'created_at']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'nickname': getattr(obj.user.userprofile, 'nickname', obj.user.username)
        }

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return PostLike.objects.filter(user=request.user, post=obj).exists()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""

    user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'target_id', 'target_type', 'content',
            'parent', 'replies', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username
        }

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
