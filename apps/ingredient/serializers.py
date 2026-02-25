"""
食材模块序列化器

本模块定义了食材相关的序列化器，用于数据的序列化和反序列化。

序列化器：
    - IngredientSerializer: 食材详细信息序列化器
    - IngredientListSerializer: 食材列表序列化器（精简版）
    - IngredientRecognitionSerializer: 食材识别记录序列化器
    - IngredientRecognizeRequestSerializer: 食材识别请求序列化器
"""

from rest_framework import serializers
from .models import Ingredient, IngredientRecognition


class IngredientSerializer(serializers.ModelSerializer):
    """
    食材详细信息序列化器

    用于序列化食材的完整信息，包括营养成分、应季信息等。

    字段：
        id: 食材 ID（只读）
        name: 食材名称
        category: 分类
        category_display: 分类显示名称（中文）
        image_url: 图片 URL
        calories: 卡路里
        protein: 蛋白质
        fat: 脂肪
        carbohydrate: 碳水化合物
        fiber: 膳食纤维
        vitamin: 维生素
        description: 描述
        season: 应季月份
        is_seasonal_now: 当前是否应季（计算字段）
        created_at: 创建时间（只读）

    使用示例：
        # 序列化单个食材
        ingredient = Ingredient.objects.get(id=1)
        serializer = IngredientSerializer(ingredient)
        return Response(serializer.data)

        # 序列化食材列表
        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)
    """

    # 获取分类的中文显示名称
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    # 计算当前是否应季
    is_seasonal_now = serializers.SerializerMethodField()

    # 营养成分摘要（计算字段）
    nutrition_summary = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'category', 'category_display', 'image_url',
            'calories', 'protein', 'fat', 'carbohydrate', 'fiber',
            'vitamin', 'description', 'season', 'is_seasonal_now',
            'nutrition_summary', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_is_seasonal_now(self, obj):
        """
        获取当前是否应季

        参数：
            obj: Ingredient 实例

        返回：
            bool: True 表示应季，False 表示不应季
        """
        return obj.is_seasonal()

    def get_nutrition_summary(self, obj):
        """
        获取营养成分摘要

        参数：
            obj: Ingredient 实例

        返回：
            dict: 营养成分摘要
        """
        return obj.get_nutrition_summary()


class IngredientListSerializer(serializers.ModelSerializer):
    """
    食材列表序列化器（精简版）

    用于食材列表页面，只包含关键字段，减少数据传输量。

    字段：
        id: 食材 ID
        name: 食材名称
        category: 分类
        category_display: 分类显示名称
        image_url: 图片 URL
        calories: 卡路里
        is_seasonal_now: 当前是否应季

    使用示例：
        # 在列表视图中使用
        ingredients = Ingredient.objects.all()
        serializer = IngredientListSerializer(ingredients, many=True)
        return Response(serializer.data)
    """

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    is_seasonal_now = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = [
            'id', 'name', 'category', 'category_display',
            'image_url', 'calories', 'is_seasonal_now'
        ]
        read_only_fields = ['id']

    def get_is_seasonal_now(self, obj):
        """
        获取当前是否应季

        参数：
            obj: Ingredient 实例

        返回：
            bool: True 表示应季，False 表示不应季
        """
        return obj.is_seasonal()


class IngredientRecognitionSerializer(serializers.ModelSerializer):
    """
    食材识别记录序列化器

    用于序列化食材识别的历史记录。

    字段：
        id: 记录 ID（只读）
        user: 用户信息（只读）
        image_url: 图片 URL（只读）
        recognition_result: 识别结果
        recognized_ingredients: 识别到的食材列表（计算字段）
        top_ingredient: 置信度最高的食材（计算字段）
        created_at: 创建时间（只读）

    使用示例：
        # 序列化识别记录
        recognition = IngredientRecognition.objects.get(id=1)
        serializer = IngredientRecognitionSerializer(recognition)
        return Response(serializer.data)

        # 序列化用户的识别历史
        recognitions = IngredientRecognition.objects.filter(user=request.user)
        serializer = IngredientRecognitionSerializer(recognitions, many=True)
        return Response(serializer.data)
    """

    # 用户信息（嵌套）
    user = serializers.SerializerMethodField()

    # 识别到的食材列表
    recognized_ingredients = serializers.SerializerMethodField()

    # 置信度最高的食材
    top_ingredient = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecognition
        fields = [
            'id', 'user', 'image_url', 'recognition_result',
            'recognized_ingredients', 'top_ingredient', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_user(self, obj):
        """
        获取用户信息

        参数：
            obj: IngredientRecognition 实例

        返回：
            dict: 用户基本信息
        """
        return {
            'id': obj.user.id,
            'username': obj.user.username
        }

    def get_recognized_ingredients(self, obj):
        """
        获取识别到的食材列表

        参数：
            obj: IngredientRecognition 实例

        返回：
            list: 食材名称列表
        """
        return obj.get_recognized_ingredients()

    def get_top_ingredient(self, obj):
        """
        获取置信度最高的食材

        参数：
            obj: IngredientRecognition 实例

        返回：
            dict: 置信度最高的食材信息
        """
        return obj.get_highest_confidence_ingredient()


class IngredientRecognizeRequestSerializer(serializers.Serializer):
    """
    食材识别请求序列化器

    用于处理用户上传图片识别食材的请求。

    字段：
        image_url: 图片 URL（必填）

    验证规则：
        - image_url 必须是有效的 URL

    使用示例：
        # 在视图中使用
        serializer = IngredientRecognizeRequestSerializer(data=request.data)
        if serializer.is_valid():
            image_url = serializer.validated_data['image_url']
            # 调用 AI 模型识别食材
            result = recognize_ingredients(image_url)
            return Response({'result': result})
        return Response(serializer.errors, status=400)
    """

    image_url = serializers.URLField(
        required=True,
        help_text='要识别的食材图片 URL'
    )

    def validate_image_url(self, value):
        """
        验证图片 URL 格式

        参数：
            value: 图片 URL

        返回：
            str: 验证通过的 URL

        异常：
            ValidationError: URL 格式不正确
        """
        # 检查 URL 是否以图片格式结尾
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        if not any(value.lower().endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                '图片 URL 必须以有效的图片格式结尾（jpg, jpeg, png, gif, bmp, webp）'
            )
        return value


class IngredientNutritionCalculatorSerializer(serializers.Serializer):
    """
    食材营养计算器序列化器

    用于计算指定重量食材的营养成分。

    字段：
        ingredient_id: 食材 ID（必填）
        quantity_grams: 重量（克，必填）

    使用示例：
        # 在视图中使用
        serializer = IngredientNutritionCalculatorSerializer(data=request.data)
        if serializer.is_valid():
            ingredient_id = serializer.validated_data['ingredient_id']
            quantity = serializer.validated_data['quantity_grams']

            ingredient = Ingredient.objects.get(id=ingredient_id)
            nutrition = ingredient.calculate_nutrition(quantity)

            return Response({'nutrition': nutrition})
        return Response(serializer.errors, status=400)
    """

    ingredient_id = serializers.IntegerField(
        required=True,
        help_text='食材 ID'
    )

    quantity_grams = serializers.FloatField(
        required=True,
        min_value=0.1,
        max_value=10000,
        help_text='食材重量（克），范围：0.1 - 10000'
    )

    def validate_ingredient_id(self, value):
        """
        验证食材是否存在

        参数：
            value: 食材 ID

        返回：
            int: 验证通过的食材 ID

        异常：
            ValidationError: 食材不存在
        """
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError('食材不存在')
        return value


class IngredientCreateSerializer(serializers.ModelSerializer):
    """
    食材创建序列化器

    用于创建新的食材（管理员使用）。

    字段：
        name: 食材名称（必填）
        category: 分类（必填）
        image_url: 图片 URL（可选）
        calories: 卡路里（必填）
        protein: 蛋白质（必填）
        fat: 脂肪（必填）
        carbohydrate: 碳水化合物（必填）
        fiber: 膳食纤维（可选）
        vitamin: 维生素（可选）
        description: 描述（可选）
        season: 应季月份（可选）

    验证规则：
        - name 必须唯一
        - 营养成分必须大于等于 0

    使用示例：
        # 在视图中使用
        serializer = IngredientCreateSerializer(data=request.data)
        if serializer.is_valid():
            ingredient = serializer.save()
            return Response(IngredientSerializer(ingredient).data)
        return Response(serializer.errors, status=400)
    """

    class Meta:
        model = Ingredient
        fields = [
            'name', 'category', 'image_url',
            'calories', 'protein', 'fat', 'carbohydrate', 'fiber',
            'vitamin', 'description', 'season'
        ]

    def validate_name(self, value):
        """
        验证食材名称是否唯一

        参数：
            value: 食材名称

        返回：
            str: 验证通过的名称

        异常：
            ValidationError: 食材名称已存在
        """
        if Ingredient.objects.filter(name=value).exists():
            raise serializers.ValidationError('该食材名称已存在')
        return value

    def validate_season(self, value):
        """
        验证应季月份格式

        参数：
            value: 应季月份列表

        返回：
            list: 验证通过的月份列表

        异常：
            ValidationError: 月份格式不正确
        """
        if not isinstance(value, list):
            raise serializers.ValidationError('应季月份必须是列表格式')

        for month in value:
            if not isinstance(month, int) or month < 1 or month > 12:
                raise serializers.ValidationError('月份必须是 1-12 之间的整数')

        return value
