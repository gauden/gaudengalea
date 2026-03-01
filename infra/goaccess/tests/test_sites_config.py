from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_DIR = Path(__file__).resolve().parents[1]
BIN_DIR = PROJECT_DIR / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

import lib_sites  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_rejects_duplicate_site_id(tmp_path: Path) -> None:
    log1 = tmp_path / "a.json"
    log2 = tmp_path / "b.json"
    log1.write_text("{}", encoding="utf-8")
    log2.write_text("{}", encoding="utf-8")
    cfg = tmp_path / "sites.yaml"

    _write(
        cfg,
        f"""sites:
  - site_id: powergraph
    source_host: powergraph.gaudengalea.com
    log_file: {log1}
    container_name: powergraph-goaccess-1
    internal_port: 7890
    enabled: true
  - site_id: powergraph
    source_host: foo.gaudengalea.com
    log_file: {log2}
    container_name: foo-goaccess
    internal_port: 7891
    enabled: true
""",
    )

    with pytest.raises(lib_sites.ConfigError, match="duplicate site_id"):
        lib_sites.validate_sites(str(cfg))


def test_rejects_duplicate_internal_port(tmp_path: Path) -> None:
    log1 = tmp_path / "a.json"
    log2 = tmp_path / "b.json"
    log1.write_text("{}", encoding="utf-8")
    log2.write_text("{}", encoding="utf-8")
    cfg = tmp_path / "sites.yaml"

    _write(
        cfg,
        f"""sites:
  - site_id: powergraph
    source_host: powergraph.gaudengalea.com
    log_file: {log1}
    container_name: powergraph-goaccess
    internal_port: 7890
    enabled: true
  - site_id: second-site
    source_host: second.gaudengalea.com
    log_file: {log2}
    container_name: second-goaccess
    internal_port: 7890
    enabled: false
""",
    )

    with pytest.raises(lib_sites.ConfigError, match="duplicate internal_port"):
        lib_sites.validate_sites(str(cfg))


def test_rejects_missing_log_file(tmp_path: Path) -> None:
    cfg = tmp_path / "sites.yaml"
    missing = tmp_path / "missing.json"

    _write(
        cfg,
        f"""sites:
  - site_id: powergraph
    source_host: powergraph.gaudengalea.com
    log_file: {missing}
    container_name: powergraph-goaccess
    internal_port: 7890
    enabled: true
""",
    )

    with pytest.raises(lib_sites.ConfigError, match="log_file does not exist"):
        lib_sites.validate_sites(str(cfg))


def test_render_compose_includes_only_enabled(tmp_path: Path) -> None:
    log1 = tmp_path / "a.json"
    log2 = tmp_path / "b.json"
    log1.write_text("{}", encoding="utf-8")
    log2.write_text("{}", encoding="utf-8")
    cfg = tmp_path / "sites.yaml"

    _write(
        cfg,
        f"""sites:
  - site_id: powergraph
    source_host: powergraph.gaudengalea.com
    log_file: {log1}
    container_name: powergraph-goaccess
    internal_port: 7890
    enabled: true
  - site_id: hidden-site
    source_host: hidden.gaudengalea.com
    log_file: {log2}
    container_name: hidden-goaccess
    internal_port: 7891
    enabled: false
""",
    )

    sites = lib_sites.validate_sites(str(cfg))
    compose = lib_sites.render_compose(sites)

    assert "powergraph-goaccess" in compose
    assert "hidden-goaccess" not in compose
    assert "wss://webstats.gaudengalea.com:443/powergraph/ws" in compose


def test_render_caddy_includes_only_enabled(tmp_path: Path) -> None:
    log1 = tmp_path / "a.json"
    log2 = tmp_path / "b.json"
    log1.write_text("{}", encoding="utf-8")
    log2.write_text("{}", encoding="utf-8")
    cfg = tmp_path / "sites.yaml"

    _write(
        cfg,
        f"""sites:
  - site_id: powergraph
    source_host: powergraph.gaudengalea.com
    log_file: {log1}
    container_name: powergraph-goaccess
    internal_port: 7890
    enabled: true
  - site_id: hidden-site
    source_host: hidden.gaudengalea.com
    log_file: {log2}
    container_name: hidden-goaccess
    internal_port: 7891
    enabled: false
""",
    )

    sites = lib_sites.validate_sites(str(cfg))
    snippet = lib_sites.render_caddy_snippet(sites)

    assert "@powergraph_root path /powergraph" in snippet
    assert "redir @powergraph_root /powergraph/ 308" in snippet
    assert "@powergraph_ws path /powergraph/ws*" in snippet
    assert "root * /data/goaccess/powergraph" in snippet
    assert "try_files {path} /index.html" in snippet
    assert "file_server" in snippet
    assert "reverse_proxy powergraph-goaccess:7890" in snippet
    assert "hidden-site" not in snippet
    assert "hidden-goaccess" not in snippet


def test_accepts_comma_separated_source_host(tmp_path: Path) -> None:
    log1 = tmp_path / "a.json"
    log1.write_text("{}", encoding="utf-8")
    cfg = tmp_path / "sites.yaml"

    _write(
        cfg,
        f"""sites:
  - site_id: blog
    source_host: gaudengalea.com,www.gaudengalea.com
    log_file: {log1}
    container_name: blog-goaccess
    internal_port: 7891
    enabled: true
""",
    )

    sites = lib_sites.validate_sites(str(cfg))
    assert sites[0].source_host == "gaudengalea.com,www.gaudengalea.com"
