"""
购物清单模块后台管理配置
"""

from django.contrib import admin
from common.admin_mixins import ExportCsvMixin
from .models import ShoppingList, ShoppingListShare


@admin.register(ShoppingList)
class ShoppingListAdmin(ExportCsvMixin, admin.ModelAdmin):
    """
    购物清单管理类

    支持批量标记已购/未购、CSV 导出。
    """

    # CSV 导出配置
    export_fields = [
        'id', 'user', 'ingredient', 'quantity', 'unit', 'is_purchased', 'created_at'
    ]
    export_filename = 'shopping_lists'

    list_display = [
        'id', 'user', 'ingredient', 'quantity', 'unit',
        'is_purchased', 'created_at'
    ]

    list_display_links = ['id', 'user']

    list_filter = ['is_purchased', 'created_at']

    search_fields = ['user__username', 'ingredient__name']

    # 批量操作
    actions = ['mark_as_purchased', 'mark_as_unpurchased', 'export_as_csv']

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('购物信息', {
            'fields': ['user', 'ingredient', 'quantity', 'unit']
        }),
        ('状态', {
            'fields': ['is_purchased']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ['-is_purchased', '-created_at']   # 已购买优先显示，方便查看

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'ingredient')

    def mark_as_purchased(self, request, queryset):
        """逐条 save 避免 unique_together 约束导致 bulk update 失败"""
        count = 0
        for item in queryset.filter(is_purchased=False):
            try:
                item.is_purchased = True
                item.save()
                count += 1
            except Exception:
                pass
        self.message_user(request, f'已标记 {count} 项为已购买')

    mark_as_purchased.short_description = '批量标记为已购买'

    def mark_as_unpurchased(self, request, queryset):
        """逐条 save 避免 unique_together 约束导致 bulk update 失败"""
        count = 0
        for item in queryset.filter(is_purchased=True):
            try:
                item.is_purchased = False
                item.save()
                count += 1
            except Exception:
                pass
        self.message_user(request, f'已标记 {count} 项为未购买')

    mark_as_unpurchased.short_description = '批量标记为未购买'


@admin.register(ShoppingListShare)
class ShoppingListShareAdmin(admin.ModelAdmin):
    """
    购物清单分享管理类

    管理分享链接，支持撤销分享操作。
    """

    list_display = [
        'id', 'owner', 'permission', 'expires_at', 'is_active', 'created_at'
    ]

    list_display_links = ['id', 'owner']

    list_filter = ['permission', 'is_active']

    search_fields = ['owner__username']

    # token 为系统生成，设为只读；created_at 自动填充
    readonly_fields = ['token', 'created_at']

    fieldsets = [
        ('分享者信息', {
            'fields': ['owner']
        }),
        ('分享设置', {
            'fields': ['token', 'permission', 'expires_at', 'is_active']
        }),
        ('时间信息', {
            'fields': ['created_at'],
            'classes': ['collapse']
        }),
    ]

    actions = ['revoke_shares']

    list_per_page = 20
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')

    def revoke_shares(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'已撤销 {count} 个分享链接')

    revoke_shares.short_description = '撤销分享链接'
