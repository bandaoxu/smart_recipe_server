# 智能食谱后端服务 (Smart Recipe Server)

智能食谱小程序的后端 API 服务，提供完整的用户系统、食谱管理、食材识别、购物清单和美食社区功能。

## 📚 技术栈

### 核心框架
- **Web 框架**: Django 5.2.4
- **REST API**: Django REST Framework 3.16.0
- **Python 版本**: Python 3.13+
- **包管理器**: UV

### 数据库
- **开发环境**: SQLite 3
- **生产环境**: PostgreSQL 16+

### 认证与安全
- **JWT 认证**: djangorestframework-simplejwt 5.5.1
- **CORS 支持**: django-cors-headers 4.9.0
- **密码加密**: Django 内置 PBKDF2 算法

### 其他依赖
- **过滤器**: django-filter 25.2
- **图像处理**: Pillow 12.1.1
- **HTTP 请求**: requests 2.32.5
- **环境变量**: python-dotenv 1.2.1
- **文档处理**: python-docx 1.2.0

## 🏗️ 项目架构

```
smart_recipe_server/
├── apps/                          # 应用模块
│   ├── user/                      # 用户模块（注册、登录、个人资料）
│   ├── ingredient/                # 食材模块（食材管理、识别、营养计算）
│   ├── recipe/                    # 食谱模块（CRUD、点赞、收藏、推荐）
│   ├── shopping/                  # 购物清单模块
│   └── community/                 # 社区模块（动态、评论）
├── common/                        # 公共组件
│   ├── response.py                # 统一响应格式
│   ├── pagination.py              # 分页器
│   └── permissions.py             # 权限控制
├── smart_recipe_server/           # 项目配置
│   ├── settings.py                # Django 配置
│   └── urls.py                    # 主路由
├── db.sqlite3                     # SQLite 数据库（开发）
├── manage.py                      # Django 管理脚本
└── pyproject.toml                 # 项目依赖配置
```

## 🚀 快速开始

详细的安装和运行步骤请参考 [SETUP.md](./SETUP.md)

### 简要步骤

```bash
# 1. 安装依赖
uv sync

# 2. 数据库迁移
uv run python manage.py migrate

# 3. 创建超级用户（可选）
uv run python manage.py createsuperuser

# 4. 启动服务器
uv run python manage.py runserver
```

访问：
- API 根路径: http://127.0.0.1:8000/api/
- Admin 后台: http://127.0.0.1:8000/admin/

## 📖 API 文档

### 主要模块

- **用户模块** (`/api/user/`): 注册、登录、个人资料管理
- **食材模块** (`/api/ingredient/`): 食材列表、搜索、识别、营养计算
- **食谱模块** (`/api/recipe/`): 食谱 CRUD、点赞、收藏、推荐
- **购物清单** (`/api/shopping-list/`): 购物清单管理
- **社区模块** (`/api/community/`): 动态发布、评论

详细 API 文档请参考 [API_TEST_GUIDE.md](./API_TEST_GUIDE.md)

## 🧪 测试

```bash
# 测试配置
uv run python test_config.py

# 完整 API 测试
uv run python test_api.py
```

## 📝 核心功能

### ✅ 已实现功能

- **用户系统**: 注册、登录、JWT 认证、个人资料管理
- **食谱管理**: 完整的 CRUD 操作、点赞、收藏、搜索
- **食材管理**: 食材列表、搜索、营养信息、应季推荐
- **购物清单**: 清单管理、基于食谱自动生成
- **社区功能**: 动态发布、评论、点赞
- **权限控制**: 基于 JWT 的细粒度权限管理
- **统一响应**: 标准化的 API 响应格式

### 🔄 待扩展功能

- AI 食材识别（接口已实现，需接入模型）
- 推荐算法优化（协同过滤、深度学习）
- 营养分析增强

## 🔧 开发指南

- [CLAUDE.md](../CLAUDE.md) - 项目开发指南
- [SETUP.md](./SETUP.md) - 安装配置指南
- [API_TEST_GUIDE.md](./API_TEST_GUIDE.md) - API 测试指南
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - 故障排除指南

## 📊 数据统计

- **代码行数**: 3000+ 行（含详细中文注释）
- **API 端点**: 50+ 个
- **数据表**: 10 个业务表 + 11 个 Django 内置表
- **测试覆盖**: 配置测试 + API 完整流程测试

## 🌟 特色

- ✅ 完整的中文代码注释
- ✅ 模块化设计，高内聚低耦合
- ✅ 统一的响应格式和错误处理
- ✅ JWT 认证，安全可靠
- ✅ 支持 SQLite（开发）和 PostgreSQL（生产）
- ✅ 完善的测试脚本
- ✅ 详细的文档

## 📄 许可证

本项目仅供学习和研究使用。

## 👥 贡献者

- 项目开发：智能食谱团队
- 技术支持：Django + DRF 社区

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 联系我们。

---

**最后更新**: 2026-02-25
**版本**: 0.1.0
**状态**: ✅ 后端核心功能已完整实现并测试通过
