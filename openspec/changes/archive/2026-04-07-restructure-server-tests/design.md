## Context

BK-Lite server 是一个 Django 4.2 + DRF 项目，使用 split_settings 管理配置，支持多种数据库后端（PostgreSQL、MySQL、SQLite 等）。当前测试基础设施名存实亡：`pytest.ini` 只指向空的 `apps/core/tests`，散落的 3 个测试文件缺乏统一规范。

项目已安装 `pytest-django`、`pytest-cov`、`pytest-mock`、`pytest-asyncio` 等核心插件，但缺少数据工厂（factory-boy）和 BDD（pytest-bdd）支持。

`apps/base` 包含 `User`（自定义 AbstractUser）和 `UserAPISecret`（API 密钥管理）两个模型，以及一个完整的 DRF ViewSet，有权限装饰器、Cookie 解析、序列化器上下文依赖等典型测试场景，适合作为试点。

## Goals / Non-Goals

**Goals:**
- 建立可复用的 pytest 三层测试架构（Unit / Integration / BDD）
- 为 `apps/base` 编写完整测试，覆盖率 ≥ 90%
- 配置全局覆盖率报告（terminal + HTML），设置最低覆盖率门禁
- 形成标准化测试模板，供后续 app 推广使用

**Non-Goals:**
- 不在本次为其他 app（cmdb、job_mgmt、monitor 等）编写测试
- 不改动业务代码（纯测试侧变更）
- 不配置 CI/CD pipeline（本次只关注本地测试体系）
- 不引入 end-to-end 浏览器测试

## Decisions

### 1. 测试框架选择：pytest-bdd vs behave

**选择**: pytest-bdd

**理由**: 项目已完全使用 pytest 生态，pytest-bdd 可以复用所有现有 fixtures 和 plugins，无需维护两套测试运行器。behave 虽然更纯粹但需要独立运行，与 pytest-cov 等插件集成困难。

### 2. 数据工厂：factory-boy + faker

**选择**: factory-boy 作为主工厂，faker 提供随机数据

**理由**: factory-boy 是 Django 生态的事实标准，与 pytest-django 集成良好。相比手动 `Model.objects.create()`，factory 可以只声明测试关注的字段，其余自动填充，减少测试噪音。

**替代方案**: model-bakery——更轻量但定制性不足，不适合需要精确控制的场景。

### 3. 测试目录结构：app 内分层 vs 顶层 tests 目录

**选择**: 每个 app 内 `tests/` 目录，按 unit/integration/bdd 分层

**理由**: 测试与被测代码同位置，便于定位和维护。通过 pytest markers 实现按层运行（`pytest -m unit` 只跑单元测试）。

```
apps/<app>/tests/
├── conftest.py          # app 级 fixtures + factories
├── factories.py         # Factory Boy 工厂
├── unit/                # @pytest.mark.unit
├── integration/         # @pytest.mark.integration
└── bdd/                 # @pytest.mark.bdd
    ├── features/*.feature
    └── step_defs/test_*.py
```

### 4. 测试数据库策略

**选择**: 使用 pytest-django 默认的 transaction rollback + SQLite in-memory

**理由**: 单元测试和集成测试都在事务中运行并自动回滚，无需手动清理。本地开发可选 `--reuse-db` 加速。pytest.ini 中不再硬编码 `--reuse-db`，由开发者按需传入。

### 5. 权限装饰器测试策略

**选择**: 双层测试

- **Unit tests**: Mock 掉 `@HasPermission` 装饰器，只测 ViewSet 业务逻辑
- **Integration tests**: 构造真实带权限的 User，验证完整权限链路

**理由**: 分离关注点。单元测试验证"逻辑对不对"，集成测试验证"权限通不通"。

### 6. Serializer 上下文依赖处理

`UserAPISecretSerializer.__init__()` 直接访问 `self.context["request"].user.group_list`，无法脱离 request 上下文实例化。

**选择**: Unit test 中通过 `RequestFactory` + mock user 构造完整 context

### 7. BDD Feature 粒度

**选择**: 每个业务领域一个 .feature 文件，每个用户故事一个 Scenario

**理由**: .feature 文件是给人读的"活文档"，粒度过细会变成代码的翻译，失去沟通价值。

### 8. 覆盖率配置

**选择**:
- `--cov=apps` 覆盖所有 app
- `--cov-report=term-missing` 终端显示未覆盖行号
- `--cov-report=html:htmlcov` HTML 详细报告
- `.coveragerc` 中 `fail_under = 60`（初始门禁，逐步提高）
- 排除 migrations、admin.py、`__init__.py`

## Risks / Trade-offs

- **[Risk] SQLite 与 PostgreSQL 行为差异** → 仅影响数据库特定功能（如 JSONField 查询），base app 的测试场景不涉及。后续 app 如需 PG 特性可单独配置 test database。
- **[Risk] 删除旧测试丢失知识** → 旧测试仅 3 个文件且质量不高，迁移价值低于从零编写规范化测试的收益。
- **[Risk] pytest-bdd 的 feature 文件维护成本** → 只在 API 行为层面写 BDD，不下沉到内部实现。控制 feature 文件数量。
- **[Trade-off] `fail_under = 60` 门禁较低** → 初始值故意保守，避免引入测试体系时就因门禁过高阻塞开发。随着测试逐步补充再提高。
