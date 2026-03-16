# 智能食谱后端 API 快速测试指南 v2.0

## 1. 快速启动

```bash
cd smart_recipe_server

# 安装依赖（首次）
uv sync

# 建库 / 迁移
uv run python manage.py migrate

# 创建超级管理员
uv run python manage.py createsuperuser

# 启动开发服务器
uv run python manage.py runserver
# → http://127.0.0.1:8000
```

## 2. 运行完整测试脚本

```bash
# 确保服务器已启动，然后：
uv run python test_api.py
```

脚本将依次测试 49 个接口（6 大模块）

## 3. 访问管理后台

```
http://127.0.0.1:8000/admin/
```

---

## 4. 统一响应格式

所有接口均返回以下 JSON 结构：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": { ... }
}
```

分页接口的 `data` 结构：

```json
{
  "count": 100,
  "next": "http://127.0.0.1:8000/api/recipe/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## 5. JWT 认证说明

- Access Token 有效期：**30 分钟**
- Refresh Token 有效期：**7 天**
- 请求头格式：`Authorization: Bearer <access_token>`
- 刷新端点（前端使用）：`POST /api/user/token/refresh/`
- 刷新端点（主路由）：`POST /api/token/refresh/`

---

## 6. 完整 API 端点速查

> 🔒 = 需要 JWT 认证

### 用户模块 `/api/user/`

| 方法   | 路径                 | 认证 | 说明                                                         |
| ------ | -------------------- | ---- | ------------------------------------------------------------ |
| POST   | `/register/`         |      | 注册（username, password, password_confirm, nickname）       |
| POST   | `/login/`            |      | 密码登录 或 手机验证码登录（login_type=phone_code）          |
| POST   | `/logout/`           | 🔒   | 退出登录                                                     |
| POST   | `/send-code/`        |      | 发送手机验证码（phone）；开发环境返回 data.code              |
| GET    | `/profile/`          | 🔒   | 获取当前用户档案                                             |
| PATCH  | `/profile/`          | 🔒   | 更新用户档案（nickname, avatar, gender, age 等）             |
| GET    | `/health-profile/`   | 🔒   | 获取健康档案                                                 |
| POST   | `/health-profile/`   | 🔒   | 更新健康档案（health_goal, daily_calories_target 等）        |
| POST   | `/change-password/`  | 🔒   | 修改密码（old_password, new_password, new_password_confirm） |
| POST   | `/<user_id>/follow/` | 🔒   | 关注用户                                                     |
| DELETE | `/<user_id>/follow/` | 🔒   | 取消关注                                                     |
| GET    | `/following/`        | 🔒   | 我的关注列表                                                 |
| GET    | `/<user_id>/`        |      | 他人公开档案                                                 |
| POST   | `/token/refresh/`    |      | Token 刷新（refresh）                                        |

### 食材模块 `/api/ingredient/`

| 方法 | 路径                    | 认证 | 说明                                                   |
| ---- | ----------------------- | ---- | ------------------------------------------------------ |
| GET  | `/`                     |      | 食材列表（分页）                                       |
| GET  | `/<id>/`                |      | 食材详情                                               |
| GET  | `/search/?q=关键词`     |      | 搜索食材                                               |
| GET  | `/seasonal/?month=N`    |      | 应季食材（month 可选，默认当月）                       |
| POST | `/recognize/`           | 🔒   | AI 食材图像识别（image_url）                           |
| GET  | `/history/`             | 🔒   | 我的识别历史                                           |
| POST | `/nutrition-calculate/` |      | 营养计算（ingredient_id, quantity_grams）              |
| POST | `/recommend/`           |      | 基于食材列表推荐食谱（ingredients: ["西红柿","鸡蛋"]） |

### 食谱模块 `/api/recipe/`

| 方法   | 路径                | 认证 | 说明                                                                          |
| ------ | ------------------- | ---- | ----------------------------------------------------------------------------- |
| GET    | `/`                 |      | 食谱列表（支持 category/difficulty/cuisine_type/search/author/ordering 过滤） |
| POST   | `/create/`          | 🔒   | 创建食谱                                                                      |
| GET    | `/<id>/`            |      | 食谱详情（自动记录浏览行为）                                                  |
| PATCH  | `/<id>/update/`     | 🔒   | 更新食谱                                                                      |
| DELETE | `/<id>/delete/`     | 🔒   | 删除食谱                                                                      |
| POST   | `/<id>/like/`       | 🔒   | 点赞 / 取消点赞（切换）                                                       |
| POST   | `/<id>/favorite/`   | 🔒   | 收藏 / 取消收藏（切换）                                                       |
| GET    | `/favorites/`       | 🔒   | 我的收藏列表                                                                  |
| GET    | `/liked/`           | 🔒   | 我点过赞的食谱                                                                |
| GET    | `/my-recipes/`      | 🔒   | 我创建的食谱                                                                  |
| GET    | `/search/?q=关键词` |      | 搜索食谱                                                                      |
| GET    | `/recommend/`       |      | 个性化推荐（登录用户按行为加权；未登录按热门）                                |
| GET    | `/hot/?limit=10`    |      | 热门食谱                                                                      |
| GET    | `/history/`         | 🔒   | 浏览历史（去重，按最近浏览排序）                                              |

### 购物清单模块 `/api/shopping-list/`

| 方法   | 路径                         | 认证 | 说明                                                  |
| ------ | ---------------------------- | ---- | ----------------------------------------------------- |
| GET    | `/`                          | 🔒   | 获取我的购物清单（?only_unpurchased=true 只看未购）   |
| POST   | `/`                          | 🔒   | 添加购物项（ingredient_id, quantity, unit）           |
| PATCH  | `/<id>/`                     | 🔒   | 更新购物项（is_purchased, quantity 等）               |
| DELETE | `/<id>/`                     | 🔒   | 删除购物项                                            |
| POST   | `/generate/`                 | 🔒   | 从食谱生成购物清单（recipe_id）                       |
| POST   | `/share/`                    | 🔒   | 创建分享链接（permission: read/edit, days: 1/3/7/30） |
| DELETE | `/share/<token>/`            | 🔒   | 撤销分享                                              |
| GET    | `/shared/<token>/`           |      | 查看分享的购物清单（无需登录）                        |
| PATCH  | `/shared/<token>/<item_id>/` |      | 更新分享清单中的项（需 edit 权限）                    |

### 社区模块 `/api/community/`

| 方法   | 路径                    | 认证 | 说明                                          |
| ------ | ----------------------- | ---- | --------------------------------------------- |
| GET    | `/posts/`               |      | 动态列表（?author=user_id 过滤）              |
| POST   | `/posts/`               | 🔒   | 发布动态（content, images[], recipe_id 可选） |
| GET    | `/posts/<id>/`          |      | 动态详情                                      |
| PUT    | `/posts/<id>/update/`   | 🔒   | 更新动态                                      |
| DELETE | `/posts/<id>/delete/`   | 🔒   | 删除动态                                      |
| POST   | `/posts/<id>/like/`     | 🔒   | 点赞 / 取消点赞（切换）                       |
| GET    | `/posts/<id>/comments/` |      | 获取动态评论                                  |
| POST   | `/posts/<id>/comments/` | 🔒   | 发表评论（content）                           |
| DELETE | `/comments/<id>/`       | 🔒   | 删除评论                                      |

### 营养模块 `/api/nutrition/`

| 方法   | 路径                   | 认证 | 说明                                                              |
| ------ | ---------------------- | ---- | ----------------------------------------------------------------- |
| GET    | `/diary/`              | 🔒   | 饮食日记列表（?date=YYYY-MM-DD 按日期过滤）                       |
| POST   | `/diary/`              | 🔒   | 添加饮食记录（food_name/recipe_id, meal_type, calories, date 等） |
| DELETE | `/diary/<id>/`         | 🔒   | 删除饮食记录                                                      |
| GET    | `/report/?period=week` | 🔒   | 营养报表（period: week / month / year）                           |
| GET    | `/advice/`             | 🔒   | 个性化健康建议                                                    |
| GET    | `/recipe/<recipe_id>/` |      | 食谱营养信息                                                      |

### 其他

| 方法 | 路径                  | 认证 | 说明                                                      |
| ---- | --------------------- | ---- | --------------------------------------------------------- |
| GET  | `/api/`               |      | API 根节点（服务状态）                                    |
| POST | `/api/upload/`        | 🔒   | 上传图片（MultipartForm，字段名 `file`，返回 `data.url`） |
| POST | `/api/token/refresh/` |      | JWT Token 刷新（主路由）                                  |

---

## 7. curl 示例

### 7.1 用户注册

```bash
curl -X POST http://127.0.0.1:8000/api/user/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test@1234",
    "password_confirm": "Test@1234",
    "nickname": "测试用户"
  }'
```

### 7.2 用户登录（获取 Token）

```bash
curl -X POST http://127.0.0.1:8000/api/user/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "Test@1234"}'
```

返回示例：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {"id": 1, "username": "testuser"},
    "profile": {"nickname": "测试用户", ...}
  }
}
```

### 7.3 手机验证码登录

```bash
# 第一步：发送验证码（开发环境返回 code）
curl -X POST http://127.0.0.1:8000/api/user/send-code/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'

# 第二步：验证码登录
curl -X POST http://127.0.0.1:8000/api/user/login/ \
  -H "Content-Type: application/json" \
  -d '{"login_type": "phone_code", "phone": "13800138000", "code": "123456"}'
```

### 7.4 食谱列表（带过滤）

```bash
# 筛选中式午餐，按点赞数排序
curl "http://127.0.0.1:8000/api/recipe/?category=lunch&cuisine_type=chinese&ordering=-likes"
```

### 7.5 创建食谱（需 Token）

```bash
export TOKEN="your_access_token_here"
curl -X POST http://127.0.0.1:8000/api/recipe/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "西红柿炒鸡蛋",
    "difficulty": "easy",
    "cooking_time": 15,
    "servings": 2,
    "category": "lunch",
    "cuisine_type": "chinese",
    "description": "简单美味的家常菜",
    "tags": ["快手", "家常"],
    "total_calories": 320,
    "is_published": true
  }'
```

### 7.6 购物清单操作

```bash
# 添加购物项
curl -X POST http://127.0.0.1:8000/api/shopping-list/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ingredient_id": 1, "quantity": "2", "unit": "个"}'

# 从食谱生成购物清单
curl -X POST http://127.0.0.1:8000/api/shopping-list/generate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recipe_id": 1}'

# 创建分享链接（7天有效期，只读）
curl -X POST http://127.0.0.1:8000/api/shopping-list/share/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permission": "read", "days": 7}'
```

### 7.7 社区动态

```bash
# 发布动态
curl -X POST http://127.0.0.1:8000/api/community/posts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "今天做了西红柿炒蛋，超好吃！", "images": []}'

# 发表评论
curl -X POST http://127.0.0.1:8000/api/community/posts/1/comments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "看起来很美味！"}'
```

### 7.8 营养追踪

```bash
# 添加饮食日记
curl -X POST http://127.0.0.1:8000/api/nutrition/diary/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "food_name": "西红柿炒蛋",
    "meal_type": "lunch",
    "calories": 320,
    "protein": 15.5,
    "fat": 12.0,
    "carbohydrate": 28.0,
    "date": "2026-03-15"
  }'

# 查看营养周报
curl "http://127.0.0.1:8000/api/nutrition/report/?period=week" \
  -H "Authorization: Bearer $TOKEN"
```

### 7.9 个性化推荐

```bash
# 未登录：按热门度推荐
curl http://127.0.0.1:8000/api/recipe/recommend/

# 已登录：按用户行为加权推荐
curl http://127.0.0.1:8000/api/recipe/recommend/ \
  -H "Authorization: Bearer $TOKEN"
```

### 7.10 上传图片

```bash
curl -X POST http://127.0.0.1:8000/api/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"
# 返回：{"code": 200, "data": {"url": "http://127.0.0.1:8000/media/uploads/xxx.jpg"}}
```

---

## 8. 项目结构

```
smart_recipe_server/
├── apps/
│   ├── user/        # 用户注册/登录/档案/关注/验证码/健康档案
│   ├── ingredient/  # 食材列表/搜索/识别/推荐/营养计算
│   ├── recipe/      # 食谱 CRUD/点赞/收藏/推荐/热门/历史
│   ├── shopping/    # 购物清单/分享
│   ├── community/   # 美食动态/评论
│   └── nutrition/   # 饮食日记/营养报表/健康建议
├── common/
│   ├── response.py      # success_response / error_response
│   ├── pagination.py    # StandardResultsSetPagination
│   └── permissions.py   # IsOwnerOrReadOnly
├── smart_recipe_server/
│   ├── settings.py
│   └── urls.py
├── test_api.py          # 完整 API 测试脚本（49 个用例）
├── API_TEST_GUIDE.md    # 本文件
└── manage.py
```

---

## 9. 常用命令

```bash
# 安装依赖
uv sync

# 新建/执行迁移
uv run python manage.py makemigrations <app>
uv run python manage.py migrate

# 创建管理员
uv run python manage.py createsuperuser

# 创建权限组
uv run python manage.py create_admin_groups

# 启动服务器
uv run python manage.py runserver

# 指定端口
uv run python manage.py runserver 8001

# 运行 API 测试
uv run python test_api.py

# 进入 Django Shell
uv run python manage.py shell
```

---

## 10. 切换到 PostgreSQL（生产）

编辑 `smart_recipe_server/settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smart_recipe_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

```bash
psql -U postgres -c "CREATE DATABASE smart_recipe_db;"
uv run python manage.py migrate
```

---

## 11. 故障排除

### 服务器启动失败

```bash
# 检查端口是否被占用
uv run python manage.py runserver 8001

# 检查数据库
uv run python manage.py check
```

### JWT Token 失效（401 Unauthorized）

```bash
# 用 refresh token 刷新
curl -X POST http://127.0.0.1:8000/api/user/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

### 迁移失败

```bash
# 查看迁移状态
uv run python manage.py showmigrations

# 指定 app 迁移
uv run python manage.py migrate ingredient
```

### 社区路由说明

> 注意：社区动态使用 `/api/community/posts/` 系列路由。
> 旧文档中的 `/feed/`、`/post/` 已废弃，请勿使用。

---

**后端版本：** Django 5.2.4 + DRF 3.16.0 | **测试脚本：** test_api.py v2.0（49 用例）
