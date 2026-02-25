"""
食材模块应用配置
"""

from django.apps import AppConfig


class IngredientConfig(AppConfig):
    """
    食材模块配置类

    配置食材模块的基本信息。
    """

    # 默认主键字段类型
    default_auto_field = 'django.db.models.BigAutoField'

    # 应用名称（必须与目录名一致）
    name = 'apps.ingredient'

    # 应用的可读名称（在 Django Admin 中显示）
    verbose_name = '食材管理'
