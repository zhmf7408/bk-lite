import json
from pathlib import Path


COLLECTOR_CONFIG_DIR = (
    Path(__file__).resolve().parents[2]
    / "node_mgmt"
    / "support-files"
    / "collectors"
)


def test_logstash_based_log_collectors_retry_without_drop_limit():
    collector_files = [
        "Auditbeat.json",
        "Filebeat.json",
        "Packetbeat.json",
        "Winlogbeat.json",
    ]

    for collector_file in collector_files:
        collector_definitions = json.loads(
            (COLLECTOR_CONFIG_DIR / collector_file).read_text(encoding="utf-8")
        )
        for collector_definition in collector_definitions:
            config = collector_definition["default_config"]["nats"]
            assert "output.logstash:" in config
            assert "max_retries: -1" in config
            assert "max_retries: 3" not in config
