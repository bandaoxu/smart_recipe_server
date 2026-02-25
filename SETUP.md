# 智能食谱后端服务 - 安装配置指南

本文档提供完整的项目安装、配置和运行步骤。

## 📋 前置要求

在开始之前，请确保您的系统已安装：

- **Python 3.13+** - [下载地址](https://www.python.org/downloads/)
- **UV 包管理器** - [安装指南](https://github.com/astral-sh/uv)
- **Git** - [下载地址](https://git-scm.com/)
- **PostgreSQL 16+** (可选，生产环境使用) - [下载地址](https://www.postgresql.org/download/)

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/bandaoxu/smart_recipe_server.git
cd smart_recipe_server
```

### 2. 安装依赖

使用 UV 包管理器安装所有项目依赖：

```bash
uv sync
```

这将自动创建虚拟环境并安装以下依赖：
- Django 5.2.4
- Django REST Framework 3.16.0
- djangorestframework-simplejwt 5.5.1
- django-cors-headers 4.9.0
- django-filter 25.2
- psycopg2-binary 2.9.10
- Pillow 12.1.1
- requests 2.32.5
- python-dotenv 1.2.1
- 其他依赖...

### 3. 配置环境变量（可选）

如果需要使用 PostgreSQL 或自定义配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接信息：

```env
# PostgreSQL 配置（生产环境）
DB_NAME=smart_recipe_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Django 配置
DEBUG=True
SECRET_KEY=your-secret-key-here
```

**注意**：开发环境默认使用 SQLite，无需配置 `.env` 文件。

### 4. 数据库迁移

执行数据库迁移，创建所有必要的数据表：

```bash
uv run python manage.py migrate
```

这将创建：
- 10 个业务数据表（用户、食材、食谱、购物清单、社区）
- 11 个 Django 内置表（认证、会话、权限等）

### 5. 创建超级用户（可选）

创建管理员账号以访问 Django Admin 后台：

```bash
uv run python manage.py createsuperuser
```

按提示输入：
- 用户名（Username）
- 邮箱（Email，可选）
- 密码（Password）

**示例**：
```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
Superuser created successfully.
```

### 6. 启动开发服务器

```bash
uv run python manage.py runserver
```

服务器将在 http://127.0.0.1:8000 启动。

### 7. 访问应用

- **API 根路径**: http://127.0.0.1:8000/api/
- **Admin 后台**: http://127.0.0.1:8000/admin/
  - 使用步骤 5 创建的超级用户登录

## 🧪 验证安装

### 测试配置

运行配置测试脚本，验证所有配置是否正确：

```bash
uv run python test_config.py
```

预期输出：
```
==================================================
[SUCCESS] Django Configuration Test Passed!
==================================================
[OK] All models imported successfully!
[OK] Database connection successful!
```

### 测试 API

运行完整的 API 测试脚本：

```bash
uv run python test_api.py
```

这将测试：
1. 用户注册
2. 用户登录（获取 JWT Token）
3. 创建食谱（使用 Token 认证）
4. 获取食谱列表
5. 获取用户档案

## 🗄️ 数据库配置

### 使用 SQLite（默认，推荐开发环境）

无需额外配置，项目默认使用 SQLite 数据库。

**优点**：
- 无需安装数据库服务
- 开箱即用
- 适合开发和测试

### 使用 PostgreSQL（生产环境）

#### 步骤 1：安装 PostgreSQL

根据您的操作系统安装 PostgreSQL：
- Windows: 下载安装包
- macOS: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

#### 步骤 2：创建数据库

```bash
# 登录 PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE smart_recipe_db;

# 退出
\q
```

#### 步骤 3：配置环境变量

编辑 `.env` 文件（参考步骤 3）。

#### 步骤 4：修改 settings.py

编辑 `smart_recipe_server/settings.py`：

```python
# 注释掉 SQLite 配置（第 93-98 行）
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# 取消 PostgreSQL 配置的注释（第 106-115 行）
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "smart_recipe_db"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "root"),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

#### 步骤 5：重新执行迁移

```bash
uv run python manage.py migrate
```

## 🔧 常用命令

### 开发服务器

```bash
# 启动服务器（默认端口 8000）
uv run python manage.py runserver

# 使用指定端口
uv run python manage.py runserver 8001

# 允许外部访问
uv run python manage.py runserver 0.0.0.0:8000
```

### 数据库管理

```bash
# 创建迁移文件
uv run python manage.py makemigrations

# 应用迁移
uv run python manage.py migrate

# 查看迁移状态
uv run python manage.py showmigrations

# 回滚迁移
uv run python manage.py migrate <app_name> <migration_name>
```

### Django Shell

```bash
# 进入 Django Shell
uv run python manage.py shell

# 示例：创建测试数据
>>> from apps.user.models import UserProfile
>>> from django.contrib.auth.models import User
>>> user = User.objects.create_user('testuser', 'test@example.com', 'password123')
>>> profile = UserProfile.objects.create(user=user, nickname='测试用户')
```

### 依赖管理

```bash
# 安装新依赖
uv add package-name

# 删除依赖
uv remove package-name

# 更新依赖
uv sync

# 查看已安装的包
uv pip list
```

## 📝 项目结构说明

```
smart_recipe_server/
├── apps/                          # 应用模块
│   ├── user/                      # 用户模块
│   ├── ingredient/                # 食材模块
│   ├── recipe/                    # 食谱模块
│   ├── shopping/                  # 购物清单模块
│   └── community/                 # 社区模块
├── common/                        # 公共组件
│   ├── response.py                # 统一响应格式
│   ├── pagination.py              # 分页器
│   └── permissions.py             # 权限控制
├── smart_recipe_server/           # 项目配置
│   ├── settings.py                # Django 配置
│   └── urls.py                    # 主路由
├── .env.example                   # 环境变量示例
├── .gitignore                     # Git 忽略文件
├── db.sqlite3                     # SQLite 数据库
├── manage.py                      # Django 管理脚本
├── pyproject.toml                 # 项目依赖配置
├── README.md                      # 项目说明
├── SETUP.md                       # 本文档
├── API_TEST_GUIDE.md              # API 测试指南
├── TROUBLESHOOTING.md             # 故障排除指南
├── test_config.py                 # 配置测试脚本
└── test_api.py                    # API 测试脚本
```

## ⚠️ 常见问题

### 1. 虚拟环境警告

```
warning: `VIRTUAL_ENV=...` does not match the project environment path `.venv`
```

**说明**：这是正常警告，UV 会自动使用项目的 `.venv`，可以忽略。

### 2. 端口被占用

```
Error: That port is already in use.
```

**解决方法**：
```bash
# 使用其他端口
uv run python manage.py runserver 8001
```

### 3. 数据库连接失败

**检查清单**：
- PostgreSQL 服务是否已启动？
- 数据库是否已创建？
- `.env` 文件中的密码是否正确？
- psycopg2-binary 是否已安装？

**解决方法**：参考 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

### 4. 迁移失败

```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**解决方法**：
```bash
# 删除数据库文件（SQLite）
rm db.sqlite3

# 重新执行迁移
uv run python manage.py migrate
```

## 📚 下一步

安装完成后，您可以：

1. **阅读 API 文档**: [API_TEST_GUIDE.md](./API_TEST_GUIDE.md)
2. **运行测试**: `uv run python test_api.py`
3. **访问 Admin 后台**: http://127.0.0.1:8000/admin/
4. **开始开发**: 参考 [CLAUDE.md](../CLAUDE.md)

## 🆘 获取帮助

如果遇到问题：
1. 查看 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. 运行 `uv run python test_config.py` 检查配置
3. 查看 Django 官方文档: https://docs.djangoproject.com/
4. 提交 GitHub Issue

---

**祝您开发顺利！** 🚀
