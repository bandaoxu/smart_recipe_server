"""
营养分析模块路由
"""

from django.urls import path
from .views import DietaryLogView, DietaryLogDeleteView, NutritionReportView, NutritionAdviceView, RecipeNutritionView

app_name = 'nutrition'

urlpatterns = [
    path('diary/', DietaryLogView.as_view(), name='diary'),
    path('diary/<int:pk>/', DietaryLogDeleteView.as_view(), name='diary-delete'),
    path('report/', NutritionReportView.as_view(), name='report'),
    path('advice/', NutritionAdviceView.as_view(), name='advice'),
    path('recipe/<int:recipe_id>/', RecipeNutritionView.as_view(), name='recipe-nutrition'),
]
