from pathlib import Path

from scripts.convert_lektor_to_astro import (
    LektorRecord,
    markdown_body,
    markdown_frontmatter,
    parse_lektor_record,
    target_markdown_path,
)


def make_record(relative_dir: str, fields: dict[str, str]) -> LektorRecord:
    return LektorRecord(
        source_path=Path("/tmp") / relative_dir / "contents.lr",
        relative_dir=Path(relative_dir),
        fields=fields,
    )


def test_parse_lektor_record_preserves_multiline_body() -> None:
    parsed = parse_lektor_record(
        "_model: blog-post\n---\ntitle: Example\n---\nsummary: Short summary\n---\nbody:\n\n## Heading\n\nParagraph.\n"
    )

    assert parsed["_model"] == "blog-post"
    assert parsed["title"] == "Example"
    assert parsed["summary"] == "Short summary"
    assert "## Heading" in parsed["body"]
    assert parsed["body"].rstrip().endswith("Paragraph.")


def test_blog_frontmatter_maps_expected_fields() -> None:
    record = make_record(
        "blog/example-post",
        {
            "title": "Example",
            "pub_date": "2026-04-08",
            "summary": "Summary",
            "image": "cover.jpg",
            "series": "Series",
            "order": "2",
            "body": "\nBody\n",
        },
    )

    frontmatter = markdown_frontmatter(record)

    assert frontmatter == {
        "title": "Example",
        "pub_date": "2026-04-08",
        "summary": "Summary",
        "image": "cover.jpg",
        "series": "Series",
        "draft": False,
        "order": 2,
    }


def test_publication_frontmatter_includes_author_and_venue() -> None:
    record = make_record(
        "pub/pmid123",
        {
            "title": "Paper",
            "pub_date": "2025-05-01",
            "venue": "Journal",
            "url": "https://example.com",
            "author": "**Author**",
            "body": "\nAbstract\n",
        },
    )

    frontmatter = markdown_frontmatter(record)

    assert frontmatter["venue"] == "Journal"
    assert frontmatter["author"] == "**Author**"
    assert frontmatter["url"] == "https://example.com"


def test_target_markdown_path_preserves_nested_blog_slugs() -> None:
    record = make_record(
        "blog/pyladies-pacman-and-public-health/community-at-the-heart",
        {"title": "Child"},
    )

    path = target_markdown_path(record)

    assert path.as_posix().endswith(
        "src/content/blog/pyladies-pacman-and-public-health/community-at-the-heart.md"
    )


def test_home_body_uses_intro_field() -> None:
    record = make_record(
        ".",
        {
            "title": "Home",
            "intro": "\n# Hello\n",
        },
    )

    assert markdown_body(record) == "# Hello\n"
