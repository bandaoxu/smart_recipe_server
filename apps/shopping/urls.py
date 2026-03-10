"""
购物清单模块路由配置
"""

from django.urls import path
from .views import (
    ShoppingListView,
    ShoppingListItemView,
    ShoppingListGenerateView,
    CreateShareView,
    RevokeShareView,
    SharedListView,
    SharedItemUpdateView,
)

# 应用命名空间
app_name = 'shopping'

urlpatterns = [
    # 购物清单列表和创建
    path('', ShoppingListView.as_view(), name='list'),

    # 购物清单项更新和删除
    path('<int:item_id>/', ShoppingListItemView.as_view(), name='item'),

    # 基于食谱生成购物清单
    path('generate/', ShoppingListGenerateView.as_view(), name='generate'),

    # 分享：创建 Token（需登录）
    path('share/', CreateShareView.as_view(), name='share-create'),

    # 分享：撤销 Token（需登录）
    path('share/<str:token>/', RevokeShareView.as_view(), name='share-revoke'),

    # 分享：查看共享清单（无需登录）
    path('shared/<str:token>/', SharedListView.as_view(), name='shared-list'),

    # 分享：更新共享清单中的购买状态（无需登录，需 edit 权限）
    path('shared/<str:token>/<int:item_id>/', SharedItemUpdateView.as_view(), name='shared-item-update'),
]
