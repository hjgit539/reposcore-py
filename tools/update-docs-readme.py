from pathlib import Path

DOCS_DIR = Path("docs")
README_PATH = DOCS_DIR / "README.md"

START_MARKER = "<!-- DOCS_LIST_START -->"
END_MARKER = "<!-- DOCS_LIST_END -->"

EXCLUDED_FILES = {"README.md"}


def extract_title(path: Path) -> str:
    """Return the first top-level markdown title from a document."""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()

        if stripped.startswith("# ") and not stripped.startswith("## "):
            return stripped.removeprefix("# ").strip()

    return path.stem


def collect_docs() -> list[Path]:
    """Collect markdown documents that should appear in docs/README.md."""
    return sorted(
        path
        for path in DOCS_DIR.glob("*.md")
        if path.name not in EXCLUDED_FILES
    )


def build_docs_list() -> str:
    """Build the markdown document list from docs/*.md files."""
    rows = []

    for path in collect_docs():
        title = extract_title(path)
        rows.append(f"* `{path.name}`: {title}")

    return "\n".join(rows)


def build_docs_section() -> str:
    """Build the managed docs list section."""
    docs_list = build_docs_list()

    return (
        "# 문서 목록\n\n"
        f"{START_MARKER}\n"
        f"{docs_list}\n"
        f"{END_MARKER}\n"
    )


def replace_managed_section(readme_text: str, docs_section: str) -> str:
    """Replace existing managed docs list section in docs/README.md."""
    if START_MARKER in readme_text and END_MARKER in readme_text:
        start_index = readme_text.index(START_MARKER)
        end_index = readme_text.index(END_MARKER) + len(END_MARKER)

        before = readme_text[:start_index]
        after = readme_text[end_index:]

        docs_list = build_docs_list()

        return (
            before
            + START_MARKER
            + "\n"
            + docs_list
            + "\n"
            + END_MARKER
            + after
        )

    heading = "# 문서 목록"

    if heading in readme_text:
        heading_index = readme_text.index(heading)
        return readme_text[:heading_index] + docs_section

    separator = "\n\n" if readme_text.endswith("\n") else "\n\n"
    return readme_text + separator + docs_section


def update_readme() -> None:
    """Update docs/README.md with the current docs/*.md list."""
    if not README_PATH.exists():
        raise FileNotFoundError(f"{README_PATH} 파일을 찾을 수 없습니다.")

    readme_text = README_PATH.read_text(encoding="utf-8")
    docs_section = build_docs_section()
    updated_text = replace_managed_section(readme_text, docs_section)

    README_PATH.write_text(updated_text, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
    print(f"Updated {README_PATH}")