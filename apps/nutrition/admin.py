"""
营养分析模块 Admin 配置
"""

from django.contrib import admin
from .models import DietaryLog


@admin.register(DietaryLog)
class DietaryLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_food_name', 'calories', 'meal_type', 'date', 'created_at']
    list_filter = ['meal_type', 'date']
    search_fields = ['user__username', 'custom_name', 'recipe__name']
    date_hierarchy = 'date'
    list_per_page = 30
    readonly_fields = ['created_at']

    def get_food_name(self, obj):
        return obj.recipe.name if obj.recipe else obj.custom_name
    get_food_name.short_description = '食物名称'
