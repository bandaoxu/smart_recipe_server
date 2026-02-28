"""
营养分析模块 apps 配置
"""

from django.apps import AppConfig


class NutritionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.nutrition'
    verbose_name = '营养分析'
