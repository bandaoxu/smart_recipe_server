"""
食材识别模型定义

使用 MobileNetV3Small 迁移学习，两阶段训练：
  Phase 1：冻结 backbone，只训练分类头
  Phase 2：解冻最后 20 层，全局 fine-tune
"""

import tensorflow as tf


def build_model(num_classes: int):
    """
    构建 MobileNetV3Small 迁移学习模型

    参数：
        num_classes: 食材类别数量

    返回：
        (model, base_model)
        - model: 完整 Keras 模型（输入 [0,255] uint8/float32，224x224x3）
        - base_model: backbone 引用，用于 Phase 2 解冻
    """
    # include_preprocessing=True：MobileNetV3 内置像素归一化，直接输入 [0,255]
    base_model = tf.keras.applications.MobileNetV3Small(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet',
        include_preprocessing=True,
    )
    base_model.trainable = False  # Phase 1：冻结 backbone

    inputs = tf.keras.Input(shape=(224, 224, 3), name='image_input')
    x = base_model(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D(name='gap')(x)
    x = tf.keras.layers.Dropout(0.2, name='dropout')(x)
    outputs = tf.keras.layers.Dense(num_classes, activation='softmax', name='predictions')(x)

    model = tf.keras.Model(inputs, outputs, name='ingredient_classifier')
    return model, base_model
