"""
食材数据集加载与数据增强

数据目录结构：
    data/ingredients/
        西红柿/
            img_001.jpg
            img_002.jpg
            ...
        鸡蛋/
            img_001.jpg
            ...

MobileNetV3Small 内置预处理（include_preprocessing=True），
输入图片为 [0, 255] 的 float32，无需额外归一化。
"""

import tensorflow as tf

IMG_SIZE = 224
AUTOTUNE = tf.data.AUTOTUNE

# 训练期数据增强层
_augmentation = tf.keras.Sequential(
    [
        tf.keras.layers.RandomFlip('horizontal'),
        tf.keras.layers.RandomRotation(0.1),
        tf.keras.layers.RandomZoom(0.1),
        tf.keras.layers.RandomBrightness(0.1),
    ],
    name='augmentation',
)


def get_datasets(data_dir: str, batch_size: int = 32):
    """
    从目录加载训练集与验证集（8:2 切分）

    参数：
        data_dir: ImageFolder 格式的根目录路径
        batch_size: 批大小

    返回：
        (train_ds, val_ds, class_names)
        - train_ds: 含增强的训练 Dataset
        - val_ds: 验证 Dataset
        - class_names: 类别名称列表，索引与标签对应
    """
    common_kwargs = dict(
        directory=data_dir,
        validation_split=0.2,
        seed=42,
        image_size=(IMG_SIZE, IMG_SIZE),
        batch_size=batch_size,
        label_mode='int',
    )

    train_ds = tf.keras.utils.image_dataset_from_directory(
        subset='training', **common_kwargs
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        subset='validation', **common_kwargs
    )

    class_names = train_ds.class_names

    # 训练集：数据增强 + prefetch
    train_ds = train_ds.map(
        lambda x, y: (_augmentation(x, training=True), y),
        num_parallel_calls=AUTOTUNE,
    ).prefetch(AUTOTUNE)

    # 验证集：只 prefetch
    val_ds = val_ds.prefetch(AUTOTUNE)

    return train_ds, val_ds, class_names
