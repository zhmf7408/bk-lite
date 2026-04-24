# 数据库信创适配 - 技术设计

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Django ORM Layer                        │
├─────────────────────────────────────────────────────────────┤
│                   apps/core/db_patches/                      │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│    │  dameng  │ │ gaussdb  │ │oceanbase │ │ goldendb │      │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│                  migrate_patch/patches/                      │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│    │  dameng  │ │ gaussdb  │ │oceanbase │ │ goldendb │      │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│               cw_cornerstone.db.{engine}.backend             │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│    │  dameng  │ │ gaussdb  │ │oceanbase │ │ goldendb │      │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Database Drivers                          │
│    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│    │   dmPy   │ │  psycopg │ │  pymysql │ │  pymysql │      │
│    └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## 补丁类型

### 1. Fake 操作类

用于跳过不支持的 Migration 操作：

```python
class FakeAddIndex(migrations.AddIndex):
    """跳过不支持的索引创建"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass

class FakeRemoveIndex(migrations.RemoveIndex):
    """跳过不存在的索引删除"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass

class FakeAlterField(migrations.AlterField):
    """跳过不支持的字段类型变更"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass

class FakeRemoveField(migrations.RemoveField):
    """跳过不支持的字段删除（如 rowkey 列）"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass

class FakeRemoveConstraint(migrations.RemoveConstraint):
    """跳过不存在的约束删除"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass
```

### 2. 初始 Migration 修改

在 `0001_initial.py` 补丁中直接定义最终字段类型，避免后续 AlterField：

```python
# 原始定义
("description", models.TextField(...))
# 后续有 AlterField 改为 JSONField

# 补丁中直接定义
("description", models.JSONField(blank=True, default=dict, help_text="规则描述", null=True))
```

## 各数据库不支持的特性

### GaussDB (ustore)

| 问题 | 错误信息 | 解决方案 |
|------|----------|----------|
| GIN 索引 | `gin index is not supported for ustore` | `FakeAddIndex` |
| jsonb ubtree 索引 | `data type jsonb has no default operator class for access method "ubtree"` | `FakeAddIndex` |
| BTreeIndex 重复 | 与 `db_index=True` 重复 | `FakeAddIndex` |

### OceanBase

| 问题 | 错误信息 | 解决方案 |
|------|----------|----------|
| JSON 列索引 | 错误码 3152 | `FakeAddIndex` |
| ALTER 非字符串类型 | 错误码 1235 | `FakeAlterField` |
| 删除 rowkey 列 | 错误码 1235 | `FakeRemoveField` |
| 删除不存在约束 | 错误码 1091 | `FakeRemoveConstraint` |

### GoldenDB

| 问题 | 错误信息 | 解决方案 |
|------|----------|----------|
| GinIndex | 不支持 | `FakeAddIndex` |
| BTreeIndex | 不支持 | `FakeAddIndex` |
| JSONField 索引 | 不支持 | `FakeAddIndex` |

### 达梦 (DM)

| 问题 | 错误信息 | 解决方案 |
|------|----------|----------|
| 重复索引 | Duplicate key name | `FakeAddIndex` |
| GinIndex/BTreeIndex | 不支持 | `FakeAddIndex` |

## 新增数据库适配流程

1. **创建 ORM 补丁**
   ```
   apps/core/db_patches/{new_db}.py
   ```

2. **注册补丁映射**
   ```python
   # apps/core/db_patches/__init__.py
   DB_PATCHES = {
       "new_db": "apps.core.db_patches.new_db",
   }
   ```

3. **创建 Migration 补丁目录**
   ```
   migrate_patch/patches/{new_db}/
   migrate_patch/patches/{new_db}/__init__.py
   ```

4. **为有问题的 app 创建补丁**
   ```
   migrate_patch/patches/{new_db}/{app_label}/__init__.py
   migrate_patch/patches/{new_db}/{app_label}/{migration_name}.py
   ```

5. **添加数据库配置**
   ```python
   # config/components/database.py
   elif db_engine == "new_db":
       DATABASES = {
           "default": {
               "ENGINE": "cw_cornerstone.db.new_db.backend",
               ...
           }
       }
   ```

## 补丁文件模板

```python
# {DB_NAME} 数据库兼容补丁
# 原始文件: apps/{app_label}/migrations/{migration_name}.py
# 问题: [描述问题]
# 处理策略: [描述解决方案]

from django.db import migrations, models


class FakeAddIndex(migrations.AddIndex):
    """跳过不支持的索引"""
    def database_forwards(self, *args, **kwargs):
        pass
    def database_backwards(self, *args, **kwargs):
        pass


class Migration(migrations.Migration):
    dependencies = [
        ("{app_label}", "{previous_migration}"),
    ]

    operations = [
        # ... 复制原始 operations，将不支持的替换为 Fake 类
    ]
```

## 验证命令

```bash
# 检查 migration 计划
python manage.py migrate --plan

# 执行 migration
python manage.py migrate

# 语法验证
python -m py_compile migrate_patch/patches/{db}/{app}/{migration}.py
```
