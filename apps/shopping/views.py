"""
购物清单模块视图

本模块定义了购物清单相关的 API 视图。

视图：
    - ShoppingListView: 购物清单列表、创建、删除
    - ShoppingListUpdateView: 更新购物清单项（标记购买状态等）
    - ShoppingListGenerateView: 基于食谱生成购物清单
    - CreateShareView: 创建分享链接
    - RevokeShareView: 撤销分享链接
    - SharedListView: 通过 Token 查看分享清单
    - SharedItemUpdateView: 通过 Token 更新分享清单中的购买状态
"""

import uuid
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from common.response import success_response, error_response
from .models import ShoppingList, ShoppingListShare
from .serializers import ShoppingListSerializer
from apps.recipe.models import Recipe


class ShoppingListView(APIView):
    """
    购物清单视图

    获取、创建、删除购物清单项。

    请求方法：GET, POST, DELETE
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取购物清单"""
        # 获取当前用户的购物清单
        queryset = ShoppingList.objects.filter(user=request.user)

        # 是否只显示未购买的
        only_unpurchased = request.query_params.get('only_unpurchased', 'false').lower() == 'true'
        if only_unpurchased:
            queryset = queryset.filter(is_purchased=False)

        serializer = ShoppingListSerializer(queryset, many=True)
        return success_response(data=serializer.data, message='获取购物清单成功')

    def post(self, request):
        """添加食材到购物清单"""
        serializer = ShoppingListSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message='添加成功')
        else:
            return error_response(message='添加失败', data=serializer.errors, code=400)


class ShoppingListItemView(APIView):
    """
    购物清单项视图

    更新或删除指定的购物清单项。

    请求方法：PUT, PATCH, DELETE
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        """完整更新购物清单项"""
        return self._update_item(request, item_id, partial=False)

    def patch(self, request, item_id):
        """部分更新购物清单项"""
        return self._update_item(request, item_id, partial=True)

    def delete(self, request, item_id):
        """删除购物清单项"""
        try:
            item = ShoppingList.objects.get(id=item_id, user=request.user)
        except ShoppingList.DoesNotExist:
            return error_response(message='购物清单项不存在', code=404)

        item.delete()
        return success_response(message='删除成功')

    def _update_item(self, request, item_id, partial=False):
        """更新购物清单项的内部方法"""
        try:
            item = ShoppingList.objects.get(id=item_id, user=request.user)
        except ShoppingList.DoesNotExist:
            return error_response(message='购物清单项不存在', code=404)

        serializer = ShoppingListSerializer(
            item,
            data=request.data,
            partial=partial,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message='更新成功')
        else:
            return error_response(message='更新失败', data=serializer.errors, code=400)


class ShoppingListGenerateView(APIView):
    """
    基于食谱生成购物清单视图

    根据指定的食谱，将所需食材添加到购物清单。

    请求方法：POST
    权限：需要登录
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """生成购物清单"""
        recipe_id = request.data.get('recipe_id')

        if not recipe_id:
            return error_response(message='缺少 recipe_id 参数', code=400)

        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        # 获取食谱的所有食材
        recipe_ingredients = recipe.recipe_ingredients.all()

        if not recipe_ingredients.exists():
            return error_response(message='该食谱没有食材信息', code=400)

        # 添加到购物清单（如果已存在则累加数量）
        added_count = 0
        for ri in recipe_ingredients:
            # 检查是否已存在
            existing_item = ShoppingList.objects.filter(
                user=request.user,
                ingredient=ri.ingredient,
                is_purchased=False
            ).first()

            if existing_item:
                # 已存在，累加数量
                existing_item.quantity += ri.quantity
                existing_item.save()
            else:
                # 不存在，创建新的
                ShoppingList.objects.create(
                    user=request.user,
                    ingredient=ri.ingredient,
                    quantity=ri.quantity,
                    unit=ri.unit
                )
                added_count += 1

        return success_response(
            data={'added_count': added_count, 'total_ingredients': recipe_ingredients.count()},
            message='生成购物清单成功'
        )


class CreateShareView(APIView):
    """创建购物清单分享 Token — POST /api/shopping-list/share/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        permission = request.data.get('permission', 'read')
        if permission not in ('read', 'edit'):
            return error_response(message='permission 必须为 read 或 edit', code=400)

        days = int(request.data.get('days', 7))
        if days not in (1, 3, 7, 30):
            days = 7

        token = uuid.uuid4().hex
        share = ShoppingListShare.objects.create(
            token=token,
            owner=request.user,
            permission=permission,
            expires_at=timezone.now() + timedelta(days=days),
        )
        return success_response(
            data={
                'token': share.token,
                'permission': share.permission,
                'expires_at': share.expires_at.isoformat(),
                'share_path': f'/pages/shopping/share?token={share.token}',
            },
            message='分享链接创建成功'
        )


class RevokeShareView(APIView):
    """撤销分享 Token — DELETE /api/shopping-list/share/<token>/"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, token):
        try:
            share = ShoppingListShare.objects.get(token=token, owner=request.user)
        except ShoppingListShare.DoesNotExist:
            return error_response(message='分享不存在', code=404)
        share.is_active = False
        share.save(update_fields=['is_active'])
        return success_response(message='分享已撤销')


class SharedListView(APIView):
    """通过 Token 查看分享的购物清单 — GET /api/shopping-list/shared/<token>/"""

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            share = ShoppingListShare.objects.select_related('owner').get(token=token)
        except ShoppingListShare.DoesNotExist:
            return error_response(message='链接无效', code=404)

        if not share.is_valid():
            return error_response(message='链接已失效或已过期', code=403)

        items = ShoppingList.objects.filter(user=share.owner).select_related('ingredient')
        serializer = ShoppingListSerializer(items, many=True)

        owner_profile = getattr(share.owner, 'userprofile', None)
        owner_name = (owner_profile.nickname if owner_profile else None) or share.owner.username

        return success_response(
            data={
                'items': serializer.data,
                'meta': {
                    'owner_name': owner_name,
                    'permission': share.permission,
                    'expires_at': share.expires_at.isoformat(),
                },
            },
            message='获取成功'
        )


class SharedItemUpdateView(APIView):
    """通过 Token 更新分享清单中的购买状态 — PATCH /api/shopping-list/shared/<token>/<item_id>/"""

    permission_classes = [AllowAny]

    def patch(self, request, token, item_id):
        try:
            share = ShoppingListShare.objects.get(token=token)
        except ShoppingListShare.DoesNotExist:
            return error_response(message='链接无效', code=404)

        if not share.is_valid():
            return error_response(message='链接已失效或已过期', code=403)

        if share.permission != 'edit':
            return error_response(message='此分享链接为只读，不可修改', code=403)

        try:
            item = ShoppingList.objects.get(id=item_id, user=share.owner)
        except ShoppingList.DoesNotExist:
            return error_response(message='清单项不存在', code=404)

        # 仅允许更新 is_purchased 字段
        is_purchased = request.data.get('is_purchased')
        if is_purchased is None:
            return error_response(message='缺少 is_purchased 参数', code=400)

        item.is_purchased = bool(is_purchased)
        item.save(update_fields=['is_purchased'])
        return success_response(
            data={'id': item.id, 'is_purchased': item.is_purchased},
            message='更新成功'
        )
