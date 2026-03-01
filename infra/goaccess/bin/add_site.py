#!/usr/bin/env python3
"""Append a site entry to goaccess-sites.yaml with safety checks."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from lib_sites import CONTAINER_RE, HOST_RE, SITE_ID_RE, ConfigError, parse_sites_yaml


def _parse_enabled(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"true", "1", "yes", "y", "on"}:
        return True
    if lowered in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Add a site to goaccess-sites.yaml")
    parser.add_argument("--site-id", required=True, help="URL slug, e.g. powergraph")
    parser.add_argument("--source-host", required=True, help="Observed hostname(s); comma-separated allowed")
    parser.add_argument("--log-file", required=True, help="Absolute host log file path")
    parser.add_argument("--container-name", required=True, help="Stable goaccess container name")
    parser.add_argument("--internal-port", required=True, type=int, help="Unique internal port")
    parser.add_argument("--enabled", type=_parse_enabled, default=True, help="true/false (default: true)")
    parser.add_argument("--allow-missing-log", action="store_true", help="Allow missing log path at add time")
    parser.add_argument("--dry-run", action="store_true", help="Print entry and checks only")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "goaccess-sites.yaml"),
        help="Path to goaccess-sites.yaml",
    )
    return parser


def _validate_new_entry(args: argparse.Namespace, existing: list[dict[str, object]]) -> None:
    if not SITE_ID_RE.fullmatch(args.site_id):
        raise ConfigError(f"invalid site_id '{args.site_id}' (must match {SITE_ID_RE.pattern})")
    if not HOST_RE.fullmatch(args.source_host):
        raise ConfigError(f"invalid source_host '{args.source_host}'")
    if not CONTAINER_RE.fullmatch(args.container_name):
        raise ConfigError(f"invalid container_name '{args.container_name}'")
    if not (1 <= args.internal_port <= 65535):
        raise ConfigError(f"invalid internal_port '{args.internal_port}'")
    if not os.path.isabs(args.log_file):
        raise ConfigError(f"log_file must be absolute path: {args.log_file}")
    if (not args.allow_missing_log) and (not os.path.exists(args.log_file)):
        raise ConfigError(f"log_file does not exist: {args.log_file}")

    for entry in existing:
        existing_site_id = str(entry.get("site_id", ""))
        existing_container = str(entry.get("container_name", ""))
        existing_port = int(entry.get("internal_port", 0))

        if existing_site_id == args.site_id:
            raise ConfigError(f"duplicate site_id: {args.site_id}")
        if existing_container == args.container_name:
            raise ConfigError(f"duplicate container_name: {args.container_name}")
        if existing_port == args.internal_port:
            raise ConfigError(f"duplicate internal_port: {args.internal_port}")


def _entry_yaml(args: argparse.Namespace) -> str:
    enabled = "true" if args.enabled else "false"
    return (
        f"  - site_id: {args.site_id}\n"
        f"    source_host: {args.source_host}\n"
        f"    log_file: {args.log_file}\n"
        f"    container_name: {args.container_name}\n"
        f"    internal_port: {args.internal_port}\n"
        f"    enabled: {enabled}\n"
    )


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: config file not found: {config_path}")
        return 1

    try:
        existing = parse_sites_yaml(str(config_path))
        _validate_new_entry(args, existing)
    except ConfigError as exc:
        print(f"ERROR: {exc}")
        return 1

    entry = _entry_yaml(args)
    if args.dry_run:
        print("Dry run OK. Entry to append:\n")
        print(entry, end="")
        return 0

    current = config_path.read_text(encoding="utf-8")
    if not current.endswith("\n"):
        current += "\n"

    config_path.write_text(current + entry, encoding="utf-8")

    print(f"Added site '{args.site_id}' to {config_path}")
    print("Next steps:")
    print("1. ./bin/validate-sites.sh ./goaccess-sites.yaml")
    print("2. Sync to molly and run ./bin/reconcile-goaccess.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
