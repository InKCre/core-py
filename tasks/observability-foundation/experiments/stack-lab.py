"""Five-component synthetic lab, capped at a combined 2 CPU / 4 GiB."""

import json
from pathlib import Path
import subprocess
import sys

from lab import docker, HERE, HOST, IMAGES

PROJECT = "inkcre-o11y-stack-g1-b0a97f7c"
SOCKET = "/tmp/inkcre-o11y-stack-b0a97f7c.sock"
IMAGES = {
  **IMAGES,
  "tempo": "grafana/tempo@sha256:3076b8dcdfb32fd6bc5ccef85e7b7313e6199b9cb84366257fc17ecb696db5fd",  # noqa: E501
  "loki": "grafana/loki@sha256:1107dd5274e0ada47e42472b7a7e71f3b2a2fe878878108f3e2f9e51528f0193",  # noqa: E501
  "prometheus": "prom/prometheus@sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e",  # noqa: E501
  "grafana": "grafana/grafana@sha256:b28bae15e219c998fb0e0424ed724930cc61b1f61fb404d47c862f9a23f9e572",  # noqa: E501
}
PORTS = {34318: 4318, 33200: 3200, 33100: 3100, 39090: 9090, 33001: 3000, 38888: 8888}


def compose():
  exporters = {}
  for name, endpoint in {
    "tempo": "http://tempo:4318",
    "loki": "http://loki:3100/otlp",
    "prometheus": "http://prometheus:9090/api/v1/otlp",
  }.items():
    exporters["otlp_http/" + name] = {
      "endpoint": endpoint,
      "timeout": "2s",
      "retry_on_failure": {
        "initial_interval": "1s",
        "max_interval": "2s",
        "max_elapsed_time": "10s",
      },
      "sending_queue": {"sizer": "bytes", "queue_size": 1048576, "num_consumers": 1},
    }
  collector = {
    "receivers": {"otlp": {"protocols": {"http": {"endpoint": "0.0.0.0:4318"}}}},
    "processors": {
      "memory_limiter": {"check_interval": "1s", "limit_mib": 384, "spike_limit_mib": 64},
      "batch": {"timeout": "1s", "send_batch_size": 128, "send_batch_max_size": 128},
    },
    "exporters": exporters,
    "service": {
      "telemetry": {
        "metrics": {
          "readers": [
            {"pull": {"exporter": {"prometheus": {"host": "0.0.0.0", "port": 8888}}}}
          ]
        }
      },
      "pipelines": {
        signal: {
          "receivers": ["otlp"],
          "processors": ["memory_limiter", "batch"],
          "exporters": ["otlp_http/" + name],
        }
        for signal, name in [
          ("traces", "tempo"),
          ("logs", "loki"),
          ("metrics", "prometheus"),
        ]
      },
    },
  }
  loki = {
    "auth_enabled": False,
    "server": {"http_listen_port": 3100, "log_level": "warn"},
    "common": {
      "instance_addr": "127.0.0.1",
      "path_prefix": "/loki",
      "storage": {
        "filesystem": {"chunks_directory": "/loki/chunks", "rules_directory": "/loki/rules"}
      },
      "replication_factor": 1,
      "ring": {"kvstore": {"store": "inmemory"}},
    },
    "schema_config": {
      "configs": [
        {
          "from": "2024-01-01",
          "store": "tsdb",
          "object_store": "filesystem",
          "schema": "v13",
          "index": {"prefix": "index_", "period": "24h"},
        }
      ]
    },
    "limits_config": {
      "allow_structured_metadata": True,
      "retention_period": "168h",
      "otlp_config": {
        "resource_attributes": {
          "ignore_defaults": True,
          "attributes_config": [
            {
              "action": "index_label",
              "attributes": ["service.name", "inkcre.deployment.id"],
            }
          ],
        }
      },
    },
    "compactor": {
      "working_directory": "/loki/compactor",
      "retention_enabled": True,
      "delete_request_store": "filesystem",
    },
    "analytics": {"reporting_enabled": False},
    "pattern_ingester": {"enabled": False},
  }
  prometheus = {
    "global": {"scrape_interval": "15s"},
    "otlp": {
      "promote_resource_attributes": [
        "service.name",
        "service.instance.id",
        "inkcre.deployment.id",
      ],
      "translation_strategy": "UnderscoreEscapingWithSuffixes",
    },
    "scrape_configs": [
      {"job_name": "collector", "static_configs": [{"targets": ["collector:8888"]}]}
    ],
  }
  datasources = {
    "apiVersion": 1,
    "datasources": [
      {
        "name": "Tempo",
        "type": "tempo",
        "uid": "tempo",
        "url": "http://tempo:3200",
        "access": "proxy",
        "jsonData": {
          "tracesToLogsV2": {
            "datasourceUid": "loki",
            "spanStartTimeShift": "-1m",
            "spanEndTimeShift": "1m",
            "filterByTraceID": True,
            "tags": [{"key": "service.name", "value": "service_name"}],
          }
        },
      },
      {
        "name": "Loki",
        "type": "loki",
        "uid": "loki",
        "url": "http://loki:3100",
        "access": "proxy",
        "jsonData": {
          "derivedFields": [
            {
              "name": "TraceID",
              "matcherType": "label",
              "matcherRegex": "trace_id",
              "url": "$${__value.raw}",
              "datasourceUid": "tempo",
            }
          ]
        },
      },
      {
        "name": "Prometheus",
        "type": "prometheus",
        "uid": "prometheus",
        "url": "http://prometheus:9090",
        "access": "proxy",
        "isDefault": True,
      },
    ],
  }
  dashboard = {
    "uid": "inkcre-o11y-g1",
    "title": "InKCre G1 合成诊断",
    "schemaVersion": 39,
    "time": {"from": "now-1h", "to": "now"},
    "templating": {
      "list": [
        {
          "name": "job",
          "type": "textbox",
          "label": "Job ID",
          "query": "42",
          "current": {"text": "42", "value": "42"},
        }
      ]
    },
    "panels": [
      {
        "id": 1,
        "title": "Job 日志 → 展开 TraceID",
        "type": "logs",
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 10},
        "datasource": {"type": "loki", "uid": "loki"},
        "targets": [
          {
            "refId": "A",
            "expr": '{service_name="inkcre-o11y-synthetic"} | inkcre_job_id="$job"',
          }
        ],
        "options": {"showTime": True, "wrapLogMessage": True, "enableLogDetails": True},
      },
      {
        "id": 2,
        "title": "完成计数（服务聚合，不按 Job 打标签）",
        "type": "stat",
        "gridPos": {"x": 0, "y": 10, "w": 12, "h": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "refId": "A",
            "expr": "sum(last_over_time(inkcre_lab_jobs_total[1h]))",
            "instant": True,
          }
        ],
      },
      {
        "id": 3,
        "title": "合成耗时观测数",
        "type": "stat",
        "gridPos": {"x": 12, "y": 10, "w": 12, "h": 6},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [
          {
            "refId": "A",
            "expr": "sum(last_over_time(inkcre_lab_duration_seconds_count[1h]))",
            "instant": True,
          }
        ],
      },
    ],
  }
  configs = {
    "collector": json.dumps(collector),
    "loki": json.dumps(loki),
    "prometheus": json.dumps(prometheus),
    "tempo": (HERE / "tempo.yaml").read_text(),
    "datasources": json.dumps(datasources),
    "dashboard": json.dumps(dashboard, ensure_ascii=False),
    "dashboards": json.dumps(
      {
        "apiVersion": 1,
        "providers": [
          {
            "name": "task-lab",
            "type": "file",
            "options": {"path": "/var/lib/grafana/task-dashboards"},
          }
        ],
      }
    ),
  }
  services = {}
  for name, cpu, memory, port, path, volume in [
    ("tempo", 0.5, 1024, 33200, "/etc/tempo/lab.yaml", "/var/tempo"),
    ("loki", 0.5, 1024, 33100, "/etc/loki/lab.yaml", "/loki"),
    ("prometheus", 0.35, 768, 39090, "/etc/prometheus/prometheus.yml", "/prometheus"),
    ("grafana", 0.4, 768, 33001, None, "/var/lib/grafana"),
    ("collector", 0.25, 512, 34318, "/etc/otelcol/lab.yaml", None),
  ]:
    service = {
      "image": IMAGES[name],
      "cpus": cpu,
      "mem_limit": f"{memory}m",
      "ports": [f"127.0.0.1:{port}:{PORTS[port]}"],
      "configs": [],
    }
    if volume:
      service["volumes"] = [f"{name}:{volume}"]
    if path:
      service["configs"].append({"source": name, "target": path})
    if name == "tempo":
      service["command"] = ["-target=all", "-config.file=" + path]
    if name == "loki":
      service["command"] = ["-config.file=" + path]
    if name == "prometheus":
      service["command"] = [
        "--config.file=" + path,
        "--web.enable-otlp-receiver",
        "--storage.tsdb.retention.time=30d",
        "--storage.tsdb.retention.size=512MB",
      ]
    if name == "collector":
      service["command"] = ["--config=" + path]
      service["ports"].append("127.0.0.1:38888:8888")
    if name == "grafana":
      # Synthetic loopback lab only; Editor is needed for Explore in Grafana OSS.
      service["environment"] = {
        "GF_AUTH_ANONYMOUS_ENABLED": "true",
        "GF_AUTH_ANONYMOUS_ORG_ROLE": "Editor",
        "GF_AUTH_DISABLE_LOGIN_FORM": "true",
        "GF_ANALYTICS_REPORTING_ENABLED": "false",
        "GF_ANALYTICS_CHECK_FOR_UPDATES": "false",
        "GF_ANALYTICS_CHECK_FOR_PLUGIN_UPDATES": "false",
        "GF_PLUGINS_PREINSTALL_DISABLED": "true",
      }
      service["configs"] = [
        {"source": key, "target": target}
        for key, target in [
          ("datasources", "/etc/grafana/provisioning/datasources/lab.yaml"),
          ("dashboards", "/etc/grafana/provisioning/dashboards/lab.yaml"),
          ("dashboard", "/var/lib/grafana/task-dashboards/lab.json"),
        ]
      ]
    services[name] = service
  return json.dumps(
    {
      "services": services,
      "configs": {
        name: {"content": value.replace("$", "$$")} for name, value in configs.items()
      },
      "volumes": {name: {} for name in ["tempo", "loki", "prometheus", "grafana"]},
    }
  )


def main(action):
  if action == "up":
    print(docker("compose", "-p", PROJECT, "-f", "-", "up", "-d", data=compose()))
    if not Path(SOCKET).exists():
      forwards = [
        part for port in PORTS for part in ["-L", f"127.0.0.1:{port}:127.0.0.1:{port}"]
      ]
      subprocess.run(  # noqa: S603
        [
          "ssh",
          "-M",
          "-S",
          SOCKET,
          "-fNT",
          "-o",
          "BatchMode=yes",
          "-o",
          "ExitOnForwardFailure=yes",
          *forwards,
          HOST,
        ],
        check=True,
      )
  elif action in {"stop", "remove"}:
    args = ["stop"] if action == "stop" else ["down", "--volumes"]
    print(docker("compose", "-p", PROJECT, "-f", "-", *args, data=compose()))
    if Path(SOCKET).exists():
      subprocess.run(["ssh", "-S", SOCKET, "-O", "exit", HOST], check=True)  # noqa: S603
  elif action == "stats":
    print(
      docker(
        "stats",
        "--no-stream",
        "--format",
        "{{json .}}",
        *[
          f"{PROJECT}-{name}-1"
          for name in ["tempo", "loki", "prometheus", "grafana", "collector"]
        ],
      )
    )
  elif action == "logs":
    print(
      docker("compose", "-p", PROJECT, "-f", "-", "logs", "--tail", "20", data=compose())
    )
  else:
    raise SystemExit("Use up, stop, remove, stats, or logs")


if __name__ == "__main__":
  main(sys.argv[1])
