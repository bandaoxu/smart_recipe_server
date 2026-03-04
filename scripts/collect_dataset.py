"""
食材图片数据集采集脚本

使用 icrawler 从 Bing 图片搜索下载食材图片，组织为 ImageFolder 格式：
    data/ingredients/
        西红柿/   img_000001.jpg  img_000002.jpg ...
        鸡蛋/     img_000001.jpg  ...

用法（在 smart_recipe_server/ 目录下执行）：
    uv run python scripts/collect_dataset.py
    uv run python scripts/collect_dataset.py --count 150
    uv run python scripts/collect_dataset.py --names 西红柿,鸡蛋,土豆 --count 100
    uv run python scripts/collect_dataset.py --output-dir my/custom/path

依赖：icrawler（已在 pyproject.toml 中声明）
"""

import argparse
import os
import sys

# 将 smart_recipe_server 根目录加入路径，以便 django.setup()
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, BASE_DIR)
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_recipe_server.settings")

import django

django.setup()


def collect(ingredient_names: list[str], output_dir: str, count: int):
    """
    对每个食材名下载图片

    参数：
        ingredient_names: 食材名称列表
        output_dir:       保存根目录
        count:            每个食材下载数量
    """
    try:
        from icrawler.builtin import BingImageCrawler
    except ImportError:
        print("[error] 请先安装依赖：uv sync")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    total = len(ingredient_names)

    for i, name in enumerate(ingredient_names, 1):
        save_dir = os.path.join(output_dir, name)
        os.makedirs(save_dir, exist_ok=True)

        # 统计已有图片数量，跳过已满足数量的目录
        existing = [
            f
            for f in os.listdir(save_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]
        if len(existing) >= count:
            print(f"[{i}/{total}] {name}：已有 {len(existing)} 张，跳过")
            continue

        need = count - len(existing)
        print(f"[{i}/{total}] {name}：已有 {len(existing)} 张，下载 {need} 张")

        crawler = BingImageCrawler(
            storage={"root_dir": save_dir},
            downloader_threads=4,
            parser_threads=2,
        )
        try:
            # 搜索关键词使用"食材名 食材"以提高相关性
            crawler.crawl(keyword=f"{name} 食材", max_num=need, min_size=(100, 100))
        except Exception as e:
            print(f"[warn] {name} 下载异常：{e}，继续下一个")

    print(f"\n[done] 数据集已保存至：{output_dir}")
    _print_summary(output_dir)


def _print_summary(output_dir: str):
    """打印各类别图片数量汇总"""
    print("\n── 数据集汇总 ──")
    total_images = 0
    for cls_name in sorted(os.listdir(output_dir)):
        cls_path = os.path.join(output_dir, cls_name)
        if not os.path.isdir(cls_path):
            continue
        imgs = [
            f
            for f in os.listdir(cls_path)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]
        print(f"  {cls_name}: {len(imgs)} 张")
        total_images += len(imgs)
    print(f"合计：{total_images} 张")


def main():
    parser = argparse.ArgumentParser(description="食材图片数据集采集")
    parser.add_argument(
        "--names",
        default="",
        help="指定采集的食材名（逗号分隔），不传则从数据库读取全部食材",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="每个食材下载图片数量（默认 100）",
    )
    parser.add_argument(
        "--output-dir",
        default="data/ingredients",
        help="数据集保存目录（默认 data/ingredients）",
    )
    args = parser.parse_args()

    # 确定食材列表
    if args.names:
        ingredient_names = [n.strip() for n in args.names.split(",") if n.strip()]
    else:
        from apps.ingredient.models import Ingredient

        ingredient_names = list(Ingredient.objects.values_list("name", flat=True))
        if not ingredient_names:
            print(
                "[warn] 数据库中没有食材记录，请先通过 admin 或 fixture 导入食材数据。"
            )
            sys.exit(0)

    print(f"准备采集 {len(ingredient_names)} 种食材，每种 {args.count} 张")
    print(f"保存目录：{args.output_dir}")
    collect(ingredient_names, args.output_dir, args.count)


if __name__ == "__main__":
    main()
