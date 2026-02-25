"""
购物清单模块后台管理配置
"""

from django.contrib import admin
from .models import ShoppingList


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """
    购物清单管理类
    """

    list_display = [
        'id', 'user', 'ingredient', 'quantity', 'unit',
        'is_purchased', 'created_at'
    ]

    list_display_links = ['id', 'user']

    list_filter = [
        'is_purchased', 'created_at'
    ]

    search_fields = [
        'user__username', 'ingredient__name'
    ]

    readonly_fields = [
        'created_at', 'updated_at'
    ]

    fieldsets = [
        ('购物信息', {
            'fields': ['user', 'ingredient', 'quantity', 'unit']
        }),
        ('状态', {
            'fields': ['is_purchased']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at']
        })
    ]

    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ['is_purchased', '-created_at']
