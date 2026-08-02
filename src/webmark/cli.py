from __future__ import annotations

import argparse
import json
import sys

from .archive import PayloadError, ingest_payload, read_payload
from .config import (
    ConfigError,
    RuntimeConfig,
    load_manifest,
    resolve_lexiang_target,
    resolve_raw_site_base_url,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="webmark")
    parser.add_argument("--config", default="config/local.json")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Install or refresh mdFlow configuration")
    init.add_argument("--upgrade-url")
    sub.add_parser("preflight", help="Verify local WebMark configuration")

    ingest = sub.add_parser("ingest", help="Archive WorkBuddy-fetched content")
    ingest.add_argument("--input", required=True, help="Path to payload JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = RuntimeConfig.from_file(args.config)
        if args.command == "init":
            manifest = load_manifest(
                config,
                initialize=args.upgrade_url is None,
                upgrade_url=args.upgrade_url,
            )
        else:
            manifest = load_manifest(config)

        base_url = resolve_raw_site_base_url(config, manifest)
        lexiang = resolve_lexiang_target(config, manifest)
        config.raw_root.mkdir(parents=True, exist_ok=True)

        if args.command == "init":
            _emit({
                "status": "success",
                "manifest_cache": str(config.manifest_cache),
                "raw_site_base_url": base_url,
                "lexiang": lexiang.as_dict(),
            })
            return 0

        if args.command == "preflight":
            _emit({
                "status": "success",
                "raw_root": str(config.raw_root),
                "manifest_cache": str(config.manifest_cache),
                "raw_site_base_url": base_url,
                "lexiang": lexiang.as_dict(),
            })
            return 0

        result = ingest_payload(
            read_payload(args.input),
            raw_root=config.raw_root,
            raw_site_base_url=base_url,
        )
        output: dict[str, object] = result.as_dict()
        output["lexiang"] = lexiang.as_dict()
        _emit(output)
        return 0
    except (ConfigError, PayloadError, OSError, ValueError) as exc:
        _emit({"status": "error", "error": str(exc)}, stream=sys.stderr)
        return 2


def _emit(value: dict[str, object], *, stream=sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2), file=stream)


if __name__ == "__main__":
    raise SystemExit(main())
