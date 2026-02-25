"""
购物清单模块路由配置
"""

from django.urls import path
from .views import (
    ShoppingListView,
    ShoppingListItemView,
    ShoppingListGenerateView
)

# 应用命名空间
app_name = 'shopping'

urlpatterns = [
    # 购物清单列表和创建
    # GET /api/shopping-list/ - 获取购物清单
    # POST /api/shopping-list/ - 添加食材到购物清单
    path('', ShoppingListView.as_view(), name='list'),

    # 购物清单项更新和删除
    # PUT /api/shopping-list/<item_id>/ - 完整更新
    # PATCH /api/shopping-list/<item_id>/ - 部分更新
    # DELETE /api/shopping-list/<item_id>/ - 删除
    path('<int:item_id>/', ShoppingListItemView.as_view(), name='item'),

    # 基于食谱生成购物清单
    # POST /api/shopping-list/generate/
    path('generate/', ShoppingListGenerateView.as_view(), name='generate'),
]
