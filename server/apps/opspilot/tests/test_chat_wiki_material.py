"""对话把明确要求记下的知识落成文本资料。"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from apps.opspilot.enum import SkillTypeChoices
from apps.opspilot.models import BuildRecord, KnowledgePage, LLMSkill, Material
from apps.opspilot.services.caller_identity import CALLER_IDENTITY_CONFIG_KEY
from apps.opspilot.services.wiki.chat_material_service import (
    REPLY_DENIED,
    REPLY_FAILED,
    REPLY_NAME_KB,
    REPLY_NO_KB,
    REPLY_NOT_WRITTEN,
    REPLY_SUCCESS,
    REPLY_SWITCH_OFF,
    WIKI_MATERIAL_ACTOR_KEY,
    WIKI_MATERIAL_TOOL_NAME,
    apply_wiki_material_runtime,
    external_actor,
    system_actor,
    wiki_grounded_uses_single_model_call,
    write_chat_wiki_material,
)
from apps.opspilot.services.wiki.material_build_queue_service import QUEUE_ITEM_TRIGGER
from apps.opspilot.services.wiki.material_source_service import source_metadata
from apps.opspilot.tests.wiki.factories import WikiFactory
from apps.system_mgmt.models import User as SystemUser
from apps.system_mgmt.models.operation_log import OperationLog

pytestmark = pytest.mark.django_db

_BODY_TAIL = "BODY_TAIL_SENTINEL"
_BROKER_SECRET = "redis://:hunter2-secret@broker:6379/0"


def _user(username="alice", domain="corp.example", user_id="user-alice", disabled=False):
    return SystemUser.objects.create(
        username=username,
        domain=domain,
        display_name=username[:100],
        email=f"{username[:40]}@example.com",
        password="x",
        user_id=user_id,
        disabled=disabled,
    )


def _skill(*knowledge_bases, allow=True, name="wiki-writer"):
    skill = LLMSkill.objects.create(
        name=name,
        team=[1],
        usage_team=[1],
        allow_wiki_material_write=allow,
    )
    if knowledge_bases:
        skill.wiki_knowledge_bases.add(*knowledge_bases)
    return skill


def _kb(name):
    return WikiFactory().knowledge_base(name=name)


def _patch_runner():
    return patch(
        "apps.opspilot.services.wiki.material_build_queue_service.kick_kb_material_build_runner",
        return_value=True,
    )


def _write(skill, user, **overrides):
    payload = {
        "skill": skill,
        "explicit_request": True,
        "title": "磁盘将满",
        "body": "根分区连续上涨，先清理日志再扩容。",
        "knowledge_base_name": "",
        "actor": system_actor(user.username, user.domain),
    }
    payload.update(overrides)
    return write_chat_wiki_material(**payload)


def test_success_enqueues_text_material_and_records_the_person(caplog):
    user = _user(username="u" * 40, user_id="long-user")
    kb = _kb("运维知识")
    skill = _skill(kb)
    body = ("甲" * 50) + _BODY_TAIL
    caplog.set_level("WARNING", logger="opspilot")

    with _patch_runner():
        reply = _write(skill, user, title="  " + ("标题" * 200), body=body, knowledge_base_name="别的库")

    assert reply == REPLY_SUCCESS
    material = Material.objects.get()
    assert material.knowledge_base_id == kb.id
    assert material.material_type == "text"
    assert material.status == "queued"
    assert material.text_content == body
    assert material.name == ("标题" * 200).strip()[:255]
    assert material.created_by == user.username[:32]
    assert len(material.created_by) == 32
    expected_source = source_metadata(kb, source_relative_path=f"chat/{material.id}.txt")
    assert material.source_relative_path == expected_source["source_relative_path"]
    assert material.source_folder_path == expected_source["source_folder_path"]
    assert material.source_identity == expected_source["source_identity"]
    assert material.source_identity
    log = OperationLog.objects.get()
    assert log.app == "opspilot"
    assert log.action_type == OperationLog.ACTION_CREATE
    assert log.target_type == "wiki_material"
    assert log.target_id == str(material.id)
    assert log.username == user.username
    assert log.domain == user.domain
    assert log.source_ip == "0.0.0.0"
    assert log.detail == {
        "knowledge_base_id": kb.id,
        "knowledge_base_name": kb.name,
        "material_name": material.name,
        "material_id": material.id,
        "body_excerpt": "甲" * 50,
    }
    assert _BODY_TAIL not in log.detail["body_excerpt"]
    assert KnowledgePage.objects.count() == 0
    assert BuildRecord.objects.filter(trigger=QUEUE_ITEM_TRIGGER, inputs__material_id=material.id).exists()
    assert _BODY_TAIL not in caplog.text
    assert body not in caplog.text


def test_enqueue_error_discards_material_and_does_not_claim_success(caplog):
    user = _user()
    skill = _skill(_kb("运维知识"))
    caplog.set_level("WARNING", logger="opspilot")

    with patch(
        "apps.opspilot.services.wiki.chat_material_service.enqueue_material_builds",
        side_effect=RuntimeError(_BROKER_SECRET),
    ):
        reply = _write(skill, user, body="正文哨兵不应出现在日志")

    assert reply == REPLY_FAILED
    assert REPLY_SUCCESS not in reply
    assert Material.objects.count() == 0
    assert OperationLog.objects.count() == 0
    assert _BROKER_SECRET not in caplog.text
    assert "正文哨兵不应出现在日志" not in caplog.text
    assert "error_type=RuntimeError" in caplog.text


def test_enqueue_without_queue_id_discards_material():
    user = _user()
    skill = _skill(_kb("运维知识"))

    with patch(
        "apps.opspilot.services.wiki.chat_material_service.enqueue_material_builds",
        return_value={"queued": [], "already_queued": [], "skipped": [{"id": 1, "reason": "invalid"}]},
    ):
        reply = _write(skill, user)

    assert reply == REPLY_FAILED
    assert Material.objects.count() == 0
    assert OperationLog.objects.count() == 0


def test_audit_failure_discards_queued_material():
    user = _user()
    skill = _skill(_kb("运维知识"))

    with _patch_runner(), patch(
        "apps.opspilot.services.wiki.chat_material_service.OperationLog.objects.create",
        side_effect=RuntimeError("audit down"),
    ):
        reply = _write(skill, user)

    assert reply == REPLY_FAILED
    assert Material.objects.count() == 0
    assert OperationLog.objects.count() == 0
    assert BuildRecord.objects.filter(trigger=QUEUE_ITEM_TRIGGER).count() == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"explicit_request": False},
        {"explicit_request": "true"},
        {"title": "  "},
        {"body": ""},
    ],
)
def test_missing_explicit_request_or_text_creates_nothing(overrides):
    user = _user()
    skill = _skill(_kb("运维知识"))

    reply = _write(skill, user, **overrides)

    assert reply == REPLY_NOT_WRITTEN
    assert Material.objects.count() == 0


def test_switch_off_refuses_without_a_material():
    user = _user()
    skill = _skill(_kb("运维知识"), allow=False)

    reply = _write(skill, user)

    assert reply == REPLY_SWITCH_OFF
    assert Material.objects.count() == 0


def test_enabled_skill_without_knowledge_base_refuses():
    user = _user()
    skill = _skill()

    reply = _write(skill, user)

    assert reply == REPLY_NO_KB
    assert Material.objects.count() == 0


def test_single_bound_knowledge_base_ignores_a_wrong_name():
    user = _user()
    bound = _kb("唯一库")
    unbound = _kb("未绑定库")
    skill = _skill(bound)

    with _patch_runner():
        reply = _write(skill, user, knowledge_base_name=unbound.name)

    assert reply == REPLY_SUCCESS
    assert Material.objects.get().knowledge_base_id == bound.id
    assert Material.objects.filter(knowledge_base=unbound).count() == 0


def test_multiple_knowledge_bases_require_one_exact_name():
    user = _user()
    first = _kb(" 磁盘告警 ")
    second = _kb("网络告警")
    unbound = _kb("未绑定库")
    skill = _skill(first, second)

    missing = _write(skill, user, knowledge_base_name="")
    wrong = _write(skill, user, knowledge_base_name=unbound.name)
    assert missing == REPLY_NAME_KB
    assert wrong == REPLY_NAME_KB
    assert Material.objects.count() == 0

    with _patch_runner():
        reply = _write(skill, user, knowledge_base_name="磁盘告警")

    assert reply == REPLY_SUCCESS
    assert Material.objects.get().knowledge_base_id == first.id


def test_duplicate_bound_names_are_refused():
    user = _user()
    skill = _skill(_kb("磁盘告警"), _kb("磁盘告警"))

    reply = _write(skill, user, knowledge_base_name="磁盘告警")

    assert reply == REPLY_NAME_KB
    assert Material.objects.count() == 0


@pytest.mark.parametrize(
    "actor",
    [
        None,
        system_actor("alice", "corp.example"),
        external_actor(""),
        external_actor("om_not_a_person"),
        external_actor("alice@example.com"),
        external_actor("爱丽丝"),
    ],
)
def test_unresolved_person_is_denied(actor):
    user = _user(disabled=actor == system_actor("alice", "corp.example"))
    if actor == external_actor("alice@example.com"):
        user.email = "alice@example.com"
        user.save(update_fields=["email"])
    skill = _skill(_kb("运维知识"))

    reply = _write(skill, user, actor=actor)

    assert reply == REPLY_DENIED
    assert Material.objects.count() == 0


def test_external_sender_matches_one_username_or_user_id():
    by_name = _user(username="ou_real", user_id="id-name", domain="a.example")
    skill = _skill(_kb("运维知识"))
    with _patch_runner():
        reply = _write(skill, by_name, actor=external_actor("ou_real"))
    assert reply == REPLY_SUCCESS
    assert OperationLog.objects.get().username == "ou_real"

    Material.objects.all().delete()
    OperationLog.objects.all().delete()
    by_id = _user(username="bob", user_id="staff-9", domain="b.example")
    with _patch_runner():
        reply = _write(skill, by_id, actor=external_actor("staff-9"))
    assert reply == REPLY_SUCCESS
    assert OperationLog.objects.get().username == "bob"


def test_ambiguous_external_sender_is_denied():
    _user(username="same", user_id="id-a", domain="a.example")
    _user(username="same", user_id="id-b", domain="b.example")
    skill = _skill(_kb("运维知识"))

    reply = _write(skill, SystemUser.objects.first(), actor=external_actor("same"))

    assert reply == REPLY_DENIED
    assert Material.objects.count() == 0

    _user(username="left", user_id="shared-token", domain="c.example")
    _user(username="shared-token", user_id="right-id", domain="d.example")
    reply = _write(skill, SystemUser.objects.first(), actor=external_actor("shared-token"))
    assert reply == REPLY_DENIED
    assert Material.objects.count() == 0


def test_runtime_prompt_and_tool_follow_the_switch():
    off = _skill(allow=False, name="off")
    on = _skill(_kb("运维知识"), allow=True, name="on")
    no_kb = _skill(allow=True, name="no-kb")
    kwargs = {
        "skill_id": off.id,
        WIKI_MATERIAL_ACTOR_KEY: external_actor(""),
    }
    chat_kwargs = {
        "system_message_prompt": "base",
        "tools_servers": [],
        "extra_config": {WIKI_MATERIAL_ACTOR_KEY: system_actor("forged", "evil.example")},
    }

    apply_wiki_material_runtime(chat_kwargs, kwargs)

    assert REPLY_SWITCH_OFF in chat_kwargs["system_message_prompt"]
    assert WIKI_MATERIAL_TOOL_NAME not in [tool.get("name") for tool in chat_kwargs["tools_servers"]]
    assert chat_kwargs["extra_config"][WIKI_MATERIAL_ACTOR_KEY] == external_actor("")

    kwargs["skill_id"] = on.id
    kwargs[WIKI_MATERIAL_ACTOR_KEY] = system_actor("alice", "corp.example")
    apply_wiki_material_runtime(chat_kwargs, kwargs)

    assert "save_wiki_material" in chat_kwargs["system_message_prompt"]
    assert any(tool.get("name") == WIKI_MATERIAL_TOOL_NAME for tool in chat_kwargs["tools_servers"])
    assert chat_kwargs["extra_config"][WIKI_MATERIAL_ACTOR_KEY] == system_actor("alice", "corp.example")
    assert chat_kwargs["extra_config"]["skill_id"] == on.id

    kwargs["skill_id"] = no_kb.id
    apply_wiki_material_runtime(chat_kwargs, kwargs)

    assert REPLY_NO_KB in chat_kwargs["system_message_prompt"]
    assert not any(tool.get("name") == WIKI_MATERIAL_TOOL_NAME for tool in chat_kwargs["tools_servers"])


def test_grounded_answer_keeps_a_tool_turn_when_write_is_enabled():
    assert wiki_grounded_uses_single_model_call(force_wiki_grounded=True, allow_wiki_material_write=False) is True
    assert wiki_grounded_uses_single_model_call(force_wiki_grounded=True, allow_wiki_material_write=True) is False
    assert wiki_grounded_uses_single_model_call(force_wiki_grounded=False, allow_wiki_material_write=True) is False


def test_format_chat_kwargs_injects_write_tool_and_keeps_model_calls(monkeypatch):
    from apps.opspilot.services import chat_service

    skill = _skill(_kb("运维知识"), allow=True, name="format-on")
    monkeypatch.setattr(
        chat_service,
        "augment_prompt_with_trace",
        lambda *_args, **_kwargs: ("augmented", [], {"llm_budget": {"used_calls": 0}}),
    )
    monkeypatch.setattr(
        chat_service,
        "load_wiki_budget_config",
        lambda: SimpleNamespace(qa_max_llm_calls=3, qa_max_output_tokens=1024),
    )
    request = {
        "user_message": "请把这条记到知识库",
        "chat_history": [],
        "conversation_window_size": 10,
        "skill_prompt": "你是运维助手",
        "skill_params": [],
        "wiki_kb_ids": [1],
        "force_wiki_grounded": True,
        "temperature": 1,
        "user_id": "u1",
        "skill_type": SkillTypeChoices.KNOWLEDGE_TOOL,
        "skill_id": skill.id,
        WIKI_MATERIAL_ACTOR_KEY: external_actor("forged"),
    }
    model = SimpleNamespace(
        openai_api_base="http://llm",
        openai_api_key="key",
        model_name="model",
        protocol_type="openai",
        vendor_id=None,
        pk=1,
    )

    chat_kwargs, _, _ = chat_service.ChatService.format_chat_server_kwargs(request, model)

    assert "save_wiki_material" in chat_kwargs["system_message_prompt"]
    assert any(tool.get("name") == WIKI_MATERIAL_TOOL_NAME for tool in chat_kwargs["tools_servers"])
    assert chat_kwargs["extra_config"][WIKI_MATERIAL_ACTOR_KEY] == external_actor("forged")
    assert chat_kwargs.get("max_model_calls") != 1

    skill.allow_wiki_material_write = False
    skill.save(update_fields=["allow_wiki_material_write"])
    closed, _, _ = chat_service.ChatService.format_chat_server_kwargs(request, model)
    assert REPLY_SWITCH_OFF in closed["system_message_prompt"]
    assert closed["max_model_calls"] == 1
    assert not any(tool.get("name") == WIKI_MATERIAL_TOOL_NAME for tool in closed.get("tools_servers") or [])


def test_tool_reads_server_actor_and_has_no_user_argument():
    from apps.opspilot.metis.llm.tools.wiki_material.save import save_wiki_material

    user = _user()
    kb = _kb("运维知识")
    skill = _skill(kb)
    assert "username" not in save_wiki_material.args
    assert WIKI_MATERIAL_ACTOR_KEY not in save_wiki_material.args

    with _patch_runner():
        reply = save_wiki_material.func(
            explicit_request=True,
            title="磁盘将满",
            body="根分区连续上涨。",
            knowledge_base_name="",
            config={
                "configurable": {
                    "skill_id": skill.id,
                    WIKI_MATERIAL_ACTOR_KEY: system_actor(user.username, user.domain),
                }
            },
        )

    assert reply == REPLY_SUCCESS
    assert Material.objects.get().knowledge_base_id == kb.id
    assert OperationLog.objects.get().username == user.username


def test_channel_params_keep_server_actor():
    from apps.opspilot.services.skill_channel_chat_service import build_skill_chat_params

    skill = _skill()
    forged = {WIKI_MATERIAL_ACTOR_KEY: system_actor("forged", "evil.example"), "foo": 1}
    external = build_skill_chat_params(
        skill,
        "hi",
        SimpleNamespace(username="im-user", id=None, locale="en"),
        extra=forged,
        wiki_sender_id="ou_real",
    )
    assert external[WIKI_MATERIAL_ACTOR_KEY] == external_actor("ou_real")
    assert external["foo"] == 1

    platform = build_skill_chat_params(
        skill,
        "hi",
        SimpleNamespace(username="alice", domain="corp.example", id=3, locale="zh-CN"),
    )
    assert platform[WIKI_MATERIAL_ACTOR_KEY] == system_actor("alice", "corp.example")

    anonymous = build_skill_chat_params(
        skill,
        "hi",
        SimpleNamespace(username="", id=None, locale="en"),
        wiki_sender_id="",
    )
    assert anonymous[WIKI_MATERIAL_ACTOR_KEY]["mode"] == "external"
    assert anonymous[WIKI_MATERIAL_ACTOR_KEY]["sender_id"] == ""


def test_agent_node_actor_comes_from_caller_identity_only():
    from apps.opspilot.utils.chat_flow_utils.nodes.agent.agent import AgentNode

    class _M2M:
        def values_list(self, *_args, **_kwargs):
            return iter(())

    skill = SimpleNamespace(
        id=9,
        skill_prompt="你是助手",
        skill_params=[],
        skill_packages=[],
        skill_package_params={},
        llm_model_id=1,
        tools=[],
        skill_type="basic",
        team=[1],
        conversation_window_size=10,
        wiki_knowledge_bases=_M2M(),
    )
    node = AgentNode.__new__(AgentNode)
    node.variable_manager = SimpleNamespace(get_variable=lambda *_args, **_kwargs: "")
    params = node._build_llm_params(
        skill,
        "hi",
        {
            "user_id": "u1",
            CALLER_IDENTITY_CONFIG_KEY: {"username": "alice", "domain": "corp.example", "team_id": 1},
            WIKI_MATERIAL_ACTOR_KEY: system_actor("forged", "evil.example"),
        },
    )

    assert params[WIKI_MATERIAL_ACTOR_KEY] == system_actor("alice", "corp.example")

    missing = node._build_llm_params(skill, "hi", {"user_id": "u1"})
    assert missing[WIKI_MATERIAL_ACTOR_KEY]["mode"] == "anonymous"


def test_openai_enrich_uses_the_authenticated_user():
    from apps.opspilot.views.chat_flow import _enrich_openai_params

    user = SimpleNamespace(
        username="alice",
        domain="corp.example",
        group_list=[7],
        is_authenticated=True,
    )
    request = SimpleNamespace(user=user, COOKIES={"current_team": "7"}, api_pass=False)
    params = {WIKI_MATERIAL_ACTOR_KEY: external_actor("forged")}

    _enrich_openai_params(request, user, params)

    assert params[WIKI_MATERIAL_ACTOR_KEY] == system_actor("alice", "corp.example")
    assert params[CALLER_IDENTITY_CONFIG_KEY]["username"] == "alice"
