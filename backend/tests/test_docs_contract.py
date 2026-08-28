"""Contratos de publicação e design da documentação pública."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_CSS = ROOT / "docs" / "wiki.css"
DOCS_JS = ROOT / "docs" / "wiki.js"
DOCS_HTML = [
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "api.html",
    ROOT / "docs" / "guia-apresentacao.html",
]


def test_docs_share_land_page_layout_tokens_and_centered_container() -> None:
    """A documentação deve usar a mesma base visual e largura da landing."""
    css = DOCS_CSS.read_text(encoding="utf-8")
    assert "--bg-void: #0e1117;" in css
    assert "--hull-panel: #1f242d;" in css
    assert "--neon-amber: #f7931a;" in css
    assert "width: min(100%, 1240px);" in css
    assert "margin: 0 auto;" in css
    assert "padding: 100px clamp(20px, 4vw, 48px) 80px;" in css
    assert "body.menu-open .wiki { margin-right" not in css


def test_docs_index_menu_is_contextual_and_not_open_by_default() -> None:
    """O índice não deve cobrir a documentação ao abrir a página."""
    javascript = DOCS_JS.read_text(encoding="utf-8")
    assert "toggleMenu(false);" in javascript
    assert "if (window.innerWidth > 900) toggleMenu(true);" not in javascript


def test_public_docs_have_consistent_navigation_and_no_legacy_routes() -> None:
    """Os três HTMLs públicos devem apontar para as superfícies atuais."""
    for html_path in DOCS_HTML:
        html = html_path.read_text(encoding="utf-8")
        assert "wiki.css" in html
        assert "wiki.js" in html
        assert "staking/start" not in html
        assert "staking/cancel" not in html
        assert "mempool-miner-mecha.html" not in html
