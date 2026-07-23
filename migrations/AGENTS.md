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
# 生成候选 revision；不会执行 upgrade
pdm run db:generate "migration message"

# 手动创建迁移
pdm run db:revision "migration message"

# 显式应用已提交的迁移
pdm run db:migrate

# 回滚迁移
pdm run db:downgrade -1      # 回滚一个版本
pdm run db:downgrade <revision>  # 回滚到指定版本

# 检查本地 migration contract
pdm run check:migrations
```

### 迁移流程

1. **修改 Schema**: 编辑 `app/schemas/` 中的模型类
2. **生成候选迁移**: `pdm run db:generate "描述变更"`
3. **审查生成脚本**: 检查 upgrade、downgrade、锁、数据与 provider 假设
4. **登记完整性**: `pdm run db:record` 只追加新 revision 的 digest
5. **验证迁移**: 在 disposable PostgreSQL/Neon-compatible 数据库验证
6. **提交 revision**: revision 与 `revision-integrity.json` 是受审代码，必须进入 Git
7. **显式应用**: 仅通过 `pdm run db:migrate` 或 release apply job

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

数据库连接由 `migrations/settings.py` 独立读取：

```python
url = get_migration_database_url()
```

唯一必需输入是 `DATABASE_URL`。Migration 不得依赖 `JWT_SECRET`、LLM、client、
logging 或应用 startup。

### 版本控制

- 迁移脚本应纳入 Git 版本控制
- 多人协作：确保迁移顺序正确（避免分支冲突）
- 生产部署：在部署流程中自动执行 `alembic upgrade head`
- 已发布 revision 必须 append-only；不得修改、删除或在 release 中临时生成
- `revision-integrity.json` 是 hard-cut 后的可信基线；CI 会验证 worktree，并在 base
  已含清单时禁止更改既有条目
- Pull request 与受管分支 push 都会执行完整性检查
- 当前历史将在独立 hard-cut packet 中重建 baseline；在此之前不得改写现有 revision

### 编码指引

**修改 Schema 后**:
```bash
pdm run db:generate "add user email field"
# 检查 migrations/versions/xxxx_add_user_email_field.py
# 在 disposable 数据库验证后提交
pdm run db:migrate
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
- `migrations/metadata.py` 负责显式补齐 `LogModel` 并断言 `logs` 已注册
- 确保所有 Schema 在 `app/schemas/__init__.py` 或 migration metadata 注册面中导入
- `Procfile` release 只能 apply 已提交 revision，禁止 `revision --autogenerate`
