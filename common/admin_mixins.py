"""
Admin 通用 Mixin

提供可复用的 Django Admin 功能，各模块 Admin 类通过继承使用。
"""

import csv
from django.http import HttpResponse


class ExportCsvMixin:
    """
    CSV 导出 Mixin

    各模块 Admin 继承此类，并定义 export_fields 和 export_filename，
    即可在 Actions 中获得"导出所选为 CSV"功能。

    子类配置示例：
        class RecipeAdmin(ExportCsvMixin, admin.ModelAdmin):
            export_fields = ['id', 'name', 'author', 'created_at']
            export_filename = 'recipes'
            actions = ['export_as_csv']
    """

    export_fields = []
    export_filename = 'export'

    def export_as_csv(self, request, queryset):
        """将所选记录导出为 UTF-8 BOM 编码的 CSV 文件（Excel 可直接打开）"""
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = (
            f'attachment; filename="{self.export_filename}.csv"'
        )
        writer = csv.writer(response)

        # 表头：使用字段的 verbose_name，如无则直接用字段名
        headers = []
        for field_name in self.export_fields:
            try:
                field = self.model._meta.get_field(field_name)
                headers.append(str(field.verbose_name))
            except Exception:
                headers.append(field_name)
        writer.writerow(headers)

        # 数据行
        for obj in queryset:
            row = []
            for field_name in self.export_fields:
                value = getattr(obj, field_name, '')
                # 对外键/关联对象调用 str()
                if hasattr(value, 'pk'):
                    value = str(value)
                # 对 callable（如自定义方法）调用
                elif callable(value):
                    value = value()
                row.append(value)
            writer.writerow(row)

        return response

    export_as_csv.short_description = '导出所选为 CSV'
