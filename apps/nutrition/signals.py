"""
营养模块信号处理

当食材或食谱的营养信息更新时，自动更新相关的饮食记录。
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import F

from apps.recipe.models import Recipe, RecipeIngredient
from apps.ingredient.models import Ingredient
from apps.nutrition.models import DietaryLog


def _calc_recipe_nutrition(recipe_id: int) -> dict:
    """
    计算食谱的营养成分

    参数：
        recipe_id: 食谱 ID

    返回：
        dict: 包含营养成分的字典
    """
    ris = RecipeIngredient.objects.filter(recipe_id=recipe_id).select_related(
        "ingredient"
    )
    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "fat": 0.0,
        "carbohydrate": 0.0,
        "fiber": 0.0,
    }
    for ri in ris:
        ing = ri.ingredient
        factor = float(ri.quantity) / 100
        for k in totals:
            totals[k] += float(getattr(ing, k) or 0) * factor
    return {k: round(v, 1) for k, v in totals.items()}


def _update_dietary_logs_for_recipe(recipe_id: int):
    """
    更新关联到指定食谱的所有饮食记录

    参数：
        recipe_id: 食谱 ID
    """
    try:
        recipe = Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return

    # 计算新的营养值
    new_nutrition = _calc_recipe_nutrition(recipe_id)

    # 更新所有关联的饮食记录
    DietaryLog.objects.filter(recipe=recipe).update(
        calories=new_nutrition["calories"],
        protein=new_nutrition["protein"],
        fat=new_nutrition["fat"],
        carbohydrate=new_nutrition["carbohydrate"],
        fiber=new_nutrition["fiber"],
    )


def _update_dietary_logs_for_ingredient(ingredient_id: int):
    """
    更新所有包含指定食材的食谱的饮食记录

    参数：
        ingredient_id: 食材 ID
    """
    # 找到所有包含该食材的食谱
    recipe_ids = (
        RecipeIngredient.objects.filter(ingredient_id=ingredient_id)
        .values_list("recipe_id", flat=True)
        .distinct()
    )

    # 更新每个食谱的饮食记录
    for recipe_id in recipe_ids:
        _update_dietary_logs_for_recipe(recipe_id)


@receiver(post_save, sender=Ingredient)
def ingredient_saved(sender, instance, created, **kwargs):
    """
    当食材保存时，更新所有包含该食材的食谱的饮食记录

    参数：
        sender: 模型类
        instance: 食材实例
        created: 是否为新创建
        kwargs: 其他参数
    """
    # 只在营养信息发生变化时更新（不是新创建的）
    if not created:
        _update_dietary_logs_for_ingredient(instance.id)


@receiver(post_save, sender=RecipeIngredient)
def recipe_ingredient_saved(sender, instance, created, **kwargs):
    """
    当食谱食材关联保存时，更新该食谱的饮食记录

    参数：
        sender: 模型类
        instance: RecipeIngredient 实例
        created: 是否为新创建
        kwargs: 其他参数
    """
    _update_dietary_logs_for_recipe(instance.recipe_id)


@receiver(post_delete, sender=RecipeIngredient)
def recipe_ingredient_deleted(sender, instance, **kwargs):
    """
    当食谱食材关联删除时，更新该食谱的饮食记录

    参数：
        sender: 模型类
        instance: RecipeIngredient 实例
        kwargs: 其他参数
    """
    _update_dietary_logs_for_recipe(instance.recipe_id)
