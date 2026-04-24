import json

import pytest
from rest_framework import status

from apps.log.utils.query_log import VictoriaMetricsAPI
from apps.log.models.log_group import LogGroup, LogGroupOrganization, SearchCondition


class DummyResponse:
    def __init__(self, lines):
        self._lines = lines

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        for line in self._lines:
            yield line


def test_query_skips_invalid_json_lines(mocker):
    response = DummyResponse(
        [
            json.dumps({"_msg": "ok-1"}),
            '{"_msg":"bad\nraw-control"}',
            json.dumps({"_msg": "ok-2"}),
        ]
    )
    post_mock = mocker.patch("apps.log.utils.query_log.requests.post", return_value=response)

    api = VictoriaMetricsAPI()

    result = api.query("*", "", "", 10)

    assert result == [{"_msg": "ok-1"}, {"_msg": "ok-2"}]
    post_mock.assert_called_once()


def test_query_ignores_empty_lines(mocker):
    response = DummyResponse(["", json.dumps({"_msg": "ok"}), ""])
    mocker.patch("apps.log.utils.query_log.requests.post", return_value=response)

    api = VictoriaMetricsAPI()

    result = api.query("*", "", "", 10)

    assert result == [{"_msg": "ok"}]


def test_query_logs_malformed_line_context(mocker):
    response = DummyResponse(['{"_msg":"bad\nraw-control"}'])
    mocker.patch("apps.log.utils.query_log.requests.post", return_value=response)
    warning_mock = mocker.patch("apps.log.utils.query_log.logger.warning")

    api = VictoriaMetricsAPI()

    result = api.query("level:error", "start-ts", "end-ts", 5)

    assert result == []
    malformed_call = warning_mock.call_args_list[0]
    assert "VictoriaLogs query 返回非法 JSON 行，已跳过" in malformed_call.args[0]
    assert "error_window_repr=" in malformed_call.args[0]
    assert "query_preview=" not in malformed_call.args[0]
    extra = malformed_call.kwargs["extra"]
    assert extra["line_length"] > 0
    assert extra["error_position"] >= 0
    assert "\\n" in extra["error_window_repr"]


def _mock_group_permission(mocker, teams=None, instance_ids=None, instance_permissions=None):
    if instance_permissions is None:
        instance_permissions = [{"id": group_id, "permission": ["View", "Operate"]} for group_id in (instance_ids or [])]
    mocked_permission = {
        "team": teams or [],
        "instance": instance_permissions,
    }
    mocker.patch(
        "apps.log.services.access_scope.get_permission_rules",
        return_value=mocked_permission,
    )


@pytest.mark.django_db
def test_search_endpoint_expands_authorized_groups_when_log_groups_missing(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Group 1", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=1)
    _mock_group_permission(mocker, teams=[1])
    search_mock = mocker.patch("apps.log.views.search.SearchService.search_logs", return_value=[])

    api_client.cookies["current_team"] = "1"
    response = api_client.post(
        "/api/v1/log/search/search/",
        data={"query": "level:error", "start_time": "", "end_time": "", "limit": 5},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    search_mock.assert_called_once_with("level:error", "", "", 5, ["g-1"])


@pytest.mark.django_db
def test_search_endpoint_rejects_unauthorized_log_group(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-2", name="Group 2", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-2", organization=2)
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.post(
        "/api/v1/log/search/search/",
        data={"query": "*", "log_groups": ["g-2"]},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["result"] is False


@pytest.mark.django_db
def test_field_values_endpoint_uses_authorized_log_groups(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Group 1", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=1)
    _mock_group_permission(mocker, teams=[1])
    field_values_mock = mocker.patch("apps.log.views.search.SearchService.field_values", return_value={"values": []})

    api_client.cookies["current_team"] = "1"
    response = api_client.get(
        "/api/v1/log/search/field_values/?filed=host&query=level:error",
    )

    assert response.status_code == status.HTTP_200_OK
    field_values_mock.assert_called_once_with("", "", "host", 100, query="level:error", log_groups=["g-1"])


@pytest.mark.django_db
def test_log_group_update_is_scoped_by_permission(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Allowed", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroup.objects.create(id="g-2", name="Denied", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=1)
    LogGroupOrganization.objects.create(log_group_id="g-2", organization=2)
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.patch(
        "/api/v1/log/log_group/g-2/",
        data={"name": "changed"},
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_log_group_update_rejects_view_only_instance_permission(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Allowed", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=2)
    _mock_group_permission(
        mocker,
        teams=[],
        instance_permissions=[{"id": "g-1", "permission": ["View"]}],
    )

    api_client.cookies["current_team"] = "1"
    response = api_client.patch(
        "/api/v1/log/log_group/g-1/",
        data={"name": "changed"},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_log_group_destroy_rejects_view_only_instance_permission(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Allowed", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=2)
    _mock_group_permission(
        mocker,
        teams=[],
        instance_permissions=[{"id": "g-1", "permission": ["View"]}],
    )

    api_client.cookies["current_team"] = "1"
    response = api_client.delete("/api/v1/log/log_group/g-1/")

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_log_group_create_rejects_unauthorized_organizations(api_client, authenticated_user, mocker):
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.post(
        "/api/v1/log/log_group/",
        data={
            "id": "g-new",
            "name": "New Group",
            "rule": {"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]},
            "organizations": [2],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "无权限绑定日志分组" in str(response.json())


@pytest.mark.django_db
def test_search_condition_rejects_unauthorized_log_groups(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-2", name="Denied", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-2", organization=2)
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.post(
        "/api/v1/log/search_conditions/",
        data={
            "name": "saved-query",
            "condition": {"query": "*", "log_groups": ["g-2"]},
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert SearchCondition.objects.count() == 0


@pytest.mark.django_db
def test_search_condition_list_hides_inaccessible_saved_conditions(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-1", name="Allowed", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroup.objects.create(id="g-2", name="Denied", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-1", organization=1)
    LogGroupOrganization.objects.create(log_group_id="g-2", organization=2)
    SearchCondition.objects.create(name="allowed", condition={"query": "*", "log_groups": ["g-1"]}, organization=1, created_by="alice")
    SearchCondition.objects.create(name="denied", condition={"query": "*", "log_groups": ["g-2"]}, organization=1, created_by="alice")
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.get("/api/v1/log/search_conditions/")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["name"] == "allowed"


@pytest.mark.django_db
def test_search_condition_retrieve_returns_404_for_inaccessible_saved_condition(api_client, authenticated_user, mocker):
    LogGroup.objects.create(id="g-2", name="Denied", rule={"mode": "AND", "conditions": [{"field": "app", "op": "==", "value": "demo"}]})
    LogGroupOrganization.objects.create(log_group_id="g-2", organization=2)
    condition = SearchCondition.objects.create(
        name="denied",
        condition={"query": "*", "log_groups": ["g-2"]},
        organization=1,
        created_by="alice",
    )
    _mock_group_permission(mocker, teams=[1])

    api_client.cookies["current_team"] = "1"
    response = api_client.get(f"/api/v1/log/search_conditions/{condition.id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
