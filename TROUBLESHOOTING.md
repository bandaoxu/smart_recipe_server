# 故障排除指南

## 问题：服务器无法启动

### 已解决的问题记录（2026-02-25）

#### 症状
- 运行 `uv run python manage.py runserver` 时出现错误
- 终端显示 "Exception in thread django-main-thread"
- 数据库连接失败

#### 根本原因
1. **虚拟环境不完整**：`.venv` 目录存在但缺少必要的包和工具
2. **PostgreSQL 驱动未安装**：切换到 PostgreSQL 配置后，`psycopg2-binary` 没有正确安装

#### 解决方案
```bash
# 1. 删除旧的虚拟环境
cd smart_recipe_server
rm -rf .venv

# 2. 重新创建虚拟环境
uv venv

# 3. 安装所有依赖
uv sync

# 4. 验证配置
uv run python test_config.py

# 5. 启动服务器
uv run python manage.py runserver
```

#### 验证结果
```
✅ 20 个包成功安装（包括 psycopg2-binary==2.9.10）
✅ 数据库连接成功
✅ 服务器正常启动
```

---

## 常见问题

### 1. 虚拟环境警告
**症状**：
```
warning: `VIRTUAL_ENV=E:\JavaDownload\python\Python313` does not match the project environment path `.venv`
```

**说明**：这是正常警告，表示系统检测到全局 Python 环境变量，但 UV 会自动使用项目的 `.venv`。可以忽略此警告。

**如需消除警告**（可选）：
```bash
# Windows PowerShell
$env:VIRTUAL_ENV = ""

# Windows CMD
set VIRTUAL_ENV=

# Linux/Mac
export VIRTUAL_ENV=
```

### 2. 数据库连接失败
**症状**：
```
[ERROR] Database connection failed
```

**检查清单**：
- [ ] PostgreSQL 服务是否已启动？
- [ ] 数据库 `smart_recipe_db` 是否已创建？
- [ ] `.env` 文件中的数据库密码是否正确？
- [ ] psycopg2-binary 是否已安装？

**验证步骤**：
```bash
# 检查 PostgreSQL 服务状态（Windows）
sc query postgresql-x64-16

# 测试数据库连接
uv run python test_config.py

# 检查依赖
uv pip list | grep psycopg
```

**创建数据库**（如果不存在）：
```bash
# 使用 psql 命令行
psql -U postgres -c "CREATE DATABASE smart_recipe_db;"
```

### 3. 依赖安装失败
**症状**：
```
Package(s) not found for: xxx
```

**解决方法**：
```bash
# 方法 1：重新同步依赖
uv sync --reinstall

# 方法 2：清理缓存后重新安装
rm -rf .venv
uv venv
uv sync

# 方法 3：手动安装缺少的包
uv pip install package-name
```

### 4. 端口被占用
**症状**：
```
Error: That port is already in use.
```

**解决方法**：
```bash
# Windows：查找并终止占用 8000 端口的进程
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9

# 或使用其他端口
uv run python manage.py runserver 8001
```

### 5. 迁移未应用
**症状**：
```
You have X unapplied migration(s).
```

**解决方法**：
```bash
# 应用所有迁移
uv run python manage.py migrate

# 查看迁移状态
uv run python manage.py showmigrations
```

---

## 切换数据库配置

### 切换到 SQLite（开发环境，推荐）
**优点**：无需额外配置，开箱即用

**步骤**：
1. 编辑 `smart_recipe_server/settings.py`
2. 注释掉 PostgreSQL 配置（第 106-115 行）
3. 取消 SQLite 配置的注释（第 93-98 行）
4. 重新运行迁移：`uv run python manage.py migrate`

### 切换到 PostgreSQL（生产环境）
**优点**：性能更好，功能更强大

**步骤**：
1. 安装 PostgreSQL 服务
2. 创建数据库：`CREATE DATABASE smart_recipe_db;`
3. 配置 `.env` 文件：
   ```env
   DB_NAME=smart_recipe_db
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=127.0.0.1
   DB_PORT=5432
   ```
4. 确保驱动已安装：`uv sync`
5. 运行迁移：`uv run python manage.py migrate`

---

## 有用的命令

### 检查和测试
```bash
# 检查 Django 配置
uv run python manage.py check

# 测试配置和数据库连接
uv run python test_config.py

# 完整 API 测试
uv run python test_api.py
```

### 数据库操作
```bash
# 创建迁移文件
uv run python manage.py makemigrations

# 应用迁移
uv run python manage.py migrate

# 进入 Django Shell
uv run python manage.py shell

# 创建超级用户
uv run python manage.py createsuperuser
```

### 依赖管理
```bash
# 安装所有依赖
uv sync

# 添加新依赖
uv add package-name

# 删除依赖
uv remove package-name

# 列出已安装的包
uv pip list
```

### 服务器操作
```bash
# 启动开发服务器
uv run python manage.py runserver

# 使用指定端口
uv run python manage.py runserver 8001

# 允许外部访问
uv run python manage.py runserver 0.0.0.0:8000
```

---

## 获取帮助

如果遇到其他问题：

1. **查看日志**：注意终端输出的错误信息
2. **运行测试脚本**：`uv run python test_config.py`
3. **检查文档**：
   - [CLAUDE.md](../CLAUDE.md) - 项目开发指南
   - [API_TEST_GUIDE.md](./API_TEST_GUIDE.md) - API 测试指南
   - [PROJECT_IMPLEMENTATION_SUMMARY.md](../PROJECT_IMPLEMENTATION_SUMMARY.md) - 实现总结

4. **常用资源**：
   - Django 官方文档: https://docs.djangoproject.com/
   - DRF 文档: https://www.django-rest-framework.org/
   - UV 文档: https://github.com/astral-sh/uv

---

**最后更新**: 2026-02-25
**版本**: 1.0
