# 智能食谱后端 API 快速测试指南

## 1. 启动服务器

```bash
cd smart_recipe_server
uv run python manage.py runserver
```

服务器将在 http://127.0.0.1:8000 启动

## 2. 访问管理后台

### 创建超级用户
```bash
uv run python manage.py createsuperuser
```

### 登录后台
访问：http://127.0.0.1:8000/admin/

## 3. API 接口测试（使用 Postman 或 curl）

### 3.1 用户注册
```bash
curl -X POST http://127.0.0.1:8000/api/user/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "123456",
    "password_confirm": "123456",
    "nickname": "测试用户"
  }'
```

### 3.2 用户登录
```bash
curl -X POST http://127.0.0.1:8000/api/user/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "123456"
  }'
```

返回示例：
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {...},
    "profile": {...}
  }
}
```

### 3.3 获取食材列表
```bash
curl http://127.0.0.1:8000/api/ingredient/
```

### 3.4 获取食谱列表
```bash
curl http://127.0.0.1:8000/api/recipe/
```

### 3.5 创建食谱（需要登录）
```bash
curl -X POST http://127.0.0.1:8000/api/recipe/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "西红柿炒鸡蛋",
    "difficulty": "easy",
    "cooking_time": 15,
    "servings": 2,
    "category": "lunch",
    "cuisine_type": "chinese",
    "description": "简单美味的家常菜"
  }'
```

## 4. 主要 API 端点

### 用户模块 (/api/user/)
- POST /register - 注册
- POST /login - 登录
- GET /profile - 获取用户档案
- PUT /profile - 更新用户档案
- POST /change-password - 修改密码

### 食材模块 (/api/ingredient/)
- GET / - 食材列表
- GET /<id>/ - 食材详情
- GET /search/?q=关键词 - 搜索食材
- GET /seasonal/ - 应季食材
- POST /recognize/ - 食材识别
- POST /nutrition-calculate/ - 营养计算

### 食谱模块 (/api/recipe/)
- GET / - 食谱列表
- POST /create/ - 创建食谱
- GET /<id>/ - 食谱详情
- PUT /<id>/update/ - 更新食谱
- DELETE /<id>/delete/ - 删除食谱
- POST /<id>/like/ - 点赞/取消点赞
- POST /<id>/favorite/ - 收藏/取消收藏
- GET /favorites/ - 用户收藏列表
- GET /search/?q=关键词 - 搜索食谱
- GET /recommend/ - 推荐食谱

### 购物清单模块 (/api/shopping-list/)
- GET / - 购物清单
- POST / - 添加食材
- PUT /<id>/ - 更新购买状态
- DELETE /<id>/ - 删除食材
- POST /generate/ - 基于食谱生成清单

### 社区模块 (/api/community/)
- GET /feed/ - 动态流
- POST /post/ - 发布动态
- GET /post/<id>/ - 动态详情
- GET /comment/ - 评论列表
- POST /comment/create/ - 发表评论

## 5. 切换到 PostgreSQL（可选）

如果需要使用 PostgreSQL，编辑 settings.py:

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

然后重新迁移：
```bash
# 确保 PostgreSQL 服务已启动
# 创建数据库
psql -U postgres -c "CREATE DATABASE smart_recipe_db;"

# 执行迁移
uv run python manage.py migrate
```

## 6. 项目结构

```
smart_recipe_server/
├── apps/
│   ├── user/          # 用户模块
│   ├── ingredient/    # 食材模块
│   ├── recipe/        # 食谱模块
│   ├── shopping/      # 购物清单模块
│   └── community/     # 社区模块
├── common/            # 公共组件
│   ├── response.py    # 统一响应格式
│   ├── pagination.py  # 分页器
│   └── permissions.py # 权限控制
├── smart_recipe_server/
│   ├── settings.py    # 项目配置
│   └── urls.py        # 主路由
├── db.sqlite3         # SQLite 数据库
└── manage.py          # Django 管理脚本
```

## 7. 开发建议

1. **使用 Postman 或 Insomnia** 测试 API
2. **查看 Django Admin** 后台管理数据
3. **阅读代码注释** 了解详细实现
4. **参考计划书** 了解业务逻辑

## 8. 常用命令

```bash
# 创建迁移
uv run python manage.py makemigrations

# 执行迁移
uv run python manage.py migrate

# 创建超级用户
uv run python manage.py createsuperuser

# 启动服务器
uv run python manage.py runserver

# 进入 Django Shell
uv run python manage.py shell

# 测试配置
uv run python test_config.py
```

## 9. 故障排除

### 数据库连接失败
- 检查 PostgreSQL 服务是否启动
- 检查 .env 文件中的数据库配置
- 临时使用 SQLite 测试

### 迁移失败
- 删除 migrations 文件夹重新迁移
- 检查模型定义是否正确

### 端口被占用
```bash
uv run python manage.py runserver 8001
```

## 10. 下一步

1. ✅ 后端代码已完成
2. 🔄 测试所有 API 接口
3. 🔄 添加测试数据
4. 🔄 开发前端界面
5. 🔄 部署到生产环境

---

**祝你开发顺利！** 🚀
