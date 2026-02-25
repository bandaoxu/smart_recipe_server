"""
智能食谱 API 完整测试脚本

演示如何注册、登录、获取 Token、创建食谱的完整流程
"""
import sys
import requests
import json

# 设置输出编码为 UTF-8（Windows 兼容）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://127.0.0.1:8000"

def print_separator(title):
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def pretty_print(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

# 步骤 1：注册用户
print_separator("Step 1: Register User")
register_data = {
    "username": "testuser003",
    "password": "123456",
    "password_confirm": "123456",
    "nickname": "Test User 003"
}

try:
    response = requests.post(f"{BASE_URL}/api/user/register/", json=register_data)
    print(f"Status Code: {response.status_code}")
    pretty_print(response.json())
except Exception as e:
    print(f"[ERROR] Registration failed: {e}")
    print("User may already exist, continue to login...")

# 步骤 2：登录获取 Token
print_separator("Step 2: Login and Get Token")
login_data = {
    "username": "testuser003",
    "password": "123456"
}

try:
    response = requests.post(f"{BASE_URL}/api/user/login/", json=login_data)
    print(f"Status Code: {response.status_code}")
    login_result = response.json()
    pretty_print(login_result)

    # 提取 access token
    if response.status_code == 200:
        access_token = login_result['data']['access']
        print(f"\n[OK] Successfully got Access Token:")
        print(f"  {access_token[:50]}...")
    else:
        print("[ERROR] Login failed, cannot continue")
        exit(1)
except Exception as e:
    print(f"[ERROR] Login failed: {e}")
    exit(1)

# 步骤 3：使用 Token 创建食谱
print_separator("Step 3: Create Recipe (with Token)")
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

recipe_data = {
    "name": "Tomato and Egg Stir-Fry",
    "difficulty": "easy",
    "cooking_time": 15,
    "servings": 2,
    "category": "lunch",
    "cuisine_type": "chinese",
    "description": "Simple and delicious home-style dish",
    "tags": ["Quick", "Home-style", "Easy"],
    "total_calories": 300
}

try:
    response = requests.post(f"{BASE_URL}/api/recipe/create/", json=recipe_data, headers=headers)
    print(f"Status Code: {response.status_code}")
    pretty_print(response.json())

    if response.status_code == 200:
        recipe_id = response.json()['data']['id']
        print(f"\n[OK] Recipe created successfully! ID: {recipe_id}")
except Exception as e:
    print(f"[ERROR] Failed to create recipe: {e}")

# 步骤 4：获取食谱列表
print_separator("Step 4: Get Recipe List")
try:
    response = requests.get(f"{BASE_URL}/api/recipe/")
    print(f"Status Code: {response.status_code}")
    result = response.json()

    if response.status_code == 200:
        recipes = result['data']['results']
        print(f"\nTotal recipes: {len(recipes)}")
        for recipe in recipes:
            print(f"  - {recipe['name']} (ID: {recipe['id']})")
except Exception as e:
    print(f"[ERROR] Failed to get recipe list: {e}")

# 步骤 5：获取用户档案
print_separator("Step 5: Get User Profile (with Token)")
try:
    response = requests.get(f"{BASE_URL}/api/user/profile/", headers=headers)
    print(f"Status Code: {response.status_code}")
    pretty_print(response.json())
except Exception as e:
    print(f"[ERROR] Failed to get user profile: {e}")

print_separator("Test Completed")
print("\nTips:")
print("  - Access Token expires in: 30 minutes")
print("  - Refresh Token expires in: 7 days")
print("  - Use Refresh Token to get new Access Token")
print(f"  - Token refresh endpoint: {BASE_URL}/api/token/refresh/")
