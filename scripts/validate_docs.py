"""Valida sintaxe básica e links locais da documentação do projeto."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"!?(?:\[[^]]*])\(([^)\s]+)(?:\s+[^)]*)?\)")
IGNORED_PARTS = {
    ".git",
    ".audit-venv",
    ".venv",
    "node_modules",
    "internal-docs",
    "prototypes",
}
PUBLIC_SITE_FILES = {
    (ROOT / "docs" / "index.html").resolve(),
    (ROOT / "docs" / "api.html").resolve(),
    (ROOT / "guia-apresentacao.html").resolve(),
}


class LinkCollector(HTMLParser):
    """Coleta href e src enquanto confirma que o HTML pode ser analisado."""

    def __init__(self) -> None:
        """Inicializa a lista de referências encontradas."""
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Registra referências de início de tag."""
        del tag
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)
            if name == "id" and value:
                self.ids.append(value)


def is_external(reference: str) -> bool:
    """Informa se uma referência não deve ser resolvida no filesystem."""
    return reference.startswith(("#", "mailto:", "tel:", "data:")) or bool(
        urlsplit(reference).scheme
    )


def resolve_public_route(reference: str) -> Path:
    """Mapeia as rotas absolutas do artefato público para seus fontes."""
    clean_path = unquote(urlsplit(reference).path)
    normalized = clean_path.rstrip("/") or "/"
    routes = {
        "/": ROOT / "docs" / "index.html",
        "/api": ROOT / "docs" / "api.html",
        "/apresentacao": ROOT / "guia-apresentacao.html",
        "/site.css": ROOT / "docs" / "site.css",
    }
    if normalized in routes:
        return routes[normalized].resolve()
    if normalized.startswith("/assets/"):
        return (ROOT / "docs" / normalized.removeprefix("/")).resolve()
    return (ROOT / "__rota_publica_inexistente__" / normalized.removeprefix("/")).resolve()


def resolve_reference(source: Path, reference: str) -> Path | None:
    """Resolve um link relativo, descartando query e fragmento."""
    if is_external(reference):
        return None
    clean_path = unquote(urlsplit(reference).path)
    if not clean_path:
        return None
    if clean_path.startswith("/"):
        if source.resolve() in PUBLIC_SITE_FILES:
            return resolve_public_route(reference)
        if source.is_relative_to(ROOT / "frontend"):
            if clean_path.startswith(("/api/", "/ws/")):
                return None
            return (ROOT / "frontend" / clean_path.removeprefix("/")).resolve()
        return None
    return (source.parent / clean_path).resolve()


def validate_html(path: Path) -> LinkCollector:
    """Analisa um HTML e devolve links e IDs."""
    parser = LinkCollector()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


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
    svg_files.extend((ROOT / "frontend" / "icons").glob("*.svg"))
    manifest_files = list(ROOT.rglob("*.webmanifest"))

    html_files = [
        path
        for path in html_files
        if not IGNORED_PARTS.intersection(path.parts) and not path.name.startswith("prototipo-")
    ]
    markdown_files = [path for path in markdown_files if not IGNORED_PARTS.intersection(path.parts)]
    manifest_files = [path for path in manifest_files if not IGNORED_PARTS.intersection(path.parts)]

    for svg in svg_files:
        try:
            ElementTree.parse(svg)
        except ElementTree.ParseError as exc:
            errors.append(f"SVG inválido {svg.relative_to(ROOT)}: {exc}")

    for manifest_path in manifest_files:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"Manifest inválido {manifest_path.relative_to(ROOT)}: {exc}")
            continue
        for field in ("name", "short_name", "start_url", "scope", "display", "icons"):
            if not manifest.get(field):
                errors.append(f"Manifest sem {field}: {manifest_path.relative_to(ROOT)}")
        for icon in manifest.get("icons", []):
            if not isinstance(icon, dict) or not isinstance(icon.get("src"), str):
                errors.append(f"Ícone inválido no manifest: {manifest_path.relative_to(ROOT)}")
                continue
            icon_target = (manifest_path.parent / icon["src"]).resolve()
            if not icon_target.exists():
                errors.append(
                    f"Ícone ausente no manifest {manifest_path.relative_to(ROOT)}: {icon['src']}"
                )

    for source in [*html_files, *markdown_files]:
        try:
            if source.suffix == ".html":
                parser = validate_html(source)
                references = parser.links
                duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
                if duplicate_ids:
                    errors.append(
                        f"IDs duplicados em {source.relative_to(ROOT)}: {', '.join(duplicate_ids)}"
                    )
                for reference in references:
                    if reference.startswith("#") and reference[1:] not in parser.ids:
                        errors.append(
                            f"Âncora quebrada em {source.relative_to(ROOT)}: {reference}"
                        )
            else:
                references = validate_markdown(source)
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
        f"{len(manifest_files)} manifest, "
        f"{checked_links} links locais."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
