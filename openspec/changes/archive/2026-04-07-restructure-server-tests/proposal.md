## Why

当前 server 端几乎没有有效的测试体系——仅存 3 个分散的测试文件，pytest.ini 硬编码只跑 `apps/core/tests`（实际为空），覆盖率统计也仅针对 `apps/core`。缺少统一的测试规范、数据工厂、BDD 场景测试和覆盖率门禁，导致代码质量无法保障、重构风险高。

## What Changes

- **删除所有现有测试文件**：移除 `apps/monitor/tests/`、`apps/system_mgmt/tests/` 下的旧测试，从零开始建立规范化测试体系
- **重建 pytest 基础设施**：重写 `pytest.ini`，配置全局 marker（unit/integration/bdd）、测试发现路径、覆盖率统计
- **引入新测试依赖**：添加 `factory-boy`、`faker`、`pytest-bdd` 到 dev dependencies
- **建立三层测试金字塔**：Unit (TDD) → Integration → BDD，定义标准目录结构
- **以 `apps/base` 为试点**：为 User 模型、UserAPISecret CRUD 全流程编写完整的三层测试
- **配置覆盖率报告**：`.coveragerc` 覆盖所有 apps，输出 terminal + HTML 报告，设置最低覆盖率门禁
- **建立根级 conftest.py**：提供全局 fixtures（DB 配置、cache mock、认证用户等）

## Capabilities

### New Capabilities

- `test-infrastructure`: pytest 全局配置、marker 定义、根级 conftest.py、.coveragerc 覆盖率配置、新依赖引入
- `test-base-app`: apps/base 完整三层测试——Unit Tests (models, serializers)、Integration Tests (API views)、BDD Tests (Gherkin feature 场景)
- `test-conventions`: 测试目录结构规范、命名约定、Factory 模式、fixture 分层策略，作为后续 app 推广的模板

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **配置文件**: `pytest.ini`、`.coveragerc`、`pyproject.toml`（dev dependencies）
- **删除文件**: `apps/monitor/tests/test_alert_name_template.py`、`apps/system_mgmt/tests/nats_api_test.py`、`apps/system_mgmt/tests/conftest.py`
- **新增文件**: `conftest.py`（根级）、`apps/base/tests/` 整个测试目录树
- **依赖变更**: 新增 `factory-boy`、`faker`、`pytest-bdd`、`pytest-factoryboy`
- **CI 影响**: Makefile 的 `test` target 行为会变化，覆盖率报告路径从 `coverage_html/` 改为 `htmlcov/`
