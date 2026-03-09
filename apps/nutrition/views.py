"""
营养分析模块视图

视图：
    - DietaryLogView: 获取/添加饮食记录
    - DietaryLogDeleteView: 删除饮食记录
    - NutritionReportView: 营养统计报表
    - NutritionAdviceView: 健康建议（多维度算法）
    - RecipeNutritionView: 单个食谱营养详情
"""

from datetime import date, timedelta

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum

from common.response import success_response, error_response
from .models import DietaryLog
from .serializers import DietaryLogSerializer


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _calc_recipe_nutrition(recipe_id: int) -> dict:
    """
    通过 RecipeIngredient 按实际用量计算食谱营养总量。
    返回 {'calories', 'protein', 'fat', 'carbohydrate', 'fiber'}，均为 float。
    """
    from apps.recipe.models import RecipeIngredient
    ris = RecipeIngredient.objects.filter(recipe_id=recipe_id).select_related('ingredient')
    totals = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0,
              'carbohydrate': 0.0, 'fiber': 0.0}
    for ri in ris:
        ing = ri.ingredient
        factor = float(ri.quantity) / 100
        for k in totals:
            totals[k] += float(getattr(ing, k) or 0) * factor
    return {k: round(v, 1) for k, v in totals.items()}


# ---------------------------------------------------------------------------
# 视图
# ---------------------------------------------------------------------------

class DietaryLogView(APIView):
    """
    饮食日记视图

    GET:  获取指定日期的饮食记录和当日汇总
    POST: 添加饮食记录（recipe_id 或 custom_name + 营养数据）
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get('date', str(date.today()))
        try:
            log_date = date.fromisoformat(date_str)
        except ValueError:
            return error_response(message='日期格式错误，应为 YYYY-MM-DD', code=400)

        logs = DietaryLog.objects.filter(user=request.user, date=log_date)
        serializer = DietaryLogSerializer(logs, many=True)

        # 按餐次分组
        meal_groups = {}
        for log in serializer.data:
            meal = log['meal_type']
            if meal not in meal_groups:
                meal_groups[meal] = []
            meal_groups[meal].append(log)

        # 当日汇总（含 fiber）
        agg = logs.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_fat=Sum('fat'),
            total_carbohydrate=Sum('carbohydrate'),
            total_fiber=Sum('fiber'),
        )

        # 用户目标卡路里
        profile = getattr(request.user, 'userprofile', None)
        daily_target = profile.daily_calories_target if profile else None

        return success_response(data={
            'date': date_str,
            'logs': serializer.data,
            'meal_groups': meal_groups,
            'summary': {
                'calories': float(agg['total_calories'] or 0),
                'protein': float(agg['total_protein'] or 0),
                'fat': float(agg['total_fat'] or 0),
                'carbohydrate': float(agg['total_carbohydrate'] or 0),
                'fiber': float(agg['total_fiber'] or 0),
            },
            'daily_target': daily_target,
        })

    def post(self, request):
        data = request.data.copy()

        # 若传入 recipe_id，自动填充营养数据（修复：使用正确关联名 + 按量换算）
        recipe_id = data.get('recipe')
        if recipe_id:
            try:
                totals = _calc_recipe_nutrition(int(recipe_id))
                for k, v in totals.items():
                    if not data.get(k) or float(data.get(k, 0)) == 0:
                        data[k] = v
            except Exception:
                pass

        # 若未传 date，默认今天
        if not data.get('date'):
            data['date'] = str(date.today())

        serializer = DietaryLogSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message='记录添加成功')
        return error_response(message='数据验证失败', data=serializer.errors, code=400)


class DietaryLogDeleteView(APIView):
    """删除/编辑饮食记录"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            log = DietaryLog.objects.get(id=pk, user=request.user)
            log.delete()
            return success_response(message='记录已删除')
        except DietaryLog.DoesNotExist:
            return error_response(message='记录不存在', code=404)

    def patch(self, request, pk):
        """编辑饮食记录（允许部分更新）"""
        try:
            log = DietaryLog.objects.get(id=pk, user=request.user)
        except DietaryLog.DoesNotExist:
            return error_response(message='记录不存在', code=404)
        serializer = DietaryLogSerializer(log, data=request.data, partial=True,
                                          context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(data=serializer.data, message='记录已更新')
        return error_response(message='数据验证失败', data=serializer.errors, code=400)


class NutritionReportView(APIView):
    """
    营养统计报表

    GET ?period=week|month
    返回按日聚合的卡路里、三大营养素、膳食纤维数据，以及三大营养素能量占比
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'week')
        today = date.today()

        if period == 'month':
            start_date = today - timedelta(days=29)
        else:
            start_date = today - timedelta(days=6)

        logs = DietaryLog.objects.filter(
            user=request.user,
            date__gte=start_date,
            date__lte=today
        )

        # 按日聚合（含 fiber）
        daily = logs.values('date').annotate(
            calories=Sum('calories'),
            protein=Sum('protein'),
            fat=Sum('fat'),
            carbohydrate=Sum('carbohydrate'),
            fiber=Sum('fiber'),
        ).order_by('date')

        # 构建完整日期序列（无记录的日期填 0）
        date_map = {str(d['date']): d for d in daily}
        result = []
        current = start_date
        while current <= today:
            key = str(current)
            if key in date_map:
                d = date_map[key]
                result.append({
                    'date': key,
                    'calories': float(d['calories'] or 0),
                    'protein': float(d['protein'] or 0),
                    'fat': float(d['fat'] or 0),
                    'carbohydrate': float(d['carbohydrate'] or 0),
                    'fiber': float(d['fiber'] or 0),
                })
            else:
                result.append({
                    'date': key,
                    'calories': 0,
                    'protein': 0,
                    'fat': 0,
                    'carbohydrate': 0,
                    'fiber': 0,
                })
            current += timedelta(days=1)

        # 统计平均值（仅有记录的天数参与计算）
        days_with_data = [r for r in result if r['calories'] > 0]
        n = len(days_with_data)
        avg = {
            'calories':     round(sum(r['calories'] for r in days_with_data) / n, 1) if n else 0,
            'protein':      round(sum(r['protein'] for r in days_with_data) / n, 1) if n else 0,
            'fat':          round(sum(r['fat'] for r in days_with_data) / n, 1) if n else 0,
            'carbohydrate': round(sum(r['carbohydrate'] for r in days_with_data) / n, 1) if n else 0,
            'fiber':        round(sum(r['fiber'] for r in days_with_data) / n, 1) if n else 0,
        }

        # 三大营养素能量占比（蛋白质×4, 脂肪×9, 碳水×4）
        cal = avg['calories']
        if cal > 0:
            macro_ratio = {
                'protein_pct':      round(avg['protein'] * 4 / cal * 100, 1),
                'fat_pct':          round(avg['fat'] * 9 / cal * 100, 1),
                'carbohydrate_pct': round(avg['carbohydrate'] * 4 / cal * 100, 1),
            }
        else:
            macro_ratio = {'protein_pct': 0, 'fat_pct': 0, 'carbohydrate_pct': 0}

        return success_response(data={
            'period': period,
            'start_date': str(start_date),
            'end_date': str(today),
            'daily': result,
            'average': avg,
            'macro_ratio': macro_ratio,
        })


class NutritionAdviceView(APIView):
    """
    健康建议视图（多维度算法）

    分析维度：
    1. 热量摄入 vs 目标
    2. 三大营养素能量占比
    3. 膳食纤维摄入
    4. 餐次热量分布
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()
        week_ago = today - timedelta(days=6)

        logs = DietaryLog.objects.filter(
            user=request.user,
            date__gte=week_ago,
            date__lte=today
        )

        # 基础聚合
        agg = logs.aggregate(
            total_cal=Sum('calories'),
            total_protein=Sum('protein'),
            total_fat=Sum('fat'),
            total_carbohydrate=Sum('carbohydrate'),
            total_fiber=Sum('fiber'),
        )
        total_cal = float(agg['total_cal'] or 0)
        total_protein = float(agg['total_protein'] or 0)
        total_fat = float(agg['total_fat'] or 0)
        total_carbs = float(agg['total_carbohydrate'] or 0)
        total_fiber = float(agg['total_fiber'] or 0)

        days_logged = logs.values('date').distinct().count()
        avg_cal = round(total_cal / days_logged, 1) if days_logged > 0 else 0
        avg_protein = round(total_protein / days_logged, 1) if days_logged > 0 else 0
        avg_fat = round(total_fat / days_logged, 1) if days_logged > 0 else 0
        avg_carbs = round(total_carbs / days_logged, 1) if days_logged > 0 else 0
        avg_fiber = round(total_fiber / days_logged, 1) if days_logged > 0 else 0

        profile = getattr(request.user, 'userprofile', None)
        target = profile.daily_calories_target if profile else None
        health_goal = profile.health_goal if profile else None

        advice = []

        # ------------------------------------------------------------------
        # 无记录时的提示
        # ------------------------------------------------------------------
        if days_logged == 0:
            advice.append('还没有记录饮食，开始记录来追踪您的营养摄入吧！')
            return success_response(data={
                'days_logged': 0,
                'avg_calories': 0,
                'target_calories': target,
                'health_goal': health_goal,
                'macro_ratio': {'protein_pct': 0, 'fat_pct': 0, 'carbohydrate_pct': 0},
                'avg_fiber': 0,
                'meal_distribution': {},
                'advice': advice,
            })

        # ------------------------------------------------------------------
        # 1. 热量摄入对比
        # ------------------------------------------------------------------
        if target:
            diff = avg_cal - target
            if abs(diff) <= 100:
                advice.append(
                    f'热量摄入：本周平均 {avg_cal} 千卡/天，非常接近目标 {target} 千卡，保持得很好！'
                )
            elif diff > 100:
                advice.append(
                    f'热量摄入：本周平均 {avg_cal} 千卡/天，超出目标 {target} 千卡约 {round(diff)} 千卡，'
                    f'建议适当控制饮食量。'
                )
            else:
                advice.append(
                    f'热量摄入：本周平均 {avg_cal} 千卡/天，低于目标 {target} 千卡约 {round(-diff)} 千卡，'
                    f'注意保证充足的能量摄入。'
                )
        else:
            advice.append(
                f'热量摄入：本周平均每日摄入 {avg_cal} 千卡。'
                f'建议在个人资料中设置每日卡路里目标以获得更精准的建议。'
            )

        # ------------------------------------------------------------------
        # 2. 三大营养素能量占比分析
        # ------------------------------------------------------------------
        macro_ratio = {'protein_pct': 0, 'fat_pct': 0, 'carbohydrate_pct': 0}
        if avg_cal > 0:
            p_pct = round(avg_protein * 4 / avg_cal * 100, 1)
            f_pct = round(avg_fat * 9 / avg_cal * 100, 1)
            c_pct = round(avg_carbs * 4 / avg_cal * 100, 1)
            macro_ratio = {
                'protein_pct': p_pct,
                'fat_pct': f_pct,
                'carbohydrate_pct': c_pct,
            }

            # 蛋白质：参考范围 15–20%
            if p_pct < 15:
                advice.append(
                    f'蛋白质摄入偏低（占总热量 {p_pct}%，参考值 15–20%），'
                    f'建议增加鸡蛋、豆制品、瘦肉等富含蛋白质的食物。'
                )
            elif p_pct > 25:
                advice.append(
                    f'蛋白质摄入偏高（占总热量 {p_pct}%，参考值 15–20%），'
                    f'长期高蛋白饮食可能增加肾脏负担，注意均衡饮食。'
                )

            # 脂肪：参考范围 25–35%
            if f_pct > 35:
                advice.append(
                    f'脂肪摄入偏高（占总热量 {f_pct}%，参考值 25–35%），'
                    f'建议减少油炸食品和高脂肪食物的摄入。'
                )
            elif f_pct < 20:
                advice.append(
                    f'脂肪摄入偏低（占总热量 {f_pct}%，参考值 25–35%），'
                    f'适量健康脂肪有助于脂溶性维生素的吸收。'
                )

            # 碳水化合物：参考范围 50–60%
            if c_pct > 65:
                advice.append(
                    f'碳水化合物比例偏高（占总热量 {c_pct}%，参考值 50–60%），'
                    f'建议适量减少精制糖和白米面，增加粗粮和蔬菜。'
                )
            elif c_pct < 45:
                advice.append(
                    f'碳水化合物摄入偏低（占总热量 {c_pct}%，参考值 50–60%），'
                    f'碳水化合物是主要能量来源，过低可能影响精力和运动表现。'
                )

        # ------------------------------------------------------------------
        # 3. 膳食纤维分析（参考值：25g/天）
        # ------------------------------------------------------------------
        if avg_fiber < 15:
            advice.append(
                f'膳食纤维摄入不足（平均 {avg_fiber} g/天，建议 ≥ 25g/天），'
                f'建议多吃蔬菜、水果、豆类和全谷物。'
            )
        elif avg_fiber >= 25:
            advice.append(f'膳食纤维摄入充足（平均 {avg_fiber} g/天），有助于消化健康！')

        # ------------------------------------------------------------------
        # 4. 餐次热量分布分析
        # ------------------------------------------------------------------
        meal_agg = (
            logs.values('meal_type')
            .annotate(meal_cal=Sum('calories'))
        )
        meal_totals = {m['meal_type']: float(m['meal_cal'] or 0) for m in meal_agg}
        total_meal_cal = sum(meal_totals.values())

        meal_distribution = {}
        if total_meal_cal > 0:
            meal_distribution = {
                mt: round(cal / total_meal_cal * 100, 1)
                for mt, cal in meal_totals.items()
            }
            breakfast_pct = meal_distribution.get('breakfast', 0)
            dinner_pct = meal_distribution.get('dinner', 0)

            if breakfast_pct < 20:
                advice.append(
                    f'早餐热量比例偏低（{breakfast_pct}%，建议 25–30%），'
                    f'充足的早餐有助于维持全天精力和代谢。'
                )
            if dinner_pct > 45:
                advice.append(
                    f'晚餐热量比例偏高（{dinner_pct}%，建议 ≤ 35%），'
                    f'建议将更多热量分配到早午餐，减少晚餐比重。'
                )

        # ------------------------------------------------------------------
        # 5. 健康目标专项建议
        # ------------------------------------------------------------------
        if health_goal == 'lose_weight':
            advice.append('减肥提示：多选择低卡高纤维食谱，减少精制糖和油炸食物，适当增加有氧运动。')
        elif health_goal == 'gain_muscle':
            advice.append(
                '增肌提示：保证充足蛋白质摄入（建议每千克体重 1.5–2g），'
                '训练后 30 分钟内补充蛋白质效果更佳。'
            )
        elif health_goal == 'maintain':
            advice.append('保持健康提示：注意饮食规律，控制总热量，保持适量运动。')
        elif health_goal == 'improve_nutrition':
            advice.append('改善营养提示：注意饮食多样化，确保每日摄入充足的蔬菜、蛋白质和健康脂肪。')

        return success_response(data={
            'days_logged': days_logged,
            'avg_calories': avg_cal,
            'target_calories': target,
            'health_goal': health_goal,
            'macro_ratio': macro_ratio,
            'avg_fiber': avg_fiber,
            'meal_distribution': meal_distribution,
            'advice': advice,
        })


class RecipeNutritionView(APIView):
    """获取单个食谱的营养信息（按食材实际用量换算）"""
    permission_classes = [AllowAny]

    def get(self, request, recipe_id):
        from apps.recipe.models import Recipe, RecipeIngredient
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        servings = max(recipe.servings or 1, 1)
        ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related('ingredient')

        ingredient_list = []
        total = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0,
                 'carbohydrate': 0.0, 'fiber': 0.0}

        for ri in ingredients:
            if not ri.ingredient:
                continue
            ing = ri.ingredient
            factor = float(ri.quantity) / 100  # 换算因子（量 / 100g）
            item = {
                'name': ing.name,
                'quantity': float(ri.quantity),
                'unit': ri.unit,
                'calories':     round(float(ing.calories or 0) * factor, 1),
                'protein':      round(float(ing.protein or 0) * factor, 1),
                'fat':          round(float(ing.fat or 0) * factor, 1),
                'carbohydrate': round(float(ing.carbohydrate or 0) * factor, 1),
                'fiber':        round(float(ing.fiber or 0) * factor, 1),
            }
            ingredient_list.append(item)
            for k in total:
                total[k] += item[k]

        total = {k: round(v, 1) for k, v in total.items()}
        per_serving = {k: round(v / servings, 1) for k, v in total.items()}

        return success_response(data={
            'recipe_id': recipe.id,
            'recipe_name': recipe.name,
            'servings': servings,
            'total': total,
            'per_serving': per_serving,
            'ingredients': ingredient_list,
        })
