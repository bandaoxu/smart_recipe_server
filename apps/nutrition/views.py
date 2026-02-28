"""
营养分析模块视图

视图：
    - DietaryLogView: 获取/添加饮食记录
    - DietaryLogDeleteView: 删除饮食记录
    - NutritionReportView: 营养统计报表
    - NutritionAdviceView: 健康建议
"""

from datetime import date, timedelta
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Sum
from django.db.models.functions import TruncDate

from common.response import success_response, error_response
from .models import DietaryLog
from .serializers import DietaryLogSerializer


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

        # 当日汇总
        agg = logs.aggregate(
            total_calories=Sum('calories'),
            total_protein=Sum('protein'),
            total_fat=Sum('fat'),
            total_carbohydrate=Sum('carbohydrate')
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
            },
            'daily_target': daily_target
        })

    def post(self, request):
        data = request.data.copy()

        # 若传入 recipe_id，自动填充营养数据
        recipe_id = data.get('recipe')
        if recipe_id and (not data.get('calories') or float(data.get('calories', 0)) == 0):
            try:
                from apps.recipe.models import Recipe
                recipe = Recipe.objects.get(id=recipe_id)
                if recipe.total_calories:
                    data['calories'] = recipe.total_calories
                # 尝试从食材汇总营养数据
                nutrition = recipe.ingredients.aggregate(
                    protein=Sum('ingredient__protein'),
                    fat=Sum('ingredient__fat'),
                    carbohydrate=Sum('ingredient__carbohydrate')
                )
                if not data.get('protein'):
                    data['protein'] = nutrition['protein'] or 0
                if not data.get('fat'):
                    data['fat'] = nutrition['fat'] or 0
                if not data.get('carbohydrate'):
                    data['carbohydrate'] = nutrition['carbohydrate'] or 0
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
    """删除饮食记录"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            log = DietaryLog.objects.get(id=pk, user=request.user)
            log.delete()
            return success_response(message='记录已删除')
        except DietaryLog.DoesNotExist:
            return error_response(message='记录不存在', code=404)


class NutritionReportView(APIView):
    """
    营养统计报表

    GET ?period=week|month
    返回按日聚合的卡路里和三大营养素数据
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

        # 按日聚合
        daily = logs.values('date').annotate(
            calories=Sum('calories'),
            protein=Sum('protein'),
            fat=Sum('fat'),
            carbohydrate=Sum('carbohydrate')
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
                })
            else:
                result.append({
                    'date': key,
                    'calories': 0,
                    'protein': 0,
                    'fat': 0,
                    'carbohydrate': 0,
                })
            current += timedelta(days=1)

        # 统计平均值
        days_with_data = [r for r in result if r['calories'] > 0]
        n = len(days_with_data)
        avg = {
            'calories': round(sum(r['calories'] for r in days_with_data) / n, 1) if n else 0,
            'protein': round(sum(r['protein'] for r in days_with_data) / n, 1) if n else 0,
            'fat': round(sum(r['fat'] for r in days_with_data) / n, 1) if n else 0,
            'carbohydrate': round(sum(r['carbohydrate'] for r in days_with_data) / n, 1) if n else 0,
        }

        return success_response(data={
            'period': period,
            'start_date': str(start_date),
            'end_date': str(today),
            'daily': result,
            'average': avg
        })


class NutritionAdviceView(APIView):
    """
    健康建议视图

    GET: 对比用户 daily_calories_target 与近 7 天平均摄入，给出文字建议
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

        agg = logs.aggregate(total_cal=Sum('calories'))
        total_cal = float(agg['total_cal'] or 0)

        # 计算有记录的天数
        days_logged = logs.values('date').distinct().count()
        avg_cal = round(total_cal / days_logged, 1) if days_logged > 0 else 0

        profile = getattr(request.user, 'userprofile', None)
        target = profile.daily_calories_target if profile else None
        health_goal = profile.health_goal if profile else None

        advice = []

        if days_logged == 0:
            advice.append('还没有记录饮食，开始记录来追踪您的营养摄入吧！')
        else:
            if target:
                diff = avg_cal - target
                if abs(diff) <= 100:
                    advice.append(f'本周平均每日摄入 {avg_cal} 千卡，非常接近您的目标 {target} 千卡，保持得很好！')
                elif diff > 100:
                    advice.append(f'本周平均每日摄入 {avg_cal} 千卡，超出目标 {target} 千卡约 {round(diff)} 千卡，建议适当控制饮食量。')
                else:
                    advice.append(f'本周平均每日摄入 {avg_cal} 千卡，低于目标 {target} 千卡约 {round(-diff)} 千卡，注意保证充足的能量摄入。')
            else:
                advice.append(f'本周平均每日摄入 {avg_cal} 千卡。建议在个人资料中设置每日卡路里目标以获得更精准的建议。')

            # 根据健康目标
            if health_goal == 'lose_weight':
                advice.append('减肥建议：多选择低卡高纤维食谱，减少油炸和高糖食物。')
            elif health_goal == 'gain_muscle':
                advice.append('增肌建议：保证充足的蛋白质摄入，每千克体重建议摄入 1.5-2g 蛋白质。')
            elif health_goal == 'improve_nutrition':
                advice.append('改善营养建议：注意饮食多样化，确保每日摄入充足的蔬菜、蛋白质和健康脂肪。')

        return success_response(data={
            'days_logged': days_logged,
            'avg_calories': avg_cal,
            'target_calories': target,
            'health_goal': health_goal,
            'advice': advice
        })


class RecipeNutritionView(APIView):
    """获取单个食谱的营养信息"""
    permission_classes = [AllowAny]

    def get(self, request, recipe_id):
        from apps.recipe.models import Recipe, RecipeIngredient
        try:
            recipe = Recipe.objects.get(id=recipe_id, is_published=True)
        except Recipe.DoesNotExist:
            return error_response(message='食谱不存在', code=404)

        ingredients = RecipeIngredient.objects.filter(recipe=recipe).select_related('ingredient')
        ingredient_list = [
            {
                'name': ri.ingredient.name,
                'quantity': ri.quantity,
                'unit': ri.unit,
                'calories': float(ri.ingredient.calories or 0),
                'protein': float(ri.ingredient.protein or 0),
                'fat': float(ri.ingredient.fat or 0),
                'carbohydrate': float(ri.ingredient.carbohydrate or 0),
            }
            for ri in ingredients if ri.ingredient
        ]
        servings = max(recipe.servings or 1, 1)
        total_cal = float(recipe.total_calories or 0)
        data = {
            'recipe_id': recipe.id,
            'recipe_name': recipe.name,
            'servings': servings,
            'total_calories': total_cal,
            'per_serving_calories': round(total_cal / servings, 1),
            'ingredients': ingredient_list,
        }
        return success_response(data=data)
