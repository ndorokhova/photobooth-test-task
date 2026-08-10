"""Prepare a MkDocs-friendly copy of the final Obsidian notes.

The source notes in ../content are never modified.  Obsidian wiki links and
embeds are converted only in the generated docs directory.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import quote


PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "content"
DOCS = PROJECT / "docs"


def anchor(value: str) -> str:
    """Make a stable URL fragment for headings written in Russian."""
    value = value.strip().lower()
    value = re.sub(r"[^\w\-\s]", "", value, flags=re.UNICODE)
    return quote(re.sub(r"[\s_]+", "-", value).strip("-"))


def target_url(target: str) -> str:
    target = target.replace("\\|", "|").strip()
    if target.startswith("#"):
        return "#" + anchor(target[1:])

    file_name, separator, fragment = target.partition("#")
    # MkDocs resolves links between source .md files and rewrites them for the
    # published site. Non-Markdown source files (for example BPMN) are copied
    # as downloadable attachments.
    attachment_suffixes = {".bpmn", ".dbml", ".puml"}
    is_attachment = any(file_name.lower().endswith(suffix) for suffix in attachment_suffixes)
    path = quote(file_name if is_attachment else file_name + ".md")
    return path + ("#" + anchor(fragment) if separator else "")


def convert(text: str) -> str:
    # Obsidian accepts headings and bullet lists immediately after other blocks.
    # Standard Markdown needs a separating blank line; without it MkDocs renders
    # markers such as ### and - as literal text (especially after tables).
    text = re.sub(r"(?m)([^\n])\n(#{1,6}\s)", r"\1\n\n\2", text)
    text = re.sub(r"(?m)([^\n])\n(-\s)", r"\1\n\n\2", text)

    # Obsidian block identifiers become normal HTML anchors.
    text = re.sub(r"\s\^([\w-]+)(?=\s|$)", r' <a id="\1"></a>', text)

    def image(match: re.Match[str]) -> str:
        target = match.group(1).replace("\\|", "|")
        path, separator, width = target.partition("|")
        # MkDocs serves each top-level note from its own directory, therefore
        # assets stored at docs/ root need one parent-directory step.
        src = quote("../" + path)
        css_class = ' class="zoomable-diagram"' if Path(path).name.startswith("BPMN_") else ""
        if separator and width.isdigit():
            return f'<img src="{src}" alt="" width="{width}">'
        return f'<img{css_class} src="{src}" alt="{Path(path).stem}">'

    text = re.sub(r"!\[\[([^\]]+)\]\]", image, text)

    def link(match: re.Match[str]) -> str:
        content = match.group(1).replace("\\|", "|")
        target, separator, label = content.partition("|")
        label = label if separator else target.split("#", 1)[0]
        return f'[{label}]({target_url(target)})'

    return re.sub(r"(?<!!)\[\[([^\]]+)\]\]", link, text)


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Source folder not found: {SOURCE}")
    if DOCS.exists():
        shutil.rmtree(DOCS)
    shutil.copytree(SOURCE, DOCS, ignore=shutil.ignore_patterns("*.md"))

    for source_file in SOURCE.glob("*.md"):
        (DOCS / source_file.name).write_text(
            convert(source_file.read_text(encoding="utf-8")), encoding="utf-8"
        )

    styles = DOCS / "stylesheets"
    styles.mkdir()
    (styles / "extra.css").write_text(
        "[data-md-color-scheme=\"default\"] {\n"
        "  --md-primary-fg-color: #D16002;\n"
        "  --md-primary-fg-color--light: #eda66d;\n"
        "  --md-primary-fg-color--dark: #9e4600;\n"
        "  --md-accent-fg-color: #9e4600;\n"
        "}\n\n"
        "img { max-width: 100%; height: auto; }\n"
        ".md-typeset table:not([class]) { display: table; }\n"
        ".md-typeset h1 + p { margin-top: -1.2rem; }\n"
        ".md-typeset h1 .headerlink { display: none; }\n"
        ".md-nav--primary > .md-nav__title { display: none; }\n"
        ".zoomable-diagram { cursor: zoom-in; }\n"
        ".image-lightbox {\n"
        "  align-items: flex-start; background: rgb(0 0 0 / 78%); cursor: zoom-out;\n"
        "  display: flex; inset: 0; justify-content: flex-start; overflow: auto; padding: 2rem;\n"
        "  position: fixed; z-index: 1000;\n"
        "}\n"
        ".image-lightbox img {\n"
        "  cursor: default; max-height: none; max-width: none; width: 1800px;\n"
        "}\n",
        encoding="utf-8",
    )

    scripts = DOCS / "javascripts"
    scripts.mkdir()
    (scripts / "image-zoom.js").write_text(
        "document.addEventListener('DOMContentLoaded', () => {\n"
        "  document.querySelectorAll('.zoomable-diagram').forEach((image) => {\n"
        "    image.addEventListener('click', () => {\n"
        "      const overlay = document.createElement('div');\n"
        "      overlay.className = 'image-lightbox';\n"
        "      const enlarged = image.cloneNode();\n"
        "      overlay.append(enlarged);\n"
        "      const close = () => overlay.remove();\n"
        "      overlay.addEventListener('click', (event) => { if (event.target === overlay) close(); });\n"
        "      document.addEventListener('keydown', function onKey(event) {\n"
        "        if (event.key === 'Escape') { close(); document.removeEventListener('keydown', onKey); }\n"
        "      });\n"
        "      document.body.append(overlay);\n"
        "    });\n"
        "  });\n"
        "});\n",
        encoding="utf-8",
    )

    (DOCS / "index.md").write_text(
        "# Тестовое задание\n\n"
        "Документация к сценарию отправки фотографии на электронную почту "
        "в приложении фотокиоска.\n\n"
        "Начните с [оглавления](00. Оглавление.md).\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
