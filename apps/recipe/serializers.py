"""
食谱模块序列化器

本模块定义了食谱相关的序列化器。由于食谱模块比较复杂，包含多个嵌套关系，
这里定义了多个序列化器用于不同的场景。

序列化器：
    - RecipeIngredientSerializer: 食谱食材序列化器
    - CookingStepSerializer: 烹饪步骤序列化器
    - RecipeListSerializer: 食谱列表序列化器（精简版）
    - RecipeDetailSerializer: 食谱详情序列化器（完整版）
    - RecipeCreateSerializer: 食谱创建序列化器
    - UserBehaviorSerializer: 用户行为序列化器
"""

from rest_framework import serializers
from .models import Recipe, RecipeIngredient, CookingStep, UserBehavior
from apps.ingredient.serializers import IngredientListSerializer


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    食谱食材序列化器

    用于序列化食谱中的食材信息。
    嵌套了食材的基本信息。
    """

    # 嵌套食材信息
    ingredient = IngredientListSerializer(read_only=True)

    # 食材 ID（用于创建/更新）
    ingredient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_id', 'quantity', 'unit', 'is_main']
        read_only_fields = ['id']


class CookingStepSerializer(serializers.ModelSerializer):
    """
    烹饪步骤序列化器

    用于序列化食谱的烹饪步骤。
    """

    class Meta:
        model = CookingStep
        fields = ['id', 'step_number', 'description', 'image_url', 'duration', 'tips']
        read_only_fields = ['id']


class RecipeListSerializer(serializers.ModelSerializer):
    """
    食谱列表序列化器（精简版）

    用于食谱列表页面，只包含关键字段。
    """

    # 作者信息
    author = serializers.SerializerMethodField()

    # 分类和菜系的中文显示名称
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    cuisine_type_display = serializers.CharField(source='get_cuisine_type_display', read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'cover_image', 'author', 'difficulty', 'difficulty_display',
            'cooking_time', 'servings', 'category', 'category_display',
            'cuisine_type', 'cuisine_type_display', 'tags', 'total_calories',
            'views', 'likes', 'favorites', 'created_at'
        ]
        read_only_fields = ['id', 'views', 'likes', 'favorites', 'created_at']

    def get_author(self, obj):
        """获取作者信息"""
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'nickname': getattr(obj.author.userprofile, 'nickname', obj.author.username)
        }


class RecipeDetailSerializer(serializers.ModelSerializer):
    """
    食谱详情序列化器（完整版）

    包含食谱的所有信息，包括食材列表和烹饪步骤。
    """

    # 作者信息
    author = serializers.SerializerMethodField()

    # 分类和菜系的中文显示名称
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    cuisine_type_display = serializers.CharField(source='get_cuisine_type_display', read_only=True)

    # 嵌套食材和步骤
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients', many=True, read_only=True)
    steps = CookingStepSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'name', 'cover_image', 'author', 'difficulty', 'difficulty_display',
            'cooking_time', 'servings', 'category', 'category_display',
            'cuisine_type', 'cuisine_type_display', 'tags', 'total_calories',
            'description', 'views', 'likes', 'favorites', 'is_published',
            'ingredients', 'steps', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'views', 'likes', 'favorites', 'created_at', 'updated_at']

    def get_author(self, obj):
        """获取作者信息"""
        return {
            'id': obj.author.id,
            'username': obj.author.username,
            'nickname': getattr(obj.author.userprofile, 'nickname', obj.author.username)
        }


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    食谱创建序列化器

    用于创建新食谱，包含食材和步骤的嵌套创建。
    """

    # 食材列表（嵌套创建）
    ingredients = RecipeIngredientSerializer(many=True, required=False)

    # 步骤列表（嵌套创建）
    steps = CookingStepSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'name', 'cover_image', 'difficulty', 'cooking_time', 'servings',
            'category', 'cuisine_type', 'tags', 'total_calories', 'description',
            'is_published', 'ingredients', 'steps'
        ]

    def create(self, validated_data):
        """
        创建食谱及其关联的食材和步骤
        """
        # 提取食材和步骤数据
        ingredients_data = validated_data.pop('ingredients', [])
        steps_data = validated_data.pop('steps', [])

        # 创建食谱（author 从 context 中获取）
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)

        # 创建食材关联
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.pop('ingredient_id')
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_id,
                **ingredient_data
            )

        # 创建烹饪步骤
        for step_data in steps_data:
            CookingStep.objects.create(recipe=recipe, **step_data)

        return recipe

    def update(self, instance, validated_data):
        """
        更新食谱及其关联的食材和步骤
        """
        # 提取食材和步骤数据
        ingredients_data = validated_data.pop('ingredients', None)
        steps_data = validated_data.pop('steps', None)

        # 更新食谱基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 更新食材（先删除旧的，再创建新的）
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                ingredient_id = ingredient_data.pop('ingredient_id')
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_id,
                    **ingredient_data
                )

        # 更新步骤（先删除旧的，再创建新的）
        if steps_data is not None:
            instance.steps.all().delete()
            for step_data in steps_data:
                CookingStep.objects.create(recipe=instance, **step_data)

        return instance


class UserBehaviorSerializer(serializers.ModelSerializer):
    """
    用户行为序列化器

    用于记录和查询用户行为。
    """

    # 用户信息
    user = serializers.SerializerMethodField(read_only=True)

    # 食谱信息（只读）
    recipe = RecipeListSerializer(read_only=True)

    # 食谱 ID（用于创建）
    recipe_id = serializers.IntegerField(write_only=True)

    # 行为类型的中文显示
    behavior_type_display = serializers.CharField(source='get_behavior_type_display', read_only=True)

    class Meta:
        model = UserBehavior
        fields = [
            'id', 'user', 'recipe', 'recipe_id', 'behavior_type',
            'behavior_type_display', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_user(self, obj):
        """获取用户信息"""
        return {
            'id': obj.user.id,
            'username': obj.user.username
        }
