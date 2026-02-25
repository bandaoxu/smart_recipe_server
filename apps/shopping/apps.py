"""
购物清单模块应用配置
"""

from django.apps import AppConfig


class ShoppingConfig(AppConfig):
    """
    购物清单模块配置类
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.shopping'
    verbose_name = '购物清单管理'
