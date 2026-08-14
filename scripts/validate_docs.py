"""Valida sintaxe básica e links locais da documentação do projeto."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?(?:\[[^]]*])\(([^)\s]+)(?:\s+[^)]*)?\)")


class LinkCollector(HTMLParser):
    """Coleta href e src enquanto confirma que o HTML pode ser analisado."""

    def __init__(self) -> None:
        """Inicializa a lista de referências encontradas."""
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Registra referências de início de tag."""
        del tag
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


def is_external(reference: str) -> bool:
    """Informa se uma referência não deve ser resolvida no filesystem."""
    return reference.startswith(("#", "/", "mailto:", "tel:", "data:")) or bool(
        urlsplit(reference).scheme
    )


def resolve_reference(source: Path, reference: str) -> Path | None:
    """Resolve um link relativo, descartando query e fragmento."""
    if is_external(reference):
        return None
    clean_path = unquote(urlsplit(reference).path)
    if not clean_path:
        return None
    return (source.parent / clean_path).resolve()


def validate_html(path: Path) -> list[str]:
    """Analisa um HTML e devolve seus links."""
    parser = LinkCollector()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.links


def validate_markdown(path: Path) -> list[str]:
    """Extrai links Markdown de um arquivo."""
    return MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))


def main() -> int:
    """Executa todas as validações e retorna código apropriado ao CI."""
    errors: list[str] = []
    checked_links = 0
    html_files = list(ROOT.rglob("*.html"))
    markdown_files = list(ROOT.rglob("*.md"))
    svg_files = list((ROOT / "docs" / "assets").glob("*.svg"))

    ignored_parts = {".git", ".audit-venv", ".venv", "node_modules"}
    html_files = [path for path in html_files if not ignored_parts.intersection(path.parts)]
    markdown_files = [path for path in markdown_files if not ignored_parts.intersection(path.parts)]

    for svg in svg_files:
        try:
            ElementTree.parse(svg)
        except ElementTree.ParseError as exc:
            errors.append(f"SVG inválido {svg.relative_to(ROOT)}: {exc}")

    for source in [*html_files, *markdown_files]:
        try:
            references = (
                validate_html(source) if source.suffix == ".html" else validate_markdown(source)
            )
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"Falha ao ler {source.relative_to(ROOT)}: {exc}")
            continue

        for reference in references:
            target = resolve_reference(source, reference)
            if target is None:
                continue
            checked_links += 1
            if not target.exists():
                errors.append(f"Link quebrado em {source.relative_to(ROOT)}: {reference}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(
        f"Documentação válida: {len(html_files)} HTML, "
        f"{len(markdown_files)} Markdown, {len(svg_files)} SVG, "
        f"{checked_links} links locais."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
