"""
权限控制模块

本模块提供自定义的权限类，用于控制 API 接口的访问权限。
配合 DRF 的权限系统，实现细粒度的权限控制。

权限类型：
    - IsOwnerOrReadOnly: 只有作者可以编辑，其他人只能查看
    - IsOwner: 只有所有者可以访问
    - IsAdminOrReadOnly: 只有管理员可以编辑，其他人只能查看
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    只有作者可以编辑的权限类

    这个权限类用于保护资源，确保只有资源的所有者可以修改或删除它。
    其他用户可以查看资源，但不能修改。

    适用场景：
        - 食谱管理：只有食谱作者可以编辑或删除自己的食谱
        - 用户资料：只有用户本人可以修改自己的资料
        - 评论管理：只有评论作者可以删除自己的评论
        - 动态管理：只有动态发布者可以删除自己的动态

    权限规则：
        - GET, HEAD, OPTIONS 请求（安全方法）：所有人都可以访问
        - POST, PUT, PATCH, DELETE 请求（不安全方法）：只有所有者可以访问

    使用示例：
        class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
            queryset = Recipe.objects.all()
            serializer_class = RecipeSerializer
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    注意：
        - 模型必须有 author 或 user 字段，指向资源的所有者
        - 如果字段名不同，需要在视图中重写 get_object() 方法
    """

    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限访问对象

        参数：
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象（如 Recipe, Comment 等）

        返回：
            bool: True 表示有权限，False 表示无权限
        """
        # 读取权限：允许所有请求（GET, HEAD, OPTIONS）
        # SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限：只有对象的所有者才能修改
        # 尝试多个可能的所有者字段名
        # 优先检查 author，其次检查 user
        if hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        else:
            # 如果对象没有所有者字段，默认拒绝访问
            return False


class IsOwner(permissions.BasePermission):
    """
    只有所有者可以访问的权限类

    这个权限类用于完全保护资源，确保只有资源的所有者可以访问。
    即使是查看操作，也只有所有者才能执行。

    适用场景：
        - 用户健康档案：只有用户本人可以查看和修改
        - 购物清单：只有用户本人可以查看和管理
        - 用户行为记录：只有用户本人可以查看

    权限规则：
        - 所有请求（GET, POST, PUT, DELETE）：只有所有者可以访问

    使用示例：
        class ShoppingListView(generics.ListCreateAPIView):
            serializer_class = ShoppingListSerializer
            permission_classes = [IsAuthenticated, IsOwner]

            def get_queryset(self):
                # 只返回当前用户的购物清单
                return ShoppingList.objects.filter(user=request.user)
    """

    def has_object_permission(self, request, view, obj):
        """
        检查用户是否是对象的所有者

        参数：
            request: HTTP 请求对象
            view: 视图对象
            obj: 要访问的对象

        返回：
            bool: True 表示是所有者，False 表示不是
        """
        # 检查对象是否属于当前用户
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        else:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    只有管理员可以编辑的权限类

    这个权限类用于保护系统数据，确保只有管理员可以修改。
    普通用户可以查看数据，但不能修改。

    适用场景：
        - 食材库管理：只有管理员可以添加、修改、删除食材
        - 系统配置：只有管理员可以修改系统设置
        - 推荐配置：只有管理员可以调整推荐算法参数

    权限规则：
        - GET, HEAD, OPTIONS 请求：所有人都可以访问
        - POST, PUT, PATCH, DELETE 请求：只有管理员可以访问

    使用示例：
        class IngredientViewSet(viewsets.ModelViewSet):
            queryset = Ingredient.objects.all()
            serializer_class = IngredientSerializer
            permission_classes = [IsAdminOrReadOnly]
    """

    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图

        参数：
            request: HTTP 请求对象
            view: 视图对象

        返回：
            bool: True 表示有权限，False 表示无权限
        """
        # 读取权限：允许所有请求
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限：只有管理员可以访问
        return request.user and request.user.is_staff


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    已登录用户可以编辑，未登录用户只能查看

    这个权限类允许所有人浏览内容，但只有登录用户可以创建或修改内容。

    适用场景：
        - 评论功能：游客可以浏览评论，但只有登录用户可以发表评论
        - 点赞功能：游客可以查看点赞数，但只有登录用户可以点赞
        - 收藏功能：游客可以浏览食谱，但只有登录用户可以收藏

    权限规则：
        - GET, HEAD, OPTIONS 请求：所有人都可以访问
        - POST, PUT, PATCH, DELETE 请求：只有登录用户可以访问

    使用示例：
        class CommentViewSet(viewsets.ModelViewSet):
            queryset = Comment.objects.all()
            serializer_class = CommentSerializer
            permission_classes = [IsAuthenticatedOrReadOnly]
    """

    def has_permission(self, request, view):
        """
        检查用户是否有权限访问视图

        参数：
            request: HTTP 请求对象
            view: 视图对象

        返回：
            bool: True 表示有权限，False 表示无权限
        """
        # 读取权限：允许所有请求
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限：只有登录用户可以访问
        return request.user and request.user.is_authenticated
