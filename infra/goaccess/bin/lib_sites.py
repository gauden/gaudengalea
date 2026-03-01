#!/usr/bin/env python3
"""Minimal parser/validator/renderer for goaccess-sites.yaml."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass


SITE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]+(?:,[A-Za-z0-9.-]+)*$")
CONTAINER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Site:
    site_id: str
    source_host: str
    log_file: str
    container_name: str
    internal_port: int
    enabled: bool


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for idx, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:idx]
    return line


def _parse_scalar(raw_value: str):
    value = raw_value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_key_value(text: str, line_no: int) -> tuple[str, object]:
    if ":" not in text:
        raise ConfigError(f"line {line_no}: expected key: value")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ConfigError(f"line {line_no}: empty key is not allowed")
    parsed_value = _parse_scalar(value)
    return key, parsed_value


def parse_sites_yaml(path: str) -> list[dict[str, object]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as exc:
        raise ConfigError(f"cannot read config: {exc}") from exc

    sites: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    root_seen = False

    for line_no, raw in enumerate(lines, start=1):
        stripped = _strip_comment(raw).rstrip("\n")
        if not stripped.strip():
            continue

        indent = len(stripped) - len(stripped.lstrip(" "))
        text = stripped.strip()

        if not root_seen:
            if indent != 0 or text != "sites:":
                raise ConfigError("line 1+: expected top-level 'sites:' key")
            root_seen = True
            continue

        if indent == 2 and text.startswith("- "):
            if current is not None:
                sites.append(current)
            current = {}
            remainder = text[2:].strip()
            if remainder:
                key, value = _parse_key_value(remainder, line_no)
                current[key] = value
            continue

        if indent == 2 and text == "-":
            if current is not None:
                sites.append(current)
            current = {}
            continue

        if indent == 4:
            if current is None:
                raise ConfigError(f"line {line_no}: key without list item")
            key, value = _parse_key_value(text, line_no)
            current[key] = value
            continue

        raise ConfigError(f"line {line_no}: unsupported structure '{text}'")

    if not root_seen:
        raise ConfigError("missing top-level 'sites:' key")

    if current is not None:
        sites.append(current)

    if not sites:
        raise ConfigError("at least one site entry is required")

    return sites


def validate_sites(path: str) -> list[Site]:
    raw_sites = parse_sites_yaml(path)
    required = {
        "site_id",
        "source_host",
        "log_file",
        "container_name",
        "internal_port",
        "enabled",
    }

    seen_site_ids: set[str] = set()
    seen_ports: set[int] = set()
    out: list[Site] = []

    for idx, item in enumerate(raw_sites, start=1):
        missing = sorted(required.difference(item.keys()))
        if missing:
            raise ConfigError(f"site #{idx}: missing required keys: {', '.join(missing)}")

        extras = sorted(set(item.keys()).difference(required))
        if extras:
            raise ConfigError(f"site #{idx}: unknown keys: {', '.join(extras)}")

        site_id = item["site_id"]
        source_host = item["source_host"]
        log_file = item["log_file"]
        container_name = item["container_name"]
        internal_port = item["internal_port"]
        enabled = item["enabled"]

        if not isinstance(site_id, str) or not SITE_ID_RE.fullmatch(site_id):
            raise ConfigError(
                f"site #{idx}: invalid site_id '{site_id}' (must match {SITE_ID_RE.pattern})"
            )
        if site_id in seen_site_ids:
            raise ConfigError(f"duplicate site_id: {site_id}")
        seen_site_ids.add(site_id)

        if not isinstance(source_host, str) or not HOST_RE.fullmatch(source_host):
            raise ConfigError(f"site #{idx}: invalid source_host '{source_host}'")

        if not isinstance(log_file, str) or not log_file:
            raise ConfigError(f"site #{idx}: log_file must be a non-empty string")
        if not os.path.isabs(log_file):
            raise ConfigError(f"site #{idx}: log_file must be absolute path: {log_file}")
        if not os.path.exists(log_file):
            raise ConfigError(f"site #{idx}: log_file does not exist: {log_file}")

        if not isinstance(container_name, str) or not CONTAINER_RE.fullmatch(container_name):
            raise ConfigError(f"site #{idx}: invalid container_name '{container_name}'")

        if not isinstance(internal_port, int) or not (1 <= internal_port <= 65535):
            raise ConfigError(f"site #{idx}: invalid internal_port '{internal_port}'")
        if internal_port in seen_ports:
            raise ConfigError(f"duplicate internal_port: {internal_port}")
        seen_ports.add(internal_port)

        if not isinstance(enabled, bool):
            raise ConfigError(f"site #{idx}: enabled must be boolean")

        out.append(
            Site(
                site_id=site_id,
                source_host=source_host,
                log_file=log_file,
                container_name=container_name,
                internal_port=internal_port,
                enabled=enabled,
            )
        )

    return out


def render_compose(sites: list[Site]) -> str:
    lines: list[str] = [
        "# GENERATED by bin/reconcile-goaccess.sh from goaccess-sites.yaml",
        "name: goaccess",
        "services:",
    ]

    enabled_sites = [site for site in sites if site.enabled]
    for site in enabled_sites:
        lines.extend(
            [
                f"  {site.container_name}:",
                "    image: allinurl/goaccess:latest",
                f"    container_name: {site.container_name}",
                "    restart: unless-stopped",
                "    command:",
                "      - --log-format=CADDY",
                "      - --real-time-html",
                "      - --output=/report/index.html",
                "      - --addr=0.0.0.0",
                f"      - --port={site.internal_port}",
                f"      - --ws-url=wss://webstats.gaudengalea.com:443/{site.site_id}/ws",
                "      - /logs/access.json",
                "    volumes:",
                f"      - {site.log_file}:/logs/access.json:ro",
                f"      - /home/ubuntu/apps/caddy/data/goaccess/{site.site_id}:/report",
                "    networks:",
                "      - caddy_default",
                "",
            ]
        )

    lines.extend(
        [
            "networks:",
            "  caddy_default:",
            "    external: true",
            "",
        ]
    )

    return "\n".join(lines)


def render_caddy_snippet(sites: list[Site]) -> str:
    lines: list[str] = [
        "# GENERATED by bin/reconcile-goaccess.sh from goaccess-sites.yaml",
        "# Requires Cloudflare trusted proxy handling in Caddy global options.",
        "# Example (global options block):",
        "# {",
        "#   servers {",
        "#     trusted_proxies static 173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18 108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17 162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22",
        "#   }",
        "# }",
        "",
        "webstats.gaudengalea.com {",
        "  # Keep WebSocket handlers before generic site handlers.",
    ]

    enabled_sites = [site for site in sites if site.enabled]
    for site in enabled_sites:
        lines.extend(
            [
                f"  @{site.site_id}_root path /{site.site_id}",
                f"  redir @{site.site_id}_root /{site.site_id}/ 308",
                "",
                f"  @{site.site_id}_ws path /{site.site_id}/ws*",
                f"  handle @{site.site_id}_ws {{",
                f"    uri strip_prefix /{site.site_id}",
                f"    reverse_proxy {site.container_name}:{site.internal_port} {{",
                "      header_up X-Real-IP {http.request.header.CF-Connecting-IP}",
                "      header_up X-Forwarded-For {http.request.header.CF-Connecting-IP}",
                "    }",
                "  }",
                "",
            ]
        )

    for site in enabled_sites:
        lines.extend(
            [
                f"  @{site.site_id} path /{site.site_id}*",
                f"  handle @{site.site_id} {{",
                f"    uri strip_prefix /{site.site_id}",
                f"    root * /data/goaccess/{site.site_id}",
                "    try_files {path} /index.html",
                "    file_server",
                "  }",
                "",
            ]
        )

    lines.extend(
        [
            '  respond "Not Found" 404',
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def _cmd_validate(args: argparse.Namespace) -> int:
    sites = validate_sites(args.config)
    print(f"OK: {len(sites)} site(s) valid")
    return 0


def _cmd_render_compose(args: argparse.Namespace) -> int:
    sites = validate_sites(args.config)
    rendered = render_compose(sites)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    print(f"Rendered compose: {args.output}")
    return 0


def _cmd_list_enabled(args: argparse.Namespace) -> int:
    sites = validate_sites(args.config)
    for site in sites:
        if site.enabled:
            print(f"{site.site_id}\t{site.container_name}\t{site.internal_port}")
    return 0


def _cmd_render_caddy(args: argparse.Namespace) -> int:
    sites = validate_sites(args.config)
    rendered = render_caddy_snippet(sites)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    print(f"Rendered caddy snippet: {args.output}")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GoAccess sites config tools")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate goaccess-sites.yaml")
    p_validate.add_argument("config", help="Path to goaccess-sites.yaml")
    p_validate.set_defaults(func=_cmd_validate)

    p_render = sub.add_parser("render-compose", help="render compose file from config")
    p_render.add_argument("config", help="Path to goaccess-sites.yaml")
    p_render.add_argument("output", help="Path to compose.yaml output")
    p_render.set_defaults(func=_cmd_render_compose)

    p_list = sub.add_parser("list-enabled", help="list enabled sites")
    p_list.add_argument("config", help="Path to goaccess-sites.yaml")
    p_list.set_defaults(func=_cmd_list_enabled)

    p_caddy = sub.add_parser("render-caddy", help="render caddy snippet from config")
    p_caddy.add_argument("config", help="Path to goaccess-sites.yaml")
    p_caddy.add_argument("output", help="Path to caddy snippet output")
    p_caddy.set_defaults(func=_cmd_render_caddy)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
