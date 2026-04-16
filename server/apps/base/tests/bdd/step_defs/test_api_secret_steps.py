import pytest
from pytest_bdd import given, when, then, scenario, parsers
from rest_framework import status
from rest_framework.test import APIClient

from apps.base.models import UserAPISecret
from apps.base.tests.factories import UserAPISecretFactory, UserFactory

BASE_URL = "/api/v1/base/user_api_secret/"


# --- Scenarios ---

@pytest.mark.bdd
@pytest.mark.django_db
@scenario(
    "../features/api_secret_management.feature",
    "用户创建 API Secret",
)
def test_create_api_secret():
    pass


@pytest.mark.bdd
@pytest.mark.django_db
@scenario(
    "../features/api_secret_management.feature",
    "用户不能重复创建 API Secret",
)
def test_duplicate_create():
    pass


@pytest.mark.bdd
@pytest.mark.django_db
@scenario(
    "../features/api_secret_management.feature",
    "用户只能查看自己的 API Secret",
)
def test_user_isolation():
    pass


@pytest.mark.bdd
@pytest.mark.django_db
@scenario(
    "../features/api_secret_management.feature",
    "完整生命周期",
)
def test_full_lifecycle():
    pass


@pytest.mark.bdd
@pytest.mark.django_db
@scenario(
    "../features/api_secret_management.feature",
    "多团队隔离",
)
def test_multi_team_isolation():
    pass


# --- Shared state fixture ---

@pytest.fixture
def ctx():
    """Mutable context dict shared across steps within a scenario."""
    return {}


# --- Given steps ---

@given("一个已认证的用户属于团队 1", target_fixture="ctx")
def given_authenticated_user_team1(bdd_user, bdd_client):
    ctx = {
        "user": bdd_user,
        "client": bdd_client,
        "response": None,
        "created_secret_id": None,
    }
    ctx["client"].cookies["current_team"] = "1"
    return ctx


@given("该用户已有一个 API Secret")
def given_user_has_secret(ctx):
    UserAPISecretFactory(
        username=ctx["user"].username,
        domain=ctx["user"].domain,
        team=1,
    )


@given("该用户有一个 API Secret")
def given_user_has_a_secret(ctx):
    UserAPISecretFactory(
        username=ctx["user"].username,
        domain=ctx["user"].domain,
        team=1,
    )


@given("另一个用户也有一个 API Secret")
def given_other_user_has_secret(db):
    other_user = UserFactory(username="otheruser", domain="domain.com")
    UserAPISecretFactory(username=other_user.username, domain=other_user.domain, team=1)


@given("该用户在团队 1 有一个 API Secret")
def given_user_has_secret_team1(ctx):
    UserAPISecretFactory(
        username=ctx["user"].username,
        domain=ctx["user"].domain,
        team=1,
    )


@given("该用户在团队 2 也有一个 API Secret")
def given_user_has_secret_team2(ctx):
    UserAPISecretFactory(
        username=ctx["user"].username,
        domain=ctx["user"].domain,
        team=2,
    )


# --- When steps ---

@when("用户请求创建 API Secret")
def when_user_creates_secret(ctx):
    ctx["response"] = ctx["client"].post(BASE_URL, data={})
    if ctx["response"].status_code == status.HTTP_201_CREATED:
        ctx["created_secret_id"] = ctx["response"].data.get("id")


@when("用户请求列出 API Secrets")
def when_user_lists_secrets(ctx):
    ctx["response"] = ctx["client"].get(BASE_URL)


@when("用户请求删除该 API Secret")
def when_user_deletes_secret(ctx):
    secret_id = ctx["created_secret_id"]
    ctx["response"] = ctx["client"].delete(f"{BASE_URL}{secret_id}/")


@when("用户以团队 1 请求列出 API Secrets")
def when_user_lists_team1(ctx):
    ctx["client"].cookies["current_team"] = "1"
    ctx["response"] = ctx["client"].get(BASE_URL)


@when("用户以团队 2 请求列出 API Secrets")
def when_user_lists_team2(ctx):
    ctx["client"].cookies["current_team"] = "2"
    ctx["response"] = ctx["client"].get(BASE_URL)


# --- Then steps ---

@then("返回 201 状态码")
def then_status_201(ctx):
    assert ctx["response"].status_code == status.HTTP_201_CREATED


@then("响应包含有效的 api_secret")
def then_response_has_valid_secret(ctx):
    data = ctx["response"].data
    assert "api_secret" in data
    assert len(data["api_secret"]) == 64


@then("返回失败响应")
def then_failure_response(ctx):
    data = ctx["response"].json()
    assert data["result"] is False


@then("只返回该用户的 API Secret")
def then_only_own_secrets(ctx):
    assert ctx["response"].status_code == status.HTTP_200_OK
    for item in ctx["response"].data:
        assert item["username"] == ctx["user"].username


@then("列表包含 1 条记录")
def then_list_has_one_record(ctx):
    assert ctx["response"].status_code == status.HTTP_200_OK
    assert len(ctx["response"].data) == 1


@then("返回 204 状态码")
def then_status_204(ctx):
    assert ctx["response"].status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)


@then("列表为空")
def then_list_is_empty(ctx):
    assert ctx["response"].status_code == status.HTTP_200_OK
    assert len(ctx["response"].data) == 0


@then("只返回团队 1 的 API Secret")
def then_only_team1_secrets(ctx):
    assert ctx["response"].status_code == status.HTTP_200_OK
    assert len(ctx["response"].data) == 1
    assert ctx["response"].data[0]["team"] == 1


@then("只返回团队 2 的 API Secret")
def then_only_team2_secrets(ctx):
    assert ctx["response"].status_code == status.HTTP_200_OK
    assert len(ctx["response"].data) == 1
    assert ctx["response"].data[0]["team"] == 2
