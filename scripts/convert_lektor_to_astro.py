from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = ROOT / "content"
SRC_CONTENT_ROOT = ROOT / "src" / "content"
PUBLIC_ROOT = ROOT / "public"
ASSETS_STATIC_ROOT = ROOT / "assets" / "static"
WELL_KNOWN_ROOT = ROOT / ".well-known"

SECTION_CONFIGS = {
    "blog": {"title": "Blog", "subtitle": "Writings and Speeches"},
    "lab": {"title": "Lab", "subtitle": None},
    "feed": {"title": "gaudengalea.com — All Updates", "subtitle": "Site-wide feed of recent updates"},
}


@dataclass(frozen=True)
class LektorRecord:
    source_path: Path
    relative_dir: Path
    fields: dict[str, str]


def parse_lektor_record(text: str) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    blocks = normalized.split("\n---\n")
    fields: dict[str, str] = {}

    for block in blocks:
        if not block.strip():
            continue
        lines = block.split("\n")
        head = lines[0]
        if ":" not in head:
            raise ValueError(f"Invalid field header: {head!r}")
        key, value = head.split(":", 1)
        key = key.strip()
        remainder = "\n".join(lines[1:])
        if remainder:
            field_value = value.lstrip() + ("\n" + remainder if value.lstrip() or remainder else "")
        else:
            field_value = value.lstrip()
        fields[key] = field_value.rstrip() + ("\n" if field_value.endswith("\n") else "")

    return fields


def dump_frontmatter(data: dict[str, object]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        elif isinstance(value, str):
            if "\n" in value:
                lines.append(f"{key}: |")
                for part in value.rstrip("\n").split("\n"):
                    lines.append(f"  {part}")
            else:
                escaped = value.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
        else:
            raise TypeError(f"Unsupported frontmatter value for {key}: {type(value)!r}")
    lines.append("---")
    return "\n".join(lines)


def load_record(path: Path) -> LektorRecord:
    return LektorRecord(
        source_path=path,
        relative_dir=path.parent.relative_to(CONTENT_ROOT),
        fields=parse_lektor_record(path.read_text(encoding="utf-8")),
    )


def is_container_record(record: LektorRecord) -> bool:
    rel = record.relative_dir
    model = record.fields.get("_model", "").strip()
    if rel == Path("."):
        return False
    if rel == Path("bio"):
        return False
    if rel.parts[0] == "pub" and rel == Path("pub"):
        return True
    return model in {"listing", "sitefeed"}


def target_collection(record: LektorRecord) -> str:
    rel = record.relative_dir
    if rel == Path(".") or rel == Path("bio") or rel == Path("feed"):
        return "pages"
    return rel.parts[0]


def target_markdown_path(record: LektorRecord) -> Path:
    collection = target_collection(record)
    rel = record.relative_dir
    if collection == "pages":
        slug = "home" if rel == Path(".") else rel.name
        return SRC_CONTENT_ROOT / "pages" / f"{slug}.md"

    section = rel.parts[0]
    tail = list(rel.parts[1:])
    if not tail:
        return SRC_CONTENT_ROOT / section / "_index.md"
    if len(tail) == 1:
        return SRC_CONTENT_ROOT / section / f"{tail[0]}.md"
    return SRC_CONTENT_ROOT / section / Path(*tail[:-1]) / f"{tail[-1]}.md"


def markdown_frontmatter(record: LektorRecord) -> dict[str, object]:
    fields = record.fields
    rel = record.relative_dir
    if rel == Path("."):
        return {
            "title": fields.get("title", "").strip(),
            "summary": fields.get("summary", "").strip() or None,
        }
    if rel in {Path("blog"), Path("lab"), Path("feed")}:
        cfg = SECTION_CONFIGS[rel.name]
        return {
            "title": fields.get("title", "").strip() or cfg["title"],
            "subtitle": fields.get("subtitle", "").strip() or cfg["subtitle"],
        }
    if rel == Path("bio"):
        return {"title": fields.get("title", "").strip() or "Biosketch"}

    result: dict[str, object] = {
        "title": fields.get("title", "").strip(),
        "pub_date": fields.get("pub_date", "").strip() or None,
        "summary": fields.get("summary", "").strip() or None,
        "image": fields.get("image", "").strip() or None,
        "series": fields.get("series", "").strip() or None,
        "draft": False,
    }
    order = fields.get("order", "").strip()
    if order:
        result["order"] = int(order)

    if rel.parts[0] == "pub":
        result["url"] = fields.get("url", "").strip() or None
        result["venue"] = fields.get("venue", "").strip() or None
        result["author"] = fields.get("author", "").strip() or None

    return result


def markdown_body(record: LektorRecord) -> str:
    fields = record.fields
    rel = record.relative_dir
    if rel == Path("."):
        return fields.get("intro", "").lstrip("\n").rstrip() + "\n"
    if rel in {Path("blog"), Path("lab"), Path("feed")}:
        return ""
    return fields.get("body", "").lstrip("\n").rstrip() + "\n"


def write_record(record: LektorRecord) -> None:
    target = target_markdown_path(record)
    target.parent.mkdir(parents=True, exist_ok=True)
    body = markdown_body(record)
    content = dump_frontmatter(markdown_frontmatter(record)) + "\n\n" + body
    target.write_text(content, encoding="utf-8")


def copy_content_assets() -> None:
    for path in CONTENT_ROOT.rglob("*"):
        if path.is_dir() or path.name == "contents.lr" or path.name.startswith("."):
            continue
        relative = path.relative_to(CONTENT_ROOT)
        destination = PUBLIC_ROOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def copy_static_assets() -> None:
    destination = PUBLIC_ROOT / "static"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(ASSETS_STATIC_ROOT, destination)
    for path in destination.rglob(".DS_Store"):
        path.unlink()

    well_known_dest = PUBLIC_ROOT / ".well-known"
    if WELL_KNOWN_ROOT.exists():
        if well_known_dest.exists():
            shutil.rmtree(well_known_dest)
        shutil.copytree(WELL_KNOWN_ROOT, well_known_dest)
        for path in well_known_dest.rglob(".DS_Store"):
            path.unlink()


def write_migration_post() -> None:
    target = SRC_CONTENT_ROOT / "blog" / "moving-from-lektor-to-astro.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """---
title: From Lektor to Astro and Pages CMS
pub_date: 2026-04-08
summary: A note on the decision to move this site from Lektor to Astro, with Pages CMS for lower-friction publishing.
draft: true
---

I have decided to move this site from Lektor to Astro, while keeping its current visual style and public URLs intact.

The motivation is practical. Lektor has served me well, but it adds more overhead than I now want for a personal site. The new stack keeps the site static, preserves the same publishing target, and lowers the friction of creating and editing new content.

The migration preserves the existing sections for writing, publications, coding, and bio material. It also retains the feed, the current styling, and the deployment flow to the production origin host.

On the editorial side, I have adopted Pages CMS as a Git-backed editor. The result is a simpler workflow for drafting and publishing content without abandoning version control.
""",
        encoding="utf-8",
    )


def clean_generated_paths() -> None:
    for path in (SRC_CONTENT_ROOT, PUBLIC_ROOT / "blog", PUBLIC_ROOT / "bio", PUBLIC_ROOT / "lab", PUBLIC_ROOT / "pub", PUBLIC_ROOT / "feed", PUBLIC_ROOT / "favicon.ico", PUBLIC_ROOT / "site.webmanifest", PUBLIC_ROOT / "static", PUBLIC_ROOT / ".well-known"):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def convert() -> None:
    records = [load_record(path) for path in sorted(CONTENT_ROOT.rglob("contents.lr"))]
    if not records:
        raise SystemExit("No Lektor source content found. The one-time migration source tree is no longer present.")
    clean_generated_paths()
    for record in records:
        if is_container_record(record):
            continue
        write_record(record)
    copy_content_assets()
    copy_static_assets()
    write_migration_post()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Lektor content into Astro content collections.")
    parser.add_argument("--check", action="store_true", help="Validate that generated output already exists.")
    args = parser.parse_args()

    if args.check:
        required = [
            SRC_CONTENT_ROOT / "pages" / "home.md",
            SRC_CONTENT_ROOT / "blog",
            SRC_CONTENT_ROOT / "lab",
            SRC_CONTENT_ROOT / "pub",
            PUBLIC_ROOT / "static" / "custom.css",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
        if missing:
            raise SystemExit(f"Missing generated paths: {', '.join(missing)}")
        return

    convert()


if __name__ == "__main__":
    main()
