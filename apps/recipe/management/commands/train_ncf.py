"""
train_ncf — 训练 Neural Collaborative Filtering 推荐模型

用法：
    uv run python manage.py train_ncf
    uv run python manage.py train_ncf --epochs 30 --embedding_dim 64
    uv run python manage.py train_ncf --min_interactions 3

训练完成后，模型文件保存至：
    apps/recipe/saved_models/ncf_model.keras
    apps/recipe/saved_models/ncf_mappings.json

完成后调用 ncf_recommender.reload() 热更新推理单例。
"""

import json
import os

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train Neural Collaborative Filtering recommendation model'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=20,
                            help='训练轮数（默认 20）')
        parser.add_argument('--embedding_dim', type=int, default=32,
                            help='Embedding 维度（默认 32）')
        parser.add_argument('--min_interactions', type=int, default=2,
                            help='用户最少交互数，低于此值不参与训练（默认 2）')
        parser.add_argument('--neg_ratio', type=int, default=4,
                            help='每条正样本对应的负样本数（默认 4）')

    def handle(self, *args, **options):
        try:
            import numpy as np
            import tensorflow as tf
        except ImportError as e:
            self.stderr.write(f'缺少依赖：{e}\n请执行 uv sync 安装 tensorflow 和 numpy')
            return

        from apps.recipe.models import UserBehavior, Recipe
        from apps.recipe.recommender import NCF_MODEL_PATH, NCF_MAPPINGS_PATH, ncf_recommender
        from django.db.models import Count

        epochs = options['epochs']
        emb_dim = options['embedding_dim']
        min_inter = options['min_interactions']
        neg_ratio = options['neg_ratio']

        # ------------------------------------------------------------------
        # 1. 加载交互数据
        # ------------------------------------------------------------------
        self.stdout.write('加载用户行为数据...')

        # 只取有意义的正交互（排除 view，保留 like/favorite/cook）
        behaviors = (
            UserBehavior.objects
            .filter(behavior_type__in=['like', 'favorite', 'cook'])
            .values('user_id', 'recipe_id', 'behavior_type')
        )

        # 构建 (user_id, recipe_id) 正交互集合
        positives = set()
        for b in behaviors:
            positives.add((b['user_id'], b['recipe_id']))

        if not positives:
            self.stderr.write('没有足够的交互数据，请先让用户产生点赞/收藏/完成烹饪行为。')
            return

        # 过滤：用户交互数 >= min_interactions
        from collections import Counter
        user_counts = Counter(uid for uid, _ in positives)
        positives = [(uid, rid) for uid, rid in positives
                     if user_counts[uid] >= min_inter]

        if len(positives) < 10:
            self.stderr.write(f'有效正样本数不足（仅 {len(positives)} 条），请降低 --min_interactions 或增加更多用户行为。')
            return

        # ------------------------------------------------------------------
        # 2. 构建 ID 映射
        # ------------------------------------------------------------------
        user_ids = sorted(set(uid for uid, _ in positives))
        recipe_ids = sorted(Recipe.objects.filter(is_published=True)
                            .values_list('id', flat=True))

        user_map = {uid: idx for idx, uid in enumerate(user_ids)}
        recipe_map = {rid: idx for idx, rid in enumerate(recipe_ids)}

        self.stdout.write(
            f'用户数：{len(user_ids)}，食谱数：{len(recipe_ids)}，正样本数：{len(positives)}'
        )

        # ------------------------------------------------------------------
        # 3. 构建训练数据（正负样本）
        # ------------------------------------------------------------------
        import random
        random.seed(42)

        all_recipe_ids = set(recipe_ids)
        pos_set = set(positives)

        train_users, train_recipes, train_labels = [], [], []

        for uid, rid in positives:
            if uid not in user_map or rid not in recipe_map:
                continue
            # 正样本
            train_users.append(user_map[uid])
            train_recipes.append(recipe_map[rid])
            train_labels.append(1.0)

            # 负采样
            neg_count = 0
            attempts = 0
            while neg_count < neg_ratio and attempts < neg_ratio * 10:
                neg_rid = random.choice(recipe_ids)
                if (uid, neg_rid) not in pos_set:
                    train_users.append(user_map[uid])
                    train_recipes.append(recipe_map[neg_rid])
                    train_labels.append(0.0)
                    neg_count += 1
                attempts += 1

        train_users = np.array(train_users)
        train_recipes = np.array(train_recipes)
        train_labels = np.array(train_labels)

        self.stdout.write(f'训练样本总数：{len(train_labels)}（含负样本）')

        # ------------------------------------------------------------------
        # 4. 构建 NCF 模型
        # ------------------------------------------------------------------
        n_users = len(user_ids)
        n_recipes = len(recipe_ids)

        user_input = tf.keras.Input(shape=(1,), name='user_input')
        recipe_input = tf.keras.Input(shape=(1,), name='recipe_input')

        user_emb = tf.keras.layers.Embedding(n_users, emb_dim, name='user_emb')(user_input)
        recipe_emb = tf.keras.layers.Embedding(n_recipes, emb_dim, name='recipe_emb')(recipe_input)

        user_flat = tf.keras.layers.Flatten()(user_emb)
        recipe_flat = tf.keras.layers.Flatten()(recipe_emb)

        concat = tf.keras.layers.Concatenate()([user_flat, recipe_flat])
        x = tf.keras.layers.Dense(64, activation='relu')(concat)
        x = tf.keras.layers.Dropout(0.2)(x)
        x = tf.keras.layers.Dense(32, activation='relu')(x)
        output = tf.keras.layers.Dense(1, activation='sigmoid', name='output')(x)

        model = tf.keras.Model(inputs=[user_input, recipe_input], outputs=output)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        # ------------------------------------------------------------------
        # 5. 训练
        # ------------------------------------------------------------------
        self.stdout.write(f'开始训练，epochs={epochs}...')

        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=5, restore_best_weights=True
        )

        model.fit(
            [train_users, train_recipes],
            train_labels,
            batch_size=256,
            epochs=epochs,
            validation_split=0.1,
            callbacks=[early_stop],
            verbose=1
        )

        # ------------------------------------------------------------------
        # 6. 保存模型和映射
        # ------------------------------------------------------------------
        os.makedirs(os.path.dirname(NCF_MODEL_PATH), exist_ok=True)

        model.save(NCF_MODEL_PATH)
        mappings = {
            'user_map': {str(uid): idx for uid, idx in user_map.items()},
            'recipe_map': {str(rid): idx for rid, idx in recipe_map.items()},
        }
        with open(NCF_MAPPINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(mappings, f)

        self.stdout.write(self.style.SUCCESS(
            f'训练完成！模型已保存至 {NCF_MODEL_PATH}'
        ))

        # 热更新推理单例
        ncf_recommender.reload()
        self.stdout.write('推理模型已热更新。')
