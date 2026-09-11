"""LLMSkill 记忆空间字段：模型 / 序列化 / 设置页 update+retrieve 回显。"""

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.opspilot.models import LLMSkill, MemorySpace
from apps.opspilot.serializers.llm_serializer import LLMSerializer
from apps.opspilot.tests.test_slice_ops_llm_views import _body, _dispatch, _su
from apps.opspilot.viewsets.llm_view import LLMViewSet

pytestmark = pytest.mark.django_db

LLM_MOD = "apps.opspilot.viewsets.llm_view"


def _space(**kwargs):
    defaults = {
        "name": "personal-notes",
        "team": [1],
        "scope": MemorySpace.SCOPE_PERSONAL,
    }
    defaults.update(kwargs)
    return MemorySpace.objects.create(**defaults)


def _serializer_context(user=None):
    user = user or _su()
    request = APIRequestFactory().get("/")
    force_authenticate(request, user=user)
    request.COOKIES["current_team"] = "1"
    request.user = user
    return {"request": request}


def test_model_persists_memory_space_and_write_rounds():
    space = _space()
    skill = LLMSkill.objects.create(
        name="mem-skill",
        team=[1],
        memory_space=space,
        memory_write_rounds=7,
    )
    skill.refresh_from_db()
    assert skill.memory_space_id == space.id
    assert skill.memory_write_rounds == 7


def test_model_defaults_memory_write_rounds_and_nullable_space():
    skill = LLMSkill.objects.create(name="no-mem", team=[1])
    skill.refresh_from_db()
    assert skill.memory_space_id is None
    assert skill.memory_write_rounds == 10


def test_serializer_create_update_retrieve_memory_fields():
    space = _space()
    other = _space(name="other-notes")
    ctx = _serializer_context()

    created = LLMSerializer(
        data={
            "name": "ser-mem",
            "team": [1],
            "memory_space": space.id,
            "memory_write_rounds": 4,
        },
        context=ctx,
    )
    assert created.is_valid(), created.errors
    skill = created.save()
    skill.refresh_from_db()
    assert skill.memory_space_id == space.id
    assert skill.memory_write_rounds == 4

    retrieved = LLMSerializer(instance=skill, context=ctx)
    assert retrieved.data["memory_space"] == space.id
    assert retrieved.data["memory_write_rounds"] == 4

    updated = LLMSerializer(
        instance=skill,
        data={
            "name": "ser-mem",
            "team": [1],
            "memory_space": other.id,
            "memory_write_rounds": 12,
        },
        context=ctx,
    )
    assert updated.is_valid(), updated.errors
    updated.save()
    skill.refresh_from_db()
    assert skill.memory_space_id == other.id
    assert skill.memory_write_rounds == 12

    cleared = LLMSerializer(
        instance=skill,
        data={
            "name": "ser-mem",
            "team": [1],
            "memory_space": None,
            "memory_write_rounds": 10,
        },
        context=ctx,
    )
    assert cleared.is_valid(), cleared.errors
    cleared.save()
    skill.refresh_from_db()
    assert skill.memory_space_id is None
    assert skill.memory_write_rounds == 10


def test_viewset_create_includes_memory_fields_in_response(mocker):
    mocker.patch(f"{LLM_MOD}.log_operation")
    space = _space()
    resp = _dispatch(
        LLMViewSet,
        "create",
        "post",
        data={
            "name": "create-mem",
            "team": [1],
            "memory_space": space.id,
            "memory_write_rounds": 9,
        },
    )
    assert resp.status_code == 201
    body = _body(resp)
    assert body["memory_space"] == space.id
    assert body["memory_write_rounds"] == 9
    skill = LLMSkill.objects.get(name="create-mem")
    assert skill.memory_space_id == space.id
    assert skill.memory_write_rounds == 9


def test_viewset_update_then_retrieve_echoes_memory_fields(mocker):
    """设置页 PUT 后 GET 必须回显 memory_space / memory_write_rounds。"""
    mocker.patch(f"{LLM_MOD}.log_operation")
    space = _space()
    skill = LLMSkill.objects.create(name="settings-mem", team=[1])

    update_resp = _dispatch(
        LLMViewSet,
        "update",
        "put",
        data={
            "name": "settings-mem",
            "team": [1],
            "memory_space": space.id,
            "memory_write_rounds": 6,
        },
        pk=skill.id,
    )
    assert _body(update_resp)["result"] is True
    skill.refresh_from_db()
    assert skill.memory_space_id == space.id
    assert skill.memory_write_rounds == 6

    retrieve_resp = _dispatch(LLMViewSet, "retrieve", "get", pk=skill.id)
    assert retrieve_resp.status_code == 200
    body = _body(retrieve_resp)
    data = body.get("data", body) if isinstance(body, dict) else body
    assert data["memory_space"] == space.id
    assert data["memory_write_rounds"] == 6


def test_viewset_update_clears_memory_space(mocker):
    mocker.patch(f"{LLM_MOD}.log_operation")
    space = _space()
    skill = LLMSkill.objects.create(
        name="clear-mem",
        team=[1],
        memory_space=space,
        memory_write_rounds=8,
    )
    resp = _dispatch(
        LLMViewSet,
        "update",
        "put",
        data={
            "name": "clear-mem",
            "team": [1],
            "memory_space": None,
            "memory_write_rounds": 10,
        },
        pk=skill.id,
    )
    assert _body(resp)["result"] is True
    skill.refresh_from_db()
    assert skill.memory_space_id is None
    assert skill.memory_write_rounds == 10
