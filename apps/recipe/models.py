"""
食谱模块数据模型

本模块定义了食谱相关的数据模型，是整个项目的核心功能模块。

模型：
    - Recipe: 食谱表，存储食谱的基本信息
    - RecipeIngredient: 食谱食材关联表，存储食谱所需的食材和用量
    - CookingStep: 烹饪步骤表，存储食谱的详细步骤
    - UserBehavior: 用户行为表，记录用户的浏览、点赞、收藏等行为
"""

from django.db import models
from django.contrib.auth.models import User
from apps.ingredient.models import Ingredient


class Recipe(models.Model):
    """
    食谱模型

    存储食谱的基本信息，包括名称、封面、难度、烹饪时间等。
    是整个食谱系统的核心表。

    字段说明：
        name: 食谱名称
        cover_image: 封面图
        author: 作者（外键：User）
        difficulty: 难度（简单、中等、困难）
        cooking_time: 烹饪时间（分钟）
        servings: 份数
        category: 分类（早餐、午餐、晚餐、甜品等）
        cuisine_type: 菜系（粤菜、川菜、西餐等）
        tags: 标签（JSON：快手菜、家常菜等）
        total_calories: 总卡路里
        description: 简介
        views: 浏览次数
        likes: 点赞数
        favorites: 收藏数
        is_published: 是否发布
        created_at: 创建时间
        updated_at: 更新时间

    关联关系：
        - author: 关联到 User 模型，表示食谱作者
        - ingredients: 通过 RecipeIngredient 关联到 Ingredient
        - steps: 反向关联到 CookingStep

    使用示例：
        # 创建食谱
        recipe = Recipe.objects.create(
            name='西红柿炒鸡蛋',
            author=request.user,
            difficulty='easy',
            cooking_time=15,
            servings=2,
            category='lunch',
            cuisine_type='chinese',
            tags=['快手菜', '家常菜'],
            description='简单美味的家常菜'
        )
    """

    # 难度选项
    DIFFICULTY_CHOICES = [
        ('easy', '简单'),
        ('medium', '中等'),
        ('hard', '困难'),
    ]

    # 分类选项
    CATEGORY_CHOICES = [
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
        ('dessert', '甜品'),
        ('snack', '小吃'),
        ('soup', '汤品'),
        ('staple', '主食'),
        ('other', '其他'),
    ]

    # 菜系选项
    CUISINE_TYPE_CHOICES = [
        ('chinese', '中餐'),
        ('cantonese', '粤菜'),
        ('sichuan', '川菜'),
        ('hunan', '湘菜'),
        ('shandong', '鲁菜'),
        ('jiangsu', '苏菜'),
        ('zhejiang', '浙菜'),
        ('fujian', '闽菜'),
        ('anhui', '徽菜'),
        ('western', '西餐'),
        ('japanese', '日料'),
        ('korean', '韩餐'),
        ('other', '其他'),
    ]

    # 食谱名称
    name = models.CharField(
        max_length=200,
        verbose_name='食谱名称',
        help_text='食谱的标题'
    )

    # 封面图 URL
    cover_image = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='封面图',
        help_text='食谱封面图片的 URL'
    )

    # 作者（外键关联到 User）
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='作者',
        help_text='创建该食谱的用户'
    )

    # 难度
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name='难度',
        help_text='食谱的烹饪难度'
    )

    # 烹饪时间（分钟）
    cooking_time = models.IntegerField(
        default=0,
        verbose_name='烹饪时间',
        help_text='制作该食谱所需的时间（分钟）'
    )

    # 份数
    servings = models.IntegerField(
        default=1,
        verbose_name='份数',
        help_text='该食谱可制作的份数'
    )

    # 分类
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other',
        verbose_name='分类',
        help_text='食谱所属的分类（早餐、午餐等）'
    )

    # 菜系
    cuisine_type = models.CharField(
        max_length=50,
        choices=CUISINE_TYPE_CHOICES,
        default='chinese',
        verbose_name='菜系',
        help_text='食谱所属的菜系'
    )

    # 标签（JSON 格式，存储多个标签）
    # 例如：["快手菜", "家常菜", "下饭菜"]
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name='标签',
        help_text='食谱的标签列表（如：快手菜、家常菜）'
    )

    # 总卡路里
    total_calories = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='总卡路里',
        help_text='整个食谱的总热量（千卡）'
    )

    # 食谱简介
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='简介',
        help_text='食谱的详细描述'
    )

    # 浏览次数
    views = models.IntegerField(
        default=0,
        verbose_name='浏览次数',
        help_text='食谱被浏览的次数'
    )

    # 点赞数
    likes = models.IntegerField(
        default=0,
        verbose_name='点赞数',
        help_text='食谱被点赞的次数'
    )

    # 收藏数
    favorites = models.IntegerField(
        default=0,
        verbose_name='收藏数',
        help_text='食谱被收藏的次数'
    )

    # 是否发布
    is_published = models.BooleanField(
        default=True,
        verbose_name='是否发布',
        help_text='是否公开显示该食谱'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='食谱创建的时间'
    )

    # 更新时间
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        help_text='食谱最后更新的时间'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'recipe'
        verbose_name = '食谱'
        verbose_name_plural = '食谱'
        ordering = ['-created_at']  # 按创建时间倒序排列
        indexes = [
            models.Index(fields=['author', 'is_published']),
            models.Index(fields=['category', 'is_published']),
            models.Index(fields=['-views']),
            models.Index(fields=['-likes']),
        ]

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 食谱名称
        """
        return self.name

    def increment_views(self):
        """
        增加浏览次数

        每次用户查看食谱详情时调用此方法。

        使用示例：
            recipe = Recipe.objects.get(id=1)
            recipe.increment_views()
        """
        self.views += 1
        self.save(update_fields=['views'])

    def increment_likes(self):
        """
        增加点赞数

        用户点赞时调用此方法。

        使用示例：
            recipe = Recipe.objects.get(id=1)
            recipe.increment_likes()
        """
        self.likes += 1
        self.save(update_fields=['likes'])

    def decrement_likes(self):
        """
        减少点赞数

        用户取消点赞时调用此方法。
        """
        if self.likes > 0:
            self.likes -= 1
            self.save(update_fields=['likes'])

    def increment_favorites(self):
        """
        增加收藏数

        用户收藏时调用此方法。
        """
        self.favorites += 1
        self.save(update_fields=['favorites'])

    def decrement_favorites(self):
        """
        减少收藏数

        用户取消收藏时调用此方法。
        """
        if self.favorites > 0:
            self.favorites -= 1
            self.save(update_fields=['favorites'])


class RecipeIngredient(models.Model):
    """
    食谱食材关联模型

    存储食谱所需的食材和用量。
    是 Recipe 和 Ingredient 的多对多关系中间表。

    字段说明：
        recipe: 食谱（外键）
        ingredient: 食材（外键）
        quantity: 数量
        unit: 单位（克、个、勺等）
        is_main: 是否主料

    使用示例：
        # 为食谱添加食材
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=tomato,
            quantity=200,
            unit='克',
            is_main=True
        )
    """

    # 关联食谱
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='食谱',
        help_text='关联的食谱'
    )

    # 关联食材
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='食材',
        help_text='关联的食材'
    )

    # 数量
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='数量',
        help_text='食材的用量'
    )

    # 单位
    unit = models.CharField(
        max_length=20,
        default='克',
        verbose_name='单位',
        help_text='食材的计量单位（克、个、勺等）'
    )

    # 是否主料
    is_main = models.BooleanField(
        default=False,
        verbose_name='是否主料',
        help_text='是否为该食谱的主要食材'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'recipe_ingredient'
        verbose_name = '食谱食材'
        verbose_name_plural = '食谱食材'
        ordering = ['-is_main', 'id']  # 主料优先，然后按 ID 排序
        unique_together = ['recipe', 'ingredient']  # 同一食谱中不能重复添加相同食材

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 食材名称和用量
        """
        return f'{self.ingredient.name} - {self.quantity}{self.unit}'


class CookingStep(models.Model):
    """
    烹饪步骤模型

    存储食谱的详细烹饪步骤。

    字段说明：
        recipe: 食谱（外键）
        step_number: 步骤序号
        description: 步骤描述
        image_url: 步骤图片
        duration: 该步骤耗时（分钟）
        tips: 小贴士

    使用示例：
        # 为食谱添加步骤
        CookingStep.objects.create(
            recipe=recipe,
            step_number=1,
            description='将西红柿切块',
            duration=2,
            tips='切成大小均匀的块状'
        )
    """

    # 关联食谱
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='食谱',
        help_text='关联的食谱'
    )

    # 步骤序号
    step_number = models.IntegerField(
        verbose_name='步骤序号',
        help_text='该步骤在食谱中的顺序（从 1 开始）'
    )

    # 步骤描述
    description = models.TextField(
        verbose_name='步骤描述',
        help_text='该步骤的详细说明'
    )

    # 步骤图片 URL
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='步骤图片',
        help_text='该步骤的图片 URL'
    )

    # 该步骤耗时（分钟）
    duration = models.IntegerField(
        default=0,
        verbose_name='耗时',
        help_text='完成该步骤所需的时间（分钟）'
    )

    # 小贴士
    tips = models.TextField(
        blank=True,
        null=True,
        verbose_name='小贴士',
        help_text='该步骤的注意事项或技巧'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'cooking_step'
        verbose_name = '烹饪步骤'
        verbose_name_plural = '烹饪步骤'
        ordering = ['step_number']  # 按步骤序号排序
        unique_together = ['recipe', 'step_number']  # 同一食谱中步骤序号不能重复

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 步骤序号和描述
        """
        return f'步骤 {self.step_number}: {self.description[:30]}'


class UserBehavior(models.Model):
    """
    用户行为模型

    记录用户的浏览、点赞、收藏、完成烹饪等行为。
    用于个性化推荐和数据统计。

    字段说明：
        user: 用户（外键）
        recipe: 食谱（外键）
        behavior_type: 行为类型（浏览、点赞、收藏、完成烹饪）
        created_at: 创建时间

    使用示例：
        # 记录用户浏览食谱
        UserBehavior.objects.create(
            user=request.user,
            recipe=recipe,
            behavior_type='view'
        )

        # 查询用户收藏的食谱
        favorites = UserBehavior.objects.filter(
            user=request.user,
            behavior_type='favorite'
        )
    """

    # 行为类型选项
    BEHAVIOR_TYPE_CHOICES = [
        ('view', '浏览'),
        ('like', '点赞'),
        ('favorite', '收藏'),
        ('cook', '完成烹饪'),
    ]

    # 关联用户
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='behaviors',
        verbose_name='用户',
        help_text='产生行为的用户'
    )

    # 关联食谱
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='behaviors',
        verbose_name='食谱',
        help_text='行为对象的食谱'
    )

    # 行为类型
    behavior_type = models.CharField(
        max_length=20,
        choices=BEHAVIOR_TYPE_CHOICES,
        verbose_name='行为类型',
        help_text='用户的行为类型'
    )

    # 创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        help_text='行为发生的时间'
    )

    class Meta:
        """
        模型元数据配置
        """
        db_table = 'user_behavior'
        verbose_name = '用户行为'
        verbose_name_plural = '用户行为'
        ordering = ['-created_at']  # 按创建时间倒序排列
        indexes = [
            models.Index(fields=['user', 'behavior_type']),
            models.Index(fields=['recipe', 'behavior_type']),
            models.Index(fields=['created_at']),
        ]
        # 对于点赞和收藏，同一用户对同一食谱只能有一条记录
        # 但浏览和完成烹饪可以有多条记录
        # 这里不设置 unique_together，在视图中控制

    def __str__(self):
        """
        模型的字符串表示

        返回：
            str: 用户、行为和食谱
        """
        return f'{self.user.username} - {self.get_behavior_type_display()} - {self.recipe.name}'
