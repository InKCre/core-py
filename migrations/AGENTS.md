## migrations/ - Database Migrations (数据库迁移)

Alembic 数据库迁移管理，用于版本化控制数据库 schema 变更。

### 核心文件

- `env.py`: Alembic 环境配置，连接数据库和 SQLModel metadata
- `script.py.mako`: 迁移脚本模板
- `alembic.ini`: Alembic 配置（在项目根目录）
- `versions/`: 迁移脚本目录（自动生成）

### 常用命令

在 [pyproject.toml](../pyproject.toml) 中定义了快捷命令：

```bash
# 自动生成迁移（推荐）
pdm run db:generate "migration message"
# 等同于: alembic revision --autogenerate -m "message" && alembic upgrade head

# 手动创建迁移
pdm run db:revision "migration message"

# 应用迁移
pdm run db:migrate
# 等同于: alembic upgrade head

# 回滚迁移
pdm run db:downgrade -1      # 回滚一个版本
pdm run db:downgrade <revision>  # 回滚到指定版本
```

### 迁移流程

1. **修改 Schema**: 编辑 `app/schemas/` 中的模型类
2. **生成迁移**: `pdm run db:generate "描述变更"`
3. **检查生成的脚本**: 在 `migrations/versions/` 中检查
4. **应用迁移**: 自动执行（`db:generate` 包含了 `upgrade`）

### 注意事项

**Autogenerate 的局限性**:
- ✅ 检测：表、列、索引、外键的增删改
- ❌ 不检测：列类型变更的细节、约束的某些变更
- 生成后务必手动检查迁移脚本

**特殊迁移**:
- PostgreSQL Enum 变更：使用 `alembic-postgresql-enum` 插件
- 数据迁移：在 `upgrade()` 中使用 `op.execute()` 执行 SQL
- 权限管理：见 [grant.sql](grant.sql)

### 配置

数据库连接从 [app/settings.py](../app/settings.py) 的 `database_url` 读取：
```python
# env.py
url = settings.database_url
context.configure(url=url, target_metadata=target_metadata)
```

### 版本控制

- 迁移脚本应纳入 Git 版本控制
- 多人协作：确保迁移顺序正确（避免分支冲突）
- 生产部署：在部署流程中自动执行 `alembic upgrade head`

### 编码指引

**修改 Schema 后**:
```bash
pdm run db:generate "add user email field"
# 检查 migrations/versions/xxxx_add_user_email_field.py
# 如有问题，修改后再次运行
```

**数据迁移示例**:
```python
def upgrade():
    # Schema 变更
    op.add_column('users', sa.Column('status', sa.String(20)))
    
    # 数据迁移
    op.execute("UPDATE users SET status = 'active'")
```

- metadata 来源：`app.schemas.Base`（所有 SQLModel 的基类）
- 确保所有 Schema 在 `app/schemas/__init__.py` 中导入
