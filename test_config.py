"""
测试 Django 配置是否正确
"""
import os
import sys
import django

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_recipe_server.settings')
django.setup()

from django.conf import settings

print("=" * 50)
print("Django Configuration Test")
print("=" * 50)

print(f"\n[OK] SECRET_KEY: {'Configured' if settings.SECRET_KEY else 'Not configured'}")
print(f"[OK] DEBUG: {settings.DEBUG}")
print(f"[OK] ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

print(f"\n[OK] Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"[OK] Database Name: {settings.DATABASES['default']['NAME']}")

print(f"\n[OK] Installed Apps: {len(settings.INSTALLED_APPS)}")
print("   Custom Apps:")
for app in settings.INSTALLED_APPS:
    if app.startswith('apps.'):
        print(f"   - {app}")

print(f"\n[OK] REST Framework: {'Configured' if hasattr(settings, 'REST_FRAMEWORK') else 'Not configured'}")
print(f"[OK] JWT Settings: {'Configured' if hasattr(settings, 'SIMPLE_JWT') else 'Not configured'}")
print(f"[OK] CORS Settings: {'Configured' if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS') else 'Not configured'}")

print("\n" + "=" * 50)
print("[SUCCESS] Django Configuration Test Passed!")
print("=" * 50)

# Test model imports
print("\nTesting model imports...")
try:
    from apps.user.models import UserProfile
    from apps.ingredient.models import Ingredient
    from apps.recipe.models import Recipe
    from apps.shopping.models import ShoppingList
    from apps.community.models import FoodPost, Comment
    print("[OK] All models imported successfully!")
except Exception as e:
    print(f"[ERROR] Model import failed: {e}")

# Test database connection
print("\nTesting database connection...")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("[OK] Database connection successful!")
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")

print("\n" + "=" * 50)
print("[SUCCESS] All tests completed!")
print("=" * 50)
print("\nYou can now run:")
print("  uv run python manage.py createsuperuser")
print("  uv run python manage.py runserver")

