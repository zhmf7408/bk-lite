## 1. 清理旧测试

- [x] 1.1 删除 `apps/monitor/tests/test_alert_name_template.py`
- [x] 1.2 删除 `apps/system_mgmt/tests/nats_api_test.py` 和 `apps/system_mgmt/tests/conftest.py`
- [x] 1.3 清理 `apps/core/tests/__init__.py`（删除空的 tests 目录或保留空 `__init__.py` 供后续使用）

## 2. 添加测试依赖

- [x] 2.1 在 `pyproject.toml` 的 `[project.optional-dependencies.dev]` 中添加 `factory-boy`、`faker`、`pytest-bdd`
- [x] 2.2 执行 `uv sync --extra dev` 验证依赖安装成功

## 3. 重写 pytest 全局配置

- [x] 3.1 重写 `pytest.ini`：testpaths 改为 `apps/`，添加 strict markers（unit/integration/bdd/slow），移除硬编码的 `--reuse-db` 和 `--html`，配置 `--cov=apps`
- [x] 3.2 重写 `.coveragerc`：source 设为 `apps`，omit 排除 tests/migrations/admin.py/__init__.py，设置 `fail_under = 60`，`show_missing = true`
- [x] 3.3 删除旧的 `report.html` 和 `coverage_html/` 输出（如存在），将 `htmlcov/` 加入 `.gitignore`

## 4. 创建根级 conftest.py

- [x] 4.1 在 `server/conftest.py` 中创建 `use_dummy_cache_backend` fixture（autouse），将 Django cache 替换为 DummyCache
- [x] 4.2 创建 `authenticated_user` fixture，返回带有默认 group_list、roles、locale、domain 的 User 实例
- [x] 4.3 创建 `api_client` fixture，返回已认证的 DRF APIClient

## 5. 创建 apps/base 测试目录结构

- [x] 5.1 创建目录结构：`apps/base/tests/{__init__.py, conftest.py, factories.py, unit/__init__.py, integration/__init__.py, bdd/__init__.py, bdd/features/, bdd/step_defs/__init__.py}`
- [x] 5.2 在 `factories.py` 中编写 `UserFactory` 和 `UserAPISecretFactory`（使用 factory-boy + faker）

## 6. 编写 Unit Tests

- [x] 6.1 `apps/base/tests/unit/test_models.py`：测试 `UserAPISecret.generate_api_secret()` 返回格式和唯一性
- [x] 6.2 `apps/base/tests/unit/test_models.py`：测试 User 和 UserAPISecret 的 `unique_together` 约束
- [x] 6.3 `apps/base/tests/unit/test_serializers.py`：测试 `UserAPISecretSerializer` 的 `team_name` 解析逻辑
- [x] 6.4 `apps/base/tests/unit/test_views.py`：测试 `_parse_current_team()` 工具函数（有效值、无效值、缺失值）

## 7. 编写 Integration Tests

- [x] 7.1 `apps/base/tests/integration/test_views.py`：测试 GET /user_api_secret/ 列表接口（数据隔离、未认证拒绝）
- [x] 7.2 测试 POST /user_api_secret/ 创建接口（成功创建、重复创建拒绝、无效 cookie）
- [x] 7.3 测试 DELETE /user_api_secret/{id}/ 删除接口
- [x] 7.4 测试 PUT /user_api_secret/{id}/ 更新被拒绝
- [x] 7.5 测试 POST /user_api_secret/generate_api_secret/ action

## 8. 编写 BDD Tests

- [x] 8.1 创建 `apps/base/tests/bdd/features/api_secret_management.feature`：API Secret 管理全流程场景（创建、查看、删除、重复创建、多团队隔离）
- [x] 8.2 创建 `apps/base/tests/bdd/step_defs/test_api_secret_steps.py`：实现 feature 文件中所有 step 定义
- [x] 8.3 在 `apps/base/tests/bdd/step_defs/conftest.py` 中配置 BDD 专用 fixtures

## 9. 验证与覆盖率

- [x] 9.1 执行 `pytest apps/base/` 确认所有测试通过
- [x] 9.2 执行 `pytest -m unit` / `pytest -m integration` / `pytest -m bdd` 确认 marker 筛选正常
- [x] 9.3 检查覆盖率报告：`apps/base/` 相关文件覆盖率 ≥ 90%
- [x] 9.4 检查 `htmlcov/index.html` 可正常打开
