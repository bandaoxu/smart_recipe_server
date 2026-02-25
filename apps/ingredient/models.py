"""
食材模块数据模型

本模块定义了食材相关的数据模型，包括食材基本信息和食材识别记录。

模型：
    - Ingredient: 食材表，存储食材的基本信息和营养成分
    - IngredientRecognition: 食材识别记录表，存储用户上传图片识别食材的历史记录
"""

from django.db import models
from django.contrib.auth.models import User


class Ingredient(models.Model):
    """
    食材模型

    存储食材的基本信息和营养成分数据。
    这是食谱和购物清单的基础数据。

    字段说明：
        name: 食材名称
        category: 分类（蔬菜、肉类、水果等）
        image_url: 食材图片 URL
        calories: 卡路里（每 100g）
        protein: 蛋白质（g/100g）
        fat: 脂肪（g/100g）
        carbohydrate: 碳水化合物（g/100g）
        fiber: 膳食纤维（g/100g）
        vitamin: 维生素含量（JSONField）
        description: 食材描述
        season: 应季月份（JSONField）
        created_at: 创建时间

    使用示例：
        # 创建食材
        ingredient = Ingredient.objects.create(
            name='西红柿',
            category='蔬菜',
            calories=18,
            protein=0.9,
            fat=0.2,
            carbohydrate=3.9,
            fiber=1.2,
            vitamin={'C': 19, 'A': 900},
            description='富含番茄红素和维生素C',
            season=[5, 6, 7, 8, 9]  # 5-9月应季
        )

        # 查询应季食材
        import datetime
        current_month = datetime.datetime.now().month
        seasonal_ingredients = Ingredient.objects.filter(
            season__contains=current_month
        )
    """

    # 食材分类选项
    CATEGORY_CHOICES = [
        ('vegetable', '蔬菜'),
        ('meat', '肉类'),
        ('seafood', '海鲜'),
        ('fruit', '水果'),
        ('grain', '谷物'),
        ('dairy', '奶制品'),
        ('egg', '蛋类'),
        ('seasoning', '调味料'),
        ('oil', '油类'),
        ('bean', '豆制品'),
        ('nuts', '坚果'),
        ('other', '其他'),
    ]

    # 食材名称（唯一）
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='食材名称',
        help_text='食材的名称（如：西红柿、鸡胸肉）'
    )

    # 食材分类
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='食材分类',
        help_text='食材所属的分类'
    )

    # 食材图片 URL
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='食材图片',
        help_text='食材图片的 URL 地址'
    )

    # 卡路里（每 100g）
    calories = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='卡路里',
        help_text='每 100g 食材的热量（千卡）'
    )

    # 蛋白质（g/100g）
    protein = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='蛋白质',
        help_text='每 100g 食材的蛋白质含量（克）'
    )

    # 脂肪（g/100g）
    fat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='脂肪',
        help_text='每 100g 食材的脂肪含量（克）'
    )

    # 碳水化合物（g/100g）
    carbohydrate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='碳水化合物',
        help_text='每 100g 食材的碳水化合物含量（克）'
    )

    # 膳食纤维（g/100g）
    fiber = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='膳食纤维',
        help_text='每 100g 食材的膳食纤维含量（克）'
    )

    # 维生素含量（JSON 格式）
    # 例如：{"C": 19, "A": 900, "E": 0.6}
    vitamin = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='维生素',
        help_text='各种维生素的含量（JSON 格式，如：{"C": 19, "A": 900}）'
    )

    # 食材描述
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='描述',
        help_text='食材的详细描述（功效、特点等）'
    )

    # 应季月份（JSON 格式，存储月份数组）
    # 例如：[5, 6, 7, 8, 9] 表示 5-9 月应季
    season = models.JSONField(
        default=list,
        blank=True,
        verbose_name='应季月份',
        help_text='食材应季的月份列表（如：[5, 6, 7, 8]）'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='食材数据创建的时间'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'ingredient'
        verbose_name = '食材'
        verbose_name_plural = '食材'
        ordering = ['category', 'name']  # 按分类和名称排序

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 食材名称
        """
        return self.name

    def is_seasonal(self, month=None):
        """
        判断食材是否应季

        参数：
            month (int, optional): 月份（1-12），如果不传则使用当前月份

        返回：
            bool: True 表示应季，False 表示不应季

        使用示例：
            ingredient = Ingredient.objects.get(name='西红柿')
            if ingredient.is_seasonal():
                print('当前是应季食材')
            if ingredient.is_seasonal(month=6):
                print('6月是应季食材')
        """
        if not self.season:
            return False

        if month is None:
            import datetime
            month = datetime.datetime.now().month

        return month in self.season

    def get_nutrition_summary(self):
        """
        获取营养成分摘要

        返回：
            dict: 包含主要营养成分的字典

        使用示例：
            ingredient = Ingredient.objects.get(name='西红柿')
            nutrition = ingredient.get_nutrition_summary()
            print(nutrition)
            # 输出：{'calories': 18, 'protein': 0.9, 'fat': 0.2, ...}
        """
        return {
            'calories': float(self.calories),
            'protein': float(self.protein),
            'fat': float(self.fat),
            'carbohydrate': float(self.carbohydrate),
            'fiber': float(self.fiber),
            'vitamin': self.vitamin
        }

    def calculate_nutrition(self, quantity_grams):
        """
        计算指定重量的营养成分

        参数：
            quantity_grams (float): 食材重量（克）

        返回：
            dict: 指定重量的营养成分

        使用示例：
            ingredient = Ingredient.objects.get(name='西红柿')
            nutrition = ingredient.calculate_nutrition(200)  # 200克
            print(nutrition['calories'])  # 输出：36（200克的热量）
        """
        factor = quantity_grams / 100  # 营养数据是基于 100g 的

        return {
            'calories': float(self.calories) * factor,
            'protein': float(self.protein) * factor,
            'fat': float(self.fat) * factor,
            'carbohydrate': float(self.carbohydrate) * factor,
            'fiber': float(self.fiber) * factor
        }


class IngredientRecognition(models.Model):
    """
    食材识别记录模型

    存储用户上传图片识别食材的历史记录。
    用于追踪识别功能的使用情况和识别结果。

    字段说明：
        user: 用户（外键）
        image_url: 上传的图片 URL
        recognition_result: 识别结果（JSONField）
        created_at: 创建时间

    使用示例：
        # 创建识别记录
        recognition = IngredientRecognition.objects.create(
            user=request.user,
            image_url='http://example.com/upload/img.jpg',
            recognition_result={
                'ingredients': [
                    {'name': '西红柿', 'confidence': 0.95},
                    {'name': '鸡蛋', 'confidence': 0.88}
                ],
                'total_items': 2
            }
        )

        # 查询用户识别历史
        history = IngredientRecognition.objects.filter(user=request.user)
    """

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ingredient_recognitions',
        verbose_name='用户',
        help_text='上传图片的用户'
    )

    # 上传的图片 URL
    image_url = models.URLField(
        max_length=500,
        verbose_name='图片URL',
        help_text='用户上传的食材图片 URL'
    )

    # 识别结果（JSON 格式）
    # 例如：
    # {
    #     "ingredients": [
    #         {"name": "西红柿", "confidence": 0.95, "ingredient_id": 1},
    #         {"name": "鸡蛋", "confidence": 0.88, "ingredient_id": 2}
    #     ],
    #     "total_items": 2,
    #     "processing_time": 1.2  # 识别耗时（秒）
    # }
    recognition_result = models.JSONField(
        default=dict,
        verbose_name='识别结果',
        help_text='AI 识别的结果（JSON 格式）'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='识别记录创建的时间'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'ingredient_recognition'
        verbose_name = '食材识别记录'
        verbose_name_plural = '食材识别记录'
        ordering = ['-created_at']  # 按创建时间倒序排列

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 用户名和识别时间
        """
        return f'{self.user.username} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'

    def get_recognized_ingredients(self):
        """
        获取识别到的食材列表

        返回：
            list: 食材名称列表

        使用示例：
            recognition = IngredientRecognition.objects.get(id=1)
            ingredients = recognition.get_recognized_ingredients()
            print(ingredients)  # 输出：['西红柿', '鸡蛋']
        """
        if not self.recognition_result or 'ingredients' not in self.recognition_result:
            return []

        return [item['name'] for item in self.recognition_result.get('ingredients', [])]

    def get_highest_confidence_ingredient(self):
        """
        获取置信度最高的食材

        返回：
            dict: 置信度最高的食材信息，如果没有则返回 None

        使用示例：
            recognition = IngredientRecognition.objects.get(id=1)
            top_ingredient = recognition.get_highest_confidence_ingredient()
            if top_ingredient:
                print(f"最可能是：{top_ingredient['name']}，置信度：{top_ingredient['confidence']}")
        """
        if not self.recognition_result or 'ingredients' not in self.recognition_result:
            return None

        ingredients = self.recognition_result.get('ingredients', [])
        if not ingredients:
            return None

        # 按置信度排序，返回第一个
        return max(ingredients, key=lambda x: x.get('confidence', 0))
