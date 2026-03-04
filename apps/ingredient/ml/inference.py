"""
食材识别推理服务

单例模式 + 线程锁，首次调用时懒加载模型。
若模型文件不存在，predict() 返回 None，调用方自动 fallback 到 mock。

用法：
    from apps.ingredient.ml.inference import IngredientClassifier

    classifier = IngredientClassifier()
    results = classifier.predict('http://example.com/img.jpg', top_k=5)
    # [{'name': '西红柿', 'confidence': 0.95}, ...]
    # 或 None（模型未训练）
"""

import io
import json
import logging
import os
import threading

import numpy as np
import requests
from PIL import Image

logger = logging.getLogger(__name__)

SAVED_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
MODEL_PATH = os.path.join(SAVED_DIR, "ingredient_classifier.keras")
CLASSES_PATH = os.path.join(SAVED_DIR, "classes.json")

IMG_SIZE = 224


class IngredientClassifier:
    """
    食材识别推理服务（线程安全单例）

    模型文件存在时自动加载并使用真实推理；
    模型文件不存在时 predict() 返回 None，让 views.py 降级到 mock 逻辑。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._model = None
                instance._classes = None
                instance._initialized = False
                cls._instance = instance
        return cls._instance

    def _load(self):
        """懒加载模型，只执行一次"""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:  # double-check
                return

            if os.path.exists(MODEL_PATH) and os.path.exists(CLASSES_PATH):
                try:
                    import tensorflow as tf

                    logger.info("加载食材识别模型：%s", MODEL_PATH)
                    # 使用.keras格式加载
                    try:
                        # 加载.keras格式模型
                        self._model = tf.keras.models.load_model(
                            MODEL_PATH, compile=False
                        )
                        self._infer = None
                        self._output_key = None
                    except Exception as e:
                        logger.error(f"模型加载失败: {e}")
                        self._model = None
                        self._classes = None
                        return

                    with open(CLASSES_PATH, encoding="utf-8") as f:
                        self._classes = json.load(f)

                    logger.info("模型加载成功，类别数：%d", len(self._classes))
                except Exception as e:
                    logger.error("模型加载失败：%s", e)
                    self._model = None
                    self._classes = None
            else:
                logger.info("未找到已训练模型，推理服务使用 mock 模式")

            self._initialized = True

    def is_ready(self) -> bool:
        """模型是否已加载就绪"""
        self._load()
        return self._model is not None

    def predict(self, image_url: str, top_k: int = 5) -> list | None:
        """
        对图片 URL 执行食材识别推理

        参数：
            image_url: 图片的 HTTP(S) URL
            top_k:     返回置信度最高的前 k 个食材

        返回：
            识别结果列表，如：
                [{'name': '西红柿', 'confidence': 0.95}, ...]
            若模型未训练或推理出错，返回 None
        """
        self._load()

        if self._model is None:
            return None

        try:
            # ── 1. 下载图片 ───────────────────────────────────────────────────
            resp = requests.get(image_url, timeout=10)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")

            # ── 2. 预处理（resize → numpy → batch 维度） ──────────────────────
            img = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
            arr = np.array(img, dtype=np.float32)  # (224, 224, 3)
            arr = np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)

            # ── 3. 推理 ───────────────────────────────────────────────
            # 使用.keras格式进行推理
            import tensorflow as tf

            with tf.device("/CPU:0"):
                tensor = tf.constant(arr, dtype=tf.float32)
                # 使用predict方法
                probs = self._model.predict(tensor, verbose=0)[0]

            # ── 4. 取 top-k ───────────────────────────────────────────────────
            top_k = min(top_k, len(self._classes))
            top_indices = np.argsort(probs)[::-1][:top_k]

            results = [
                {
                    "name": self._classes[idx],
                    "confidence": round(float(probs[idx]), 4),
                }
                for idx in top_indices
            ]
            return results

        except Exception as e:
            logger.error("食材推理失败：%s", e)
            return None

    def reload(self):
        """重新加载模型（训练完成后调用）"""
        with self._lock:
            self._initialized = False
            self._model = None
            self._classes = None
        self._load()
