from types import SimpleNamespace
from unittest.mock import Mock

from apps.log.views.collect_config import CollectConfigViewSet, CollectInstanceViewSet


class FakeQuerySet(list):
    def select_related(self, *args):
        return self

    def prefetch_related(self, *args):
        return self

    def delete(self):
        self.deleted = True


class FakeOrganizations(list):
    def all(self):
        return self


def make_request(data):
    return SimpleNamespace(
        user=SimpleNamespace(username="alice", domain="default"),
        data=data,
        COOKIES={"current_team": "1", "include_children": "0"},
    )


def make_instance(instance_id="inst-1", collect_type_id=7, organizations=None):
    return SimpleNamespace(
        id=instance_id,
        collect_type_id=collect_type_id,
        collectinstanceorganization_set=FakeOrganizations([SimpleNamespace(organization=org) for org in organizations or [2]]),
    )


def test_remove_collect_instance_requires_operate_permission(monkeypatch):
    instance = make_instance()
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(return_value=FakeQuerySet([instance])),
    )
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(return_value={"data": {}, "team": [1]}),
    )
    node_mgmt = Mock()
    monkeypatch.setattr(collect_config, "NodeMgmt", node_mgmt)

    response = CollectInstanceViewSet().remove_collect_instance(make_request({"instance_ids": [instance.id]}))

    assert response.status_code == 403
    node_mgmt.assert_not_called()


def test_remove_collect_instance_allows_authorized_org_scope(monkeypatch):
    instance = make_instance()
    config_qs = FakeQuerySet([])
    instance_delete_qs = FakeQuerySet([])
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(side_effect=[FakeQuerySet([instance]), instance_delete_qs]),
    )
    monkeypatch.setattr(collect_config.CollectConfig.objects, "filter", Mock(return_value=config_qs))
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(return_value={"data": {"all": {"team": [2]}}, "team": [1]}),
    )

    response = CollectInstanceViewSet().remove_collect_instance(make_request({"instance_ids": [instance.id]}))

    assert response.status_code == 200
    assert getattr(config_qs, "deleted", False)
    assert getattr(instance_delete_qs, "deleted", False)


def test_remove_collect_instance_allows_instance_level_operate_permission(monkeypatch):
    instance = make_instance()
    config_qs = FakeQuerySet([])
    instance_delete_qs = FakeQuerySet([])
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(side_effect=[FakeQuerySet([instance]), instance_delete_qs]),
    )
    monkeypatch.setattr(collect_config.CollectConfig.objects, "filter", Mock(return_value=config_qs))
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(
            return_value={
                "data": {
                    str(instance.collect_type_id): {
                        "instance": [{"id": instance.id, "permission": ["Operate"]}],
                    }
                },
                "team": [1],
            }
        ),
    )

    response = CollectInstanceViewSet().remove_collect_instance(make_request({"instance_ids": [instance.id]}))

    assert response.status_code == 200
    assert getattr(config_qs, "deleted", False)
    assert getattr(instance_delete_qs, "deleted", False)


def test_get_config_content_requires_view_permission(monkeypatch):
    instance = make_instance()
    config = SimpleNamespace(id="cfg-1", collect_instance_id=instance.id, collect_instance=instance)
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectConfig.objects,
        "filter",
        Mock(return_value=FakeQuerySet([config])),
    )
    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(return_value=FakeQuerySet([instance])),
    )
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(return_value={"data": {}, "team": [1]}),
    )
    node_mgmt = Mock()
    monkeypatch.setattr(collect_config, "NodeMgmt", node_mgmt)

    response = CollectConfigViewSet().get_config_content(make_request({"ids": [config.id]}))

    assert response.status_code == 403
    node_mgmt.assert_not_called()


def test_get_config_content_allows_instance_level_view_permission(monkeypatch):
    instance = make_instance()
    config = SimpleNamespace(id="cfg-1", collect_instance_id=instance.id, collect_instance=instance, file_type="yaml", is_child=False)
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectConfig.objects,
        "filter",
        Mock(return_value=FakeQuerySet([config])),
    )
    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(return_value=FakeQuerySet([instance])),
    )
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(
            return_value={
                "data": {
                    str(instance.collect_type_id): {
                        "instance": [{"id": instance.id, "permission": ["View"]}],
                    }
                },
                "team": [1],
            }
        ),
    )
    node_mgmt = Mock()
    node_mgmt.return_value.get_configs_by_ids.return_value = [{"config_template": "key: value"}]
    monkeypatch.setattr(collect_config, "NodeMgmt", node_mgmt)

    response = CollectConfigViewSet().get_config_content(make_request({"ids": [config.id]}))

    assert response.status_code == 200
    node_mgmt.return_value.get_configs_by_ids.assert_called_once_with([config.id])


def test_remove_collect_instance_allows_merged_duplicate_instance_permissions(monkeypatch):
    instance = make_instance()
    config_qs = FakeQuerySet([])
    instance_delete_qs = FakeQuerySet([])
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(side_effect=[FakeQuerySet([instance]), instance_delete_qs]),
    )
    monkeypatch.setattr(collect_config.CollectConfig.objects, "filter", Mock(return_value=config_qs))
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(
            return_value={
                "data": {
                    str(instance.collect_type_id): {
                        "instance": [
                            {"id": instance.id, "permission": ["View"]},
                            {"id": instance.id, "permission": ["Operate"]},
                        ],
                    }
                },
                "team": [1],
            }
        ),
    )

    response = CollectInstanceViewSet().remove_collect_instance(make_request({"instance_ids": [instance.id]}))

    assert response.status_code == 200
    assert getattr(config_qs, "deleted", False)
    assert getattr(instance_delete_qs, "deleted", False)


def test_set_organizations_rejects_target_org_outside_authorized_scope(monkeypatch):
    instance = make_instance()
    from apps.log.views import collect_config

    monkeypatch.setattr(
        collect_config.CollectInstance.objects,
        "filter",
        Mock(return_value=FakeQuerySet([instance])),
    )
    monkeypatch.setattr(
        collect_config,
        "get_permissions_rules",
        Mock(return_value={"data": {"all": {"team": [2]}}, "team": [1]}),
    )
    set_orgs = Mock()
    monkeypatch.setattr(collect_config.CollectTypeService, "set_instances_organizations", set_orgs)

    response = CollectInstanceViewSet().set_organizations(make_request({"instance_ids": [instance.id], "organizations": [3]}))

    assert response.status_code == 403
    set_orgs.assert_not_called()
