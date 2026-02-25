"""
统一响应格式模块

本模块提供统一的 API 响应格式，确保所有接口返回的数据结构一致。
这样可以方便前端处理响应数据，提升代码的可维护性。

响应格式：
{
    "code": 200,           # HTTP 状态码
    "message": "success",  # 提示信息
    "data": {...}          # 响应数据
}
"""

from rest_framework.response import Response


def success_response(data=None, message="操作成功", code=200):
    """
    成功响应函数

    用于返回成功的 API 响应。

    参数：
        data (dict/list/None): 返回的数据，可以是字典、列表或 None
        message (str): 成功提示信息，默认为 "操作成功"
        code (int): HTTP 状态码，默认为 200

    返回：
        Response: DRF Response 对象，包含统一格式的成功响应

    使用示例：
        # 返回列表数据
        return success_response(data=recipes, message="获取食谱列表成功")

        # 返回单个对象
        return success_response(data=recipe, message="获取食谱详情成功")

        # 只返回消息
        return success_response(message="删除成功")
    """
    return Response({
        "code": code,
        "message": message,
        "data": data
    }, status=code)


def error_response(message="操作失败", code=400, data=None):
    """
    错误响应函数

    用于返回错误的 API 响应。

    参数：
        message (str): 错误提示信息，默认为 "操作失败"
        code (int): HTTP 状态码，默认为 400
        data (dict/None): 额外的错误信息，如字段验证错误详情

    返回：
        Response: DRF Response 对象，包含统一格式的错误响应

    常见状态码：
        400: 客户端请求错误（参数错误、验证失败等）
        401: 未授权（用户未登录）
        403: 禁止访问（权限不足）
        404: 资源不存在
        500: 服务器内部错误

    使用示例：
        # 参数错误
        return error_response(message="缺少必填参数", code=400)

        # 未登录
        return error_response(message="请先登录", code=401)

        # 权限不足
        return error_response(message="无权限操作", code=403)

        # 资源不存在
        return error_response(message="食谱不存在", code=404)

        # 带详细错误信息
        return error_response(
            message="表单验证失败",
            code=400,
            data={"name": ["食谱名称不能为空"]}
        )
    """
    return Response({
        "code": code,
        "message": message,
        "data": data
    }, status=code)


def paginated_response(page_data, message="获取列表成功", code=200):
    """
    分页响应函数

    用于返回分页数据的 API 响应。
    这个函数会保留 DRF 分页器返回的分页信息（count, next, previous）。

    参数：
        page_data (dict): 分页器返回的数据，包含 count, next, previous, results
        message (str): 成功提示信息，默认为 "获取列表成功"
        code (int): HTTP 状态码，默认为 200

    返回：
        Response: DRF Response 对象，包含统一格式的分页响应

    响应格式：
    {
        "code": 200,
        "message": "获取列表成功",
        "data": {
            "count": 100,           # 总记录数
            "next": "http://...",   # 下一页链接
            "previous": null,       # 上一页链接
            "results": [...]        # 当前页数据列表
        }
    }

    使用示例：
        # 在视图中使用
        page = self.paginate_queryset(recipes)
        serializer = RecipeSerializer(page, many=True)
        page_data = self.get_paginated_response(serializer.data).data
        return paginated_response(page_data, message="获取食谱列表成功")
    """
    return Response({
        "code": code,
        "message": message,
        "data": page_data
    }, status=code)
