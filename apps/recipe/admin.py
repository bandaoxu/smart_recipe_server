"""
食谱模块后台管理配置

本模块配置了食谱相关模型在 Django Admin 后台的显示和管理方式。
"""

from django.contrib import admin
from django.db.models import Count
from common.admin_mixins import ExportCsvMixin
from .models import Recipe, RecipeIngredient, CookingStep, UserBehavior


class RecipeIngredientInline(admin.TabularInline):
    """
    食谱食材内联编辑

    在食谱详情页中可以直接编辑食材列表。
    启用 autocomplete_fields 需要 IngredientAdmin 配置了 search_fields（已配置）。
    """
    model = RecipeIngredient
    extra = 1
    fields = ['ingredient', 'quantity', 'unit', 'is_main']
    autocomplete_fields = ['ingredient']


class CookingStepInline(admin.StackedInline):
    """
    烹饪步骤内联编辑

    使用 StackedInline（堆叠布局）代替 TabularInline，
    方便编辑 description、tips 等长文本字段。
    """
    model = CookingStep
    extra = 1
    fields = ['step_number', 'description', 'image_url', 'duration', 'tips']
    ordering = ['step_number']


@admin.register(Recipe)
class RecipeAdmin(ExportCsvMixin, admin.ModelAdmin):
    """
    食谱管理类

    配置食谱在 Django Admin 后台的显示和操作方式。
    功能：列表管理、批量操作、内联编辑食材和步骤、CSV 导出。
    """

    # CSV 导出配置
    export_fields = [
        'id', 'name', 'author', 'category', 'difficulty',
        'cooking_time', 'views', 'likes', 'favorites',
        'is_published', 'created_at'
    ]
    export_filename = 'recipes'

    # 内联编辑食材和步骤
    inlines = [RecipeIngredientInline, CookingStepInline]

    # 列表页显示的字段
    list_display = [
        'id', 'name', 'author', 'category', 'difficulty',
        'cooking_time', 'views', 'likes', 'favorites',
        'is_published', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'name']

    # 列表页可直接编辑的字段（快速切换发布状态）
    list_editable = ['is_published']

    # 列表页右侧过滤器
    list_filter = [
        'category', 'difficulty', 'cuisine_type',
        'is_published', 'created_at'
    ]

    # 搜索字段
    search_fields = [
        'name', 'description', 'author__username'
    ]

    # 批量操作
    actions = ['make_published', 'make_unpublished', 'export_as_csv']

    # 只读字段
    readonly_fields = [
        'views', 'likes', 'favorites', 'created_at', 'updated_at'
    ]

    # 字段分组
    fieldsets = [
        ('基本信息', {
            'fields': ['name', 'cover_image', 'author', 'description']
        }),
        ('分类信息', {
            'fields': ['category', 'cuisine_type', 'difficulty', 'tags']
        }),
        ('详细信息', {
            'fields': ['cooking_time', 'servings', 'total_calories']
        }),
        ('统计信息', {
            'fields': ['views', 'likes', 'favorites'],
            'classes': ['collapse']
        }),
        ('发布设置', {
            'fields': ['is_published']
        }),
        ('时间信息', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    # 每页显示数量
    list_per_page = 20

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')

    def make_published(self, request, queryset):
        count = queryset.update(is_published=True)
        self.message_user(request, f'已批量发布 {count} 个食谱')

    make_published.short_description = '批量发布所选食谱'

    def make_unpublished(self, request, queryset):
        count = queryset.update(is_published=False)
        self.message_user(request, f'已批量取消发布 {count} 个食谱')

    make_unpublished.short_description = '批量取消发布所选食谱'


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    """
    用户行为管理类

    配置用户行为在 Django Admin 后台的显示和操作方式。
    列表页顶部显示行为类型统计和热门食谱排行。
    """

    # 自定义列表页模板（用于显示统计面板）
    change_list_template = 'admin/recipe/userbehavior/change_list.html'

    # 列表页显示的字段
    list_display = [
        'id', 'user', 'recipe', 'behavior_type', 'created_at'
    ]

    # 列表页可点击进入详情的字段
    list_display_links = ['id', 'user']

    # 列表页右侧过滤器
    list_filter = [
        'behavior_type', 'created_at'
    ]

    # 搜索字段
    search_fields = [
        'user__username', 'recipe__name'
    ]

    # 只读字段
    readonly_fields = [
        'user', 'recipe', 'behavior_type', 'created_at'
    ]

    # 每页显示数量
    list_per_page = 50

    # 日期层级导航
    date_hierarchy = 'created_at'

    # 排序方式
    ordering = ['-created_at']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'recipe')

    def changelist_view(self, request, extra_context=None):
        """注入行为统计数据到列表页模板上下文"""
        # 按行为类型统计数量
        behavior_stats = list(
            UserBehavior.objects
            .values('behavior_type')
            .annotate(count=Count('id'))
            .order_by('behavior_type')
        )
        behavior_type_map = dict(UserBehavior.BEHAVIOR_TYPE_CHOICES)
        # 为每条统计添加中文名称
        for item in behavior_stats:
            item['type_display'] = behavior_type_map.get(
                item['behavior_type'], item['behavior_type']
            )

        # 热门食谱 Top 10（按行为总数）
        hot_recipes = list(
            UserBehavior.objects
            .values('recipe__id', 'recipe__name')
            .annotate(total=Count('id'))
            .order_by('-total')[:10]
        )

        extra_context = extra_context or {}
        extra_context['behavior_stats'] = behavior_stats
        extra_context['hot_recipes'] = hot_recipes
        return super().changelist_view(request, extra_context=extra_context)
