"""
用户模块应用配置
"""

from django.apps import AppConfig


class UserConfig(AppConfig):
    """
    用户模块配置类

    配置用户模块的基本信息。
    """

    # 默认主键字段类型
    default_auto_field = 'django.db.models.BigAutoField'

    # 应用名称（必须与目录名一致）
    name = 'apps.user'

    # 应用的可读名称（在 Django Admin 中显示）
    verbose_name = '用户管理'
