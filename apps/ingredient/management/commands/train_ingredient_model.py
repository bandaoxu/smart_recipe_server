"""
Django 管理命令：训练食材识别模型

用法：
    uv run python manage.py train_ingredient_model
    uv run python manage.py train_ingredient_model --data-dir data/ingredients --epochs 20 --batch-size 32 --lr 0.001

训练完成后，推理服务（IngredientClassifier）会在下次请求时自动重载新模型。
"""

import os

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = '使用 MobileNetV3Small 迁移学习训练食材识别模型'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            default='data/ingredients',
            help='ImageFolder 格式的数据集根目录（默认：data/ingredients）',
        )
        parser.add_argument(
            '--epochs',
            type=int,
            default=20,
            help='Phase 2 最大训练轮数（默认：20）',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='批大小（默认：32）',
        )
        parser.add_argument(
            '--lr',
            type=float,
            default=0.001,
            help='Phase 1 学习率（默认：0.001，Phase 2 自动除以 10）',
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        epochs = options['epochs']
        batch_size = options['batch_size']
        lr = options['lr']

        # 验证数据目录
        if not os.path.isdir(data_dir):
            raise CommandError(
                f'数据目录不存在：{data_dir}\n'
                f'请先运行：uv run python scripts/collect_dataset.py --count 100'
            )

        sub_dirs = [
            d for d in os.listdir(data_dir)
            if os.path.isdir(os.path.join(data_dir, d))
        ]
        if len(sub_dirs) < 2:
            raise CommandError(
                f'数据目录 {data_dir} 中类别数量不足（当前 {len(sub_dirs)} 个），至少需要 2 个。'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'开始训练 | 数据目录：{data_dir} | 类别数：{len(sub_dirs)} | '
                f'epochs={epochs} | batch_size={batch_size} | lr={lr}'
            )
        )

        try:
            from apps.ingredient.ml.train import train
            from apps.ingredient.ml.inference import IngredientClassifier

            train(
                data_dir=data_dir,
                epochs=epochs,
                batch_size=batch_size,
                lr=lr,
                logger=self.stdout.write,
            )

            # 训练完成后重载推理服务单例
            IngredientClassifier().reload()
            self.stdout.write(self.style.SUCCESS('推理服务已重载，模型立即生效。'))

        except Exception as e:
            raise CommandError(f'训练失败：{e}') from e
