## Why

BK-Lite 需要支持国产信创数据库（达梦、GaussDB、OceanBase、GoldenDB 等），这些数据库与 PostgreSQL/MySQL 存在兼容性差异，特别是在 Migration 执行时会遇到不支持的索引类型、字段类型变更等问题。

## What Changes

建立统一的数据库信创适配框架：
- ORM 补丁层：`apps/core/db_patches/{db_engine}.py`
- Migration 补丁层：`migrate_patch/patches/{db_engine}/{app_label}/{migration_name}.py`
- 数据库配置：`config/components/database.py`

## Capabilities

### 已支持的数据库

| 数据库 | ENGINE | 状态 |
|--------|--------|------|
| PostgreSQL | `django.db.backends.postgresql` | ✅ 原生支持 |
| MySQL | `django.db.backends.mysql` | ✅ 原生支持 |
| SQLite | `django.db.backends.sqlite3` | ✅ 原生支持 |
| 达梦 (DM) | `cw_cornerstone.db.dameng.backend` | ✅ 已适配 |
| GaussDB | `cw_cornerstone.db.gaussdb.backend` | ✅ 已适配 |
| OceanBase | `cw_cornerstone.db.oceanbase.backend` | ✅ 已适配 |
| GoldenDB | `cw_cornerstone.db.goldendb.backend` | ✅ 已适配 |

### 补丁加载机制

Migration 补丁通过 `cw_cornerstone.migrate_patch` 自动加载，在 `pre_migrate` 信号时替换原始 migration 的 operations。

## Impact

**代码目录结构:**
```
server/
├── apps/core/db_patches/
│   ├── __init__.py          # 数据库引擎到补丁模块的映射
│   ├── dameng.py             # 达梦 ORM 补丁
│   ├── gaussdb.py            # GaussDB ORM 补丁
│   ├── goldendb.py           # GoldenDB ORM 补丁
│   └── oceanbase.py          # OceanBase ORM 补丁
├── migrate_patch/patches/
│   ├── dameng/               # 达梦 Migration 补丁
│   ├── gaussdb/              # GaussDB Migration 补丁
│   ├── goldendb/             # GoldenDB Migration 补丁
│   └── oceanbase/            # OceanBase Migration 补丁
└── config/components/
    └── database.py           # 数据库配置（DB_ENGINE 环境变量）
```

**环境变量:**
- `DB_ENGINE`: 数据库类型（postgresql/mysql/sqlite/dameng/gaussdb/oceanbase/goldendb）
- `DB_NAME`: 数据库名
- `DB_USER`: 用户名
- `DB_PASSWORD`: 密码
- `DB_HOST`: 主机地址
- `DB_PORT`: 端口号
