import json

from apps.log.utils.query_log import VictoriaMetricsAPI


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
