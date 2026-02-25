"""
分页器模块

本模块提供统一的分页配置，用于所有需要分页的 API 接口。
使用 DRF 的 PageNumberPagination 实现页码分页。

分页参数：
    - page: 页码（从 1 开始）
    - page_size: 每页数量（默认 20，最大 100）

使用示例：
    GET /api/recipe/?page=2&page_size=30
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    标准分页器

    这是项目中所有列表接口的默认分页器。
    前端可以通过 page 和 page_size 参数控制分页。

    配置说明：
        page_size: 默认每页返回 20 条数据
        page_size_query_param: 允许前端通过 page_size 参数自定义每页数量
        max_page_size: 限制每页最多返回 100 条数据，防止一次查询过多数据
        page_query_param: 页码参数名，默认为 'page'

    返回格式：
    {
        "count": 100,              # 总记录数
        "next": "http://...?page=3",   # 下一页链接（如果没有则为 null）
        "previous": "http://...?page=1", # 上一页链接（如果没有则为 null）
        "results": [...]           # 当前页数据列表
    }

    使用示例：
        # 在视图中使用
        class RecipeListView(generics.ListAPIView):
            queryset = Recipe.objects.all()
            serializer_class = RecipeSerializer
            pagination_class = StandardResultsSetPagination

        # 前端调用
        GET /api/recipe/?page=2&page_size=30
    """

    # 默认每页返回 20 条数据
    page_size = 20

    # 允许前端通过此参数自定义每页数量
    # 例如: ?page_size=50
    page_size_query_param = 'page_size'

    # 限制每页最多返回 100 条数据
    # 防止前端请求过大的 page_size 导致性能问题
    max_page_size = 100

    # 页码参数名（默认值，可以不设置）
    page_query_param = 'page'


class LargeResultsSetPagination(PageNumberPagination):
    """
    大数据量分页器

    用于数据量较大的场景，每页返回更多数据。
    适用于后台管理系统或数据导出等场景。

    配置说明：
        page_size: 默认每页返回 50 条数据
        max_page_size: 限制每页最多返回 500 条数据

    使用示例：
        class RecipeAdminListView(generics.ListAPIView):
            queryset = Recipe.objects.all()
            serializer_class = RecipeSerializer
            pagination_class = LargeResultsSetPagination
    """

    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


class SmallResultsSetPagination(PageNumberPagination):
    """
    小数据量分页器

    用于数据量较小或需要频繁刷新的场景。
    适用于评论列表、动态流等场景。

    配置说明：
        page_size: 默认每页返回 10 条数据
        max_page_size: 限制每页最多返回 50 条数据

    使用示例：
        class CommentListView(generics.ListAPIView):
            queryset = Comment.objects.all()
            serializer_class = CommentSerializer
            pagination_class = SmallResultsSetPagination
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
