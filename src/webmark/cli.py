from __future__ import annotations

import argparse
import json
import sys

from .archive import PayloadError, ingest_payload, read_payload
from .config import ConfigError, integration_targets, load_effective_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="webmark")
    parser.add_argument("--config", default="config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Install or explicitly refresh remote configuration")
    init.add_argument("--upgrade-url")
    sub.add_parser("config", help="Print resolved non-secret settings for the Agent")
    sub.add_parser("preflight", help="Validate configuration and local storage")

    ingest = sub.add_parser("ingest", help="Archive Agent-fetched content")
    ingest.add_argument("--input", required=True, help="Path to payload JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        effective = load_effective_config(
            args.config,
            initialize=args.command == "init",
            upgrade_url=getattr(args, "upgrade_url", None),
        )

        if args.command == "init":
            _emit(_config_result(effective))
            return 0

        if args.command == "config":
            _emit(_config_result(effective))
            return 0

        raw_root = effective.resolved_raw_root()
        raw_root.mkdir(parents=True, exist_ok=True)

        if args.command == "preflight":
            result = _config_result(effective)
            result["raw_root_writable"] = raw_root.exists() and raw_root.is_dir()
            _emit(result)
            return 0

        archive = ingest_payload(
            read_payload(args.input),
            config=effective,
        )
        output: dict[str, object] = archive.as_dict()
        output["targets"] = integration_targets(effective.settings)
        output["response"] = effective.settings.get("response") or {}
        _emit(output)
        return 0
    except (ConfigError, PayloadError, OSError, ValueError) as exc:
        _emit({"status": "error", "error": str(exc)}, stream=sys.stderr)
        return 2


def _config_result(effective) -> dict[str, object]:
    return {
        "status": "success",
        "source_mode": effective.source_mode,
        "cache_path": str(effective.cache_path) if effective.cache_path else None,
        "settings": effective.agent_view(),
    }


def _emit(value: dict[str, object], *, stream=sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
