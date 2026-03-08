"""
食谱推荐算法模块

包含四种推荐策略：
1. CollaborativeFilter  — 用户行为相似度（协同过滤）
2. ContentBasedFilter   — 食谱特征向量匹配（内容推荐）
3. score_health_goal    — 健康目标规则加分
4. NCFRecommender       — Neural Collaborative Filtering（深度学习，训练前降级）
5. HybridRecommender    — 混合入口，加权融合以上策略
"""

import json
import math
import os
import threading

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

BEHAVIOR_WEIGHTS = {'cook': 4, 'favorite': 3, 'like': 2, 'view': 1}

# NCF 模型文件路径
_HERE = os.path.dirname(os.path.abspath(__file__))
NCF_MODEL_PATH = os.path.join(_HERE, 'saved_models', 'ncf_model.keras')
NCF_MAPPINGS_PATH = os.path.join(_HERE, 'saved_models', 'ncf_mappings.json')


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """计算两个稀疏向量（recipe_id → score）的余弦相似度"""
    common_keys = set(vec_a) & set(vec_b)
    if not common_keys:
        return 0.0
    dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _normalize(scores: dict) -> dict:
    """将分值字典归一化到 [0, 1]"""
    if not scores:
        return {}
    max_val = max(scores.values())
    if max_val == 0:
        return {k: 0.0 for k in scores}
    return {k: v / max_val for k, v in scores.items()}


def _get_recipe_nutrition(recipe) -> dict:
    """
    从 prefetch 好的 recipe_ingredients 计算营养信息。
    返回 {'calories': float, 'protein': float, 'fat': float, 'carbohydrate': float}
    """
    cache_key = '__rec_nutrition'
    if hasattr(recipe, cache_key):
        return getattr(recipe, cache_key)
    totals = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carbohydrate': 0.0}
    for ri in recipe.recipe_ingredients.all():
        ing = ri.ingredient
        factor = float(ri.quantity) / 100
        totals['calories'] += float(ing.calories or 0) * factor
        totals['protein'] += float(ing.protein or 0) * factor
        totals['fat'] += float(ing.fat or 0) * factor
        totals['carbohydrate'] += float(ing.carbohydrate or 0) * factor
    result = {k: round(v, 1) for k, v in totals.items()}
    setattr(recipe, cache_key, result)
    return result


# ---------------------------------------------------------------------------
# 1. 协同过滤
# ---------------------------------------------------------------------------

class CollaborativeFilter:
    """
    基于用户行为的用户协同过滤（User-based CF）。

    - 行为权重：cook=4, favorite=3, like=2, view=1
    - 冷启动：行为数 < 5 时返回空结果
    - 邻居上限：取最多 200 名活跃用户中前 20 名相似者
    - SQLite 兼容：全部 Python 计算，不依赖数据库侧向量运算
    """

    COLD_START_THRESHOLD = 5
    MAX_ACTIVE_USERS = 200
    TOP_K_NEIGHBORS = 20

    def get_user_vector(self, user_id: int) -> dict:
        """返回 {recipe_id: weighted_score} 字典（最近 200 条行为聚合）"""
        from .models import UserBehavior
        behaviors = (
            UserBehavior.objects
            .filter(user_id=user_id)
            .order_by('-created_at')
            .values('recipe_id', 'behavior_type')[:200]
        )
        vec = {}
        for b in behaviors:
            rid = b['recipe_id']
            w = BEHAVIOR_WEIGHTS.get(b['behavior_type'], 1)
            vec[rid] = vec.get(rid, 0) + w
        return vec

    def _load_active_users(self, exclude_user_id: int) -> list:
        """
        加载活跃用户列表（行为数 ≥ 3），排除目标用户。
        返回 [(user_id, {recipe_id: score}), ...]
        """
        from .models import UserBehavior
        from django.db.models import Count

        active_ids = (
            UserBehavior.objects
            .exclude(user_id=exclude_user_id)
            .values('user_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gte=3)
            .order_by('-cnt')
            .values_list('user_id', flat=True)[:self.MAX_ACTIVE_USERS]
        )

        result = []
        for uid in active_ids:
            vec = self.get_user_vector(uid)
            if vec:
                result.append((uid, vec))
        return result

    def get_recommendations(self, user_id: int, exclude_recipe_ids: set,
                            limit: int = 30) -> dict:
        """
        返回 {recipe_id: cf_score} 字典。
        若冷启动则返回空字典。
        """
        target_vec = self.get_user_vector(user_id)
        if len(target_vec) < self.COLD_START_THRESHOLD:
            return {}

        active_users = self._load_active_users(user_id)
        if not active_users:
            return {}

        # 计算相似度，取 top-K 邻居
        similarities = [
            (uid, _cosine_similarity(target_vec, vec), vec)
            for uid, vec in active_users
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        neighbors = similarities[:self.TOP_K_NEIGHBORS]

        # 按邻居加权聚合推荐分
        rec_scores = {}
        for _uid, sim, vec in neighbors:
            if sim <= 0:
                continue
            for rid, score in vec.items():
                if rid in exclude_recipe_ids or rid in target_vec:
                    continue
                rec_scores[rid] = rec_scores.get(rid, 0) + sim * score

        # 按分数排序，返回前 limit 条
        sorted_recs = sorted(rec_scores.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_recs[:limit])


# ---------------------------------------------------------------------------
# 2. 内容推荐
# ---------------------------------------------------------------------------

class ContentBasedFilter:
    """
    基于食谱特征向量的内容推荐（Content-Based Filtering）。

    食谱特征：tags + category + cuisine_type + difficulty
    用户偏好：dietary_preference + 历史交互食谱的特征（like/favorite/cook 加权）
    相似度：Jaccard 相似度
    """

    def get_recipe_features(self, recipe) -> set:
        """提取食谱特征集合"""
        features = set()
        if recipe.tags:
            features.update(recipe.tags)
        if recipe.category:
            features.add(f'cat:{recipe.category}')
        if recipe.cuisine_type:
            features.add(f'cuisine:{recipe.cuisine_type}')
        if recipe.difficulty:
            features.add(f'diff:{recipe.difficulty}')
        return features

    def get_user_preference(self, user, profile) -> dict:
        """
        构建用户偏好特征频次字典 {feature: weight}。
        - dietary_preference 直接偏好：权重 3
        - 历史 cook/favorite/like/view 食谱的特征：按行为权重累加
        """
        from .models import UserBehavior, Recipe

        pref_vec = {}

        # 来源 1：用户档案中的饮食偏好
        if profile and profile.dietary_preference:
            for tag in profile.dietary_preference:
                pref_vec[tag] = pref_vec.get(tag, 0) + 3

        # 来源 2：历史行为食谱的特征
        behaviors = (
            UserBehavior.objects
            .filter(user=user, behavior_type__in=['cook', 'favorite', 'like', 'view'])
            .select_related('recipe')
            .order_by('-created_at')[:100]
        )
        for b in behaviors:
            w = BEHAVIOR_WEIGHTS.get(b.behavior_type, 1)
            recipe = b.recipe
            if recipe.tags:
                for tag in recipe.tags:
                    pref_vec[tag] = pref_vec.get(tag, 0) + w
            if recipe.category:
                k = f'cat:{recipe.category}'
                pref_vec[k] = pref_vec.get(k, 0) + w
            if recipe.cuisine_type:
                k = f'cuisine:{recipe.cuisine_type}'
                pref_vec[k] = pref_vec.get(k, 0) + w

        return pref_vec

    def score_recipe(self, recipe, user_pref: dict) -> float:
        """
        计算食谱与用户偏好的相似度，返回 0–1 分值。
        使用加权 Jaccard 变体：sum(min(feat_w, pref_w)) / sum(max(feat_w, pref_w))
        """
        if not user_pref:
            return 0.0
        features = self.get_recipe_features(recipe)
        if not features:
            return 0.0

        # 将特征集合转为单位权重字典
        feat_vec = {f: 1 for f in features}

        intersection = sum(min(feat_vec.get(k, 0), user_pref.get(k, 0))
                           for k in set(feat_vec) | set(user_pref))
        union = sum(max(feat_vec.get(k, 0), user_pref.get(k, 0))
                    for k in set(feat_vec) | set(user_pref))
        return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# 3. 健康目标规则
# ---------------------------------------------------------------------------

def score_health_goal(recipe, profile) -> float:
    """
    根据用户健康目标为食谱打分，返回 0–20 分值。
    使用 prefetch 后的营养数据，安全降级（无数据时返回 0）。
    """
    if not profile or not profile.health_goal:
        return 0.0

    try:
        nutrition = _get_recipe_nutrition(recipe)
    except Exception:
        return 0.0

    servings = max(recipe.servings or 1, 1)
    cal_per_serving = nutrition['calories'] / servings
    protein_per_serving = nutrition['protein'] / servings
    fat_per_serving = nutrition['fat'] / servings

    goal = profile.health_goal
    score = 0.0

    if goal == 'lose_weight':
        if cal_per_serving < 400:
            score += 15.0
        elif cal_per_serving < 600:
            score += 7.0
        if fat_per_serving < 10:
            score += 5.0

    elif goal == 'gain_muscle':
        if protein_per_serving >= 20:
            score += 15.0
        elif protein_per_serving >= 10:
            score += 7.0
        if cal_per_serving >= 500:
            score += 5.0

    elif goal == 'maintain':
        if 300 <= cal_per_serving <= 600:
            score += 10.0

    # improve_nutrition: 无热量约束，不特别加分

    return score


# ---------------------------------------------------------------------------
# 4. 深度学习推荐（Neural Collaborative Filtering）
# ---------------------------------------------------------------------------

class NCFRecommender:
    """
    Neural Collaborative Filtering 推荐器。

    架构：GMF + MLP 混合
    - User Embedding (32) + Recipe Embedding (32)
    - 拼接 → Dense(64) → Dense(32) → Dense(1, sigmoid)
    - 输出：交互概率 0–1

    模型文件：apps/recipe/saved_models/ncf_model.keras
    映射文件：apps/recipe/saved_models/ncf_mappings.json

    未训练时（模型文件不存在）自动降级，is_available() 返回 False。
    训练命令：uv run python manage.py train_ncf [--epochs 20]
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
                    cls._instance._mappings = None
                    cls._instance._loaded = False
        return cls._instance

    def _load(self):
        """懒加载模型（线程安全）"""
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            if not os.path.exists(NCF_MODEL_PATH) or not os.path.exists(NCF_MAPPINGS_PATH):
                self._loaded = True
                return
            try:
                import tensorflow as tf
                self._model = tf.keras.models.load_model(NCF_MODEL_PATH)
                with open(NCF_MAPPINGS_PATH, 'r', encoding='utf-8') as f:
                    self._mappings = json.load(f)
            except Exception:
                self._model = None
                self._mappings = None
            self._loaded = True

    def is_available(self) -> bool:
        """检查模型是否可用"""
        self._load()
        return self._model is not None and self._mappings is not None

    def predict(self, user_id: int, recipe_ids: list) -> dict:
        """
        批量预测用户对食谱列表的交互概率。
        返回 {recipe_id: score(0–1)} 字典。
        若模型不可用则返回空字典。
        """
        if not self.is_available():
            return {}
        if not recipe_ids:
            return {}

        try:
            import numpy as np

            user_map = self._mappings.get('user_map', {})
            recipe_map = self._mappings.get('recipe_map', {})

            uid_str = str(user_id)
            if uid_str not in user_map:
                return {}

            user_idx = user_map[uid_str]

            valid_pairs = []
            for rid in recipe_ids:
                rid_str = str(rid)
                if rid_str in recipe_map:
                    valid_pairs.append((rid, recipe_map[rid_str]))

            if not valid_pairs:
                return {}

            user_arr = np.array([user_idx] * len(valid_pairs))
            recipe_arr = np.array([p[1] for p in valid_pairs])

            preds = self._model.predict(
                [user_arr, recipe_arr], batch_size=256, verbose=0
            ).flatten()

            return {valid_pairs[i][0]: float(preds[i]) for i in range(len(valid_pairs))}

        except Exception:
            return {}

    def reload(self):
        """强制重新加载模型（训练完成后调用）"""
        with self._lock:
            self._model = None
            self._mappings = None
            self._loaded = False


# 单例
ncf_recommender = NCFRecommender()


# ---------------------------------------------------------------------------
# 5. 混合推荐
# ---------------------------------------------------------------------------

class HybridRecommender:
    """
    混合推荐入口。

    策略权重（DL 可用时）：CF 0.30 + CBF 0.25 + Health 0.20 + DL 0.15 + Pop 0.10
    策略权重（DL 不可用）：CF 0.40 + CBF 0.30 + Health 0.20 + Pop 0.10
    策略权重（CF 冷启动）：CBF 0.50 + Health 0.30 + Pop 0.20
    """

    def __init__(self):
        self.cf = CollaborativeFilter()
        self.cbf = ContentBasedFilter()

    def recommend(self, user, queryset, profile=None, limit: int = 20) -> list:
        """
        主入口。

        :param user:      Django User 实例
        :param queryset:  已过滤过敏食材的 Recipe queryset（带 prefetch_related）
        :param profile:   UserProfile 实例（可为 None）
        :param limit:     返回食谱数量
        :return:          排好序的 Recipe 列表
        """

        # --- 候选池：热门度前 80 ---
        hot_candidates = list(queryset.order_by('-views', '-likes')[:80])
        candidate_map = {r.id: r for r in hot_candidates}  # recipe_id -> Recipe

        # --- CF 补充候选池 ---
        exclude_ids = set(candidate_map.keys())
        cf_scores_raw = self.cf.get_recommendations(user.id, exclude_ids, limit=30)

        if cf_scores_raw:
            # 按 CF 推荐的 recipe_id 从 DB 加载（需要在 queryset 范围内）
            cf_recipe_ids = list(cf_scores_raw.keys())
            cf_extra = list(
                queryset.filter(id__in=cf_recipe_ids).prefetch_related(
                    'recipe_ingredients__ingredient'
                )
            )
            for r in cf_extra:
                if r.id not in candidate_map:
                    candidate_map[r.id] = r
            cf_available = True
        else:
            cf_available = False

        candidates = list(candidate_map.values())
        if not candidates:
            return []

        # --- CBF 用户偏好 ---
        user_pref = self.cbf.get_user_preference(user, profile)

        # --- NCF 批量预测 ---
        candidate_ids = [r.id for r in candidates]
        dl_scores = ncf_recommender.predict(user.id, candidate_ids)
        dl_available = bool(dl_scores)

        # --- 归一化各维度分数 ---
        # Popularity
        pop_raw = {r.id: (r.views or 0) * 0.1 + (r.likes or 0) * 2 for r in candidates}
        pop_scores = _normalize(pop_raw)

        # CF（归一化已有的 cf_scores_raw + 候选池中的 0 值）
        if cf_available and cf_scores_raw:
            cf_all = {r.id: cf_scores_raw.get(r.id, 0.0) for r in candidates}
            cf_scores = _normalize(cf_all)
        else:
            cf_scores = {r.id: 0.0 for r in candidates}

        # CBF
        cbf_raw = {r.id: self.cbf.score_recipe(r, user_pref) for r in candidates}
        cbf_scores = _normalize(cbf_raw)

        # Health
        health_raw = {r.id: score_health_goal(r, profile) for r in candidates}
        health_scores = _normalize(health_raw)

        # DL
        if dl_available:
            dl_norm = _normalize(dl_scores)
        else:
            dl_norm = {}

        # --- 确定权重 ---
        if dl_available and cf_available:
            def final_score(rid):
                return (cf_scores.get(rid, 0) * 0.30
                        + cbf_scores.get(rid, 0) * 0.25
                        + health_scores.get(rid, 0) * 0.20
                        + dl_norm.get(rid, 0) * 0.15
                        + pop_scores.get(rid, 0) * 0.10)
        elif cf_available:
            def final_score(rid):
                return (cf_scores.get(rid, 0) * 0.40
                        + cbf_scores.get(rid, 0) * 0.30
                        + health_scores.get(rid, 0) * 0.20
                        + pop_scores.get(rid, 0) * 0.10)
        else:
            # 冷启动
            def final_score(rid):
                return (cbf_scores.get(rid, 0) * 0.50
                        + health_scores.get(rid, 0) * 0.30
                        + pop_scores.get(rid, 0) * 0.20)

        candidates.sort(key=lambda r: final_score(r.id), reverse=True)
        return candidates[:limit]
