"""作业执行 SSE 在客户端断开后必须停掉生成器和 JetStream 消费者。"""

import asyncio
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

from django.urls import clear_url_caches, path

from apps.job_mgmt.constants import ExecutionStatus
from apps.job_mgmt.views.execution import JobExecutionViewSet

urlpatterns = []


def _install_view(monkeypatch, view):
    monkeypatch.setattr(sys.modules[__name__], "urlpatterns", [path("resource/", view)])
    clear_url_caches()


def _scope():
    return {
        "type": "http",
        "method": "GET",
        "path": "/resource/",
        "query_string": b"",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1),
        "scheme": "http",
        "http_version": "1.1",
    }


def _application(settings, monkeypatch):
    from apps.core.utils import loader

    settings.MIDDLEWARE = []
    settings.ROOT_URLCONF = __name__
    settings.ALLOWED_HOSTS = ["testserver"]
    monkeypatch.setattr(loader, "preload_language_cache", lambda **kwargs: None)
    monkeypatch.setenv("DB_ENGINE", "postgresql")
    clear_url_caches()
    app = runpy.run_path(str(Path(__file__).resolve().parents[3] / "asgi.py"))["application"]
    return app


def test_job_stream_closes_generator_and_consumer_when_client_disconnects(settings, monkeypatch):
    """离开进行中的 /stream 后不再发出后续事件，JetStream 消费者必须结束。"""
    execution = SimpleNamespace(
        id=7,
        status=ExecutionStatus.RUNNING,
        target_list=[{"target_id": 5, "name": "h1", "ip": "1.1.1.1"}],
        execution_results=[],
    )
    state = {"entered": False, "consumer_closed": False, "subject": None}

    async def jetstream_consumer(filter_subject, idle_timeout=300):
        try:
            state["subject"] = filter_subject
            yield (
                f"job.stream.{execution.id}.5",
                {"stream": "stdout", "line": "alive"},
            )
            state["entered"] = True
            await asyncio.sleep(30)
            yield (
                f"job.stream.{execution.id}.5",
                {"stream": "stdout", "line": "late"},
            )
        finally:
            state["consumer_closed"] = True

    monkeypatch.setattr(
        "apps.job_mgmt.services.execution_stream_service.iter_jetstream_subject",
        jetstream_consumer,
    )
    monkeypatch.setattr("apps.job_mgmt.views.execution.ensure_stream_sync", lambda *args, **kwargs: None)

    def view(request):
        request.user = SimpleNamespace(is_superuser=True, username="testuser", locale="en")
        viewset = JobExecutionViewSet()
        viewset.action = "stream"
        viewset.kwargs = {"pk": execution.id}
        viewset.format_kwarg = None
        viewset.get_object = lambda: execution
        return viewset.stream(request, pk=execution.id)

    _install_view(monkeypatch, view)
    application = _application(settings, monkeypatch)
    calls = {"n": 0}
    release_disconnect = asyncio.Event()

    async def receive():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"type": "http.request", "body": b"", "more_body": False}
        await release_disconnect.wait()
        return {"type": "http.disconnect"}

    async def exercise():
        messages = []

        async def send(message):
            messages.append(message)

        async def disconnect_once_blocked():
            for _ in range(200):
                if state["entered"]:
                    release_disconnect.set()
                    return
                await asyncio.sleep(0.01)
            raise AssertionError("作业流没有进入 JetStream 等待")

        waiter = asyncio.create_task(disconnect_once_blocked())
        try:
            try:
                await asyncio.wait_for(application(_scope(), receive, send), 2)
            except TimeoutError as error:
                raise AssertionError("断开后作业流仍在跑，生成器没有结束") from error
        finally:
            await waiter
        body = b"".join(message.get("body", b"") for message in messages)
        assert b"alive" in body
        assert b"late" not in body
        assert b"[DONE]" not in body

    asyncio.run(exercise())
    assert state["entered"]
    assert state["consumer_closed"]
    assert state["subject"] == f"job.stream.{execution.id}.>"
    assert calls["n"] == 2
