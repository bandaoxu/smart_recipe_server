"""
创建 Django Admin 权限分组管理命令

用法：uv run python manage.py create_admin_groups

创建4个预定义权限组：
- 内容管理员：管理食谱和社区模块
- 用户管理员：管理用户档案和关注关系
- 数据管理员：所有模块只读查看权限
- 超级管理员：通过 is_superuser=True 拥有所有权限（无需分组，此命令不创建）
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = '创建 Admin 后台所需的权限分组'

    # 各分组的应用名与模型名配置
    GROUPS_CONFIG = {
        '内容管理员': {
            'apps': ['recipe', 'community'],
            'permissions': ['add', 'change', 'delete', 'view'],
        },
        '用户管理员': {
            'apps': ['user'],
            'permissions': ['add', 'change', 'delete', 'view'],
        },
        '数据管理员': {
            'apps': ['recipe', 'community', 'ingredient', 'nutrition', 'shopping', 'user'],
            'permissions': ['view'],
        },
    }

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for group_name, config in self.GROUPS_CONFIG.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                created_count += 1
                self.stdout.write(f'  创建分组：{group_name}')
            else:
                updated_count += 1
                self.stdout.write(f'  更新分组：{group_name}')

            # 收集权限
            permissions = []
            for app_label in config['apps']:
                content_types = ContentType.objects.filter(app_label=app_label)
                for ct in content_types:
                    for perm_codename_prefix in config['permissions']:
                        codename = f'{perm_codename_prefix}_{ct.model}'
                        try:
                            perm = Permission.objects.get(
                                codename=codename,
                                content_type=ct
                            )
                            permissions.append(perm)
                        except Permission.DoesNotExist:
                            pass

            group.permissions.set(permissions)
            self.stdout.write(
                f'    → 分配 {len(permissions)} 个权限'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！新建 {created_count} 个分组，更新 {updated_count} 个分组。\n'
                '提示：超级管理员请直接设置 is_superuser=True，无需分配分组。'
            )
        )
