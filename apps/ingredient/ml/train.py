"""
食材识别模型训练

两阶段迁移学习：
  Phase 1（10 epochs）：冻结 backbone，高学习率训练分类头
  Phase 2（epochs 参数控制）：解冻最后 20 层，低学习率 fine-tune

用法（通过 Django 管理命令调用）：
    uv run python manage.py train_ingredient_model
    uv run python manage.py train_ingredient_model --data-dir data/ingredients --epochs 20
"""

import json
import os

import tensorflow as tf

from .dataset import get_datasets
from .model import build_model

SAVED_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
MODEL_PATH = os.path.join(SAVED_DIR, "ingredient_classifier.keras")
CLASSES_PATH = os.path.join(SAVED_DIR, "classes.json")


def train(
    data_dir: str = "data/ingredients",
    epochs: int = 20,
    batch_size: int = 32,
    lr: float = 0.001,
    logger=None,
):
    """
    执行两阶段迁移学习训练并保存模型

    参数：
        data_dir:   ImageFolder 格式的数据集根目录
        epochs:     Phase 2 最大训练轮数
        batch_size: 批大小
        lr:         Phase 1 学习率（Phase 2 使用 lr/10）
        logger:     可选的日志函数，默认 print
    """
    log = logger or print
    os.makedirs(SAVED_DIR, exist_ok=True)

    # ── 加载数据集 ────────────────────────────────────────────────────────────
    log(f"[train] 加载数据集：{data_dir}")
    train_ds, val_ds, class_names = get_datasets(data_dir, batch_size=batch_size)
    num_classes = len(class_names)
    log(f"[train] 类别数：{num_classes}，类别：{class_names}")

    if num_classes < 2:
        raise ValueError("至少需要 2 个食材类别才能训练，请先采集数据集。")

    # ── 构建模型 ──────────────────────────────────────────────────────────────
    model, base_model = build_model(num_classes)
    log(f"[train] 模型参数量：{model.count_params():,}")

    # ── Phase 1：冻结 backbone，只训练分类头 ──────────────────────────────────
    log("[train] Phase 1：训练分类头（backbone 冻结，最多 10 轮）")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=10,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy",
                patience=3,
                restore_best_weights=True,
                verbose=1,
            )
        ],
        verbose=1,
    )

    # ── Phase 2：解冻最后 20 层，fine-tune ────────────────────────────────────
    log("[train] Phase 2：fine-tune（解冻最后 20 层）")
    base_model.trainable = True
    for layer in base_model.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr / 10),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=MODEL_PATH,
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1,
    )
    early_stop_cb = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True,
        verbose=1,
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=[checkpoint_cb, early_stop_cb],
        verbose=1,
    )

    # 早停恢复最佳权重后，确保以 SavedModel 格式写入磁盘
    model.save(MODEL_PATH, save_format="tf")

    # ── 保存类别映射 ──────────────────────────────────────────────────────────
    with open(CLASSES_PATH, "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    log(f"[train] 训练完成，模型已保存至：{MODEL_PATH}")
    log(f"[train] 类别文件已保存至：{CLASSES_PATH}")

    # 评估最终验证集指标
    loss, acc = model.evaluate(val_ds, verbose=0)
    log(f"[train] 最终验证集 loss={loss:.4f}，accuracy={acc:.4f}")

    return model, class_names
