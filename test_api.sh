#!/bin/bash
# 智能食谱 API 测试脚本

echo "================================"
echo "智能食谱 API 完整测试流程"
echo "================================"

# 1. 注册用户
echo -e "\n[步骤 1] 注册用户..."
REGISTER_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/user/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser001",
    "password": "123456",
    "password_confirm": "123456",
    "nickname": "测试用户001"
  }')
echo "注册响应: $REGISTER_RESPONSE"

# 2. 登录获取 Token
echo -e "\n[步骤 2] 登录获取 Token..."
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/user/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser001",
    "password": "123456"
  }')
echo "登录响应: $LOGIN_RESPONSE"

# 提取 access token（需要 jq 工具，如果没有安装可以手动复制）
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access":"[^"]*' | grep -o '[^"]*$')
echo -e "\n获取到的 Access Token: $ACCESS_TOKEN"

# 3. 使用 Token 创建食谱
echo -e "\n[步骤 3] 使用 Token 创建食谱..."
CREATE_RECIPE_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/recipe/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "name": "西红柿炒鸡蛋",
    "difficulty": "easy",
    "cooking_time": 15,
    "servings": 2,
    "category": "lunch",
    "cuisine_type": "chinese",
    "description": "简单美味的家常菜",
    "tags": ["快手菜", "家常菜"]
  }')
echo "创建食谱响应: $CREATE_RECIPE_RESPONSE"

# 4. 查看食谱列表
echo -e "\n[步骤 4] 查看食谱列表..."
LIST_RESPONSE=$(curl -s http://127.0.0.1:8000/api/recipe/)
echo "食谱列表: $LIST_RESPONSE"

echo -e "\n================================"
echo "测试完成！"
echo "================================"
