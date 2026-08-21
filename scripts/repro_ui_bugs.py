"""Reproduz os bugs de layout da UI do Mempool Miner.

Abre a UI real (http://127.0.0.1:8010) em vários viewports, captura
screenshots e inspeciona estilos computados para confirmar:
  Bug 1: lista de palavras (word bank) não ajusta no bloco
  Bug 2: boss-hud sobreposto ao painel de palavras fora de tela cheia
"""
import json
import sys

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8010/"
OUT = "/home/developer/mempool.miner/audit-shots"

import os
os.makedirs(OUT, exist_ok=True)

VIEWPORTS = [
    ("1440x900", 1440, 900),
    ("1024x768", 1024, 768),
    ("1920x1080", 1920, 1080),
    ("768x1024", 768, 1024),
]

JS_INSPECT = """
() => {
    const out = {};
    const q = (sel) => document.querySelector(sel);
    const rect = (el) => {
        if (!el) return null;
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {
            x: Math.round(r.x), y: Math.round(r.y),
            w: Math.round(r.width), h: Math.round(r.height),
            display: cs.display, position: cs.position,
            zIndex: cs.zIndex, overflow: cs.overflow,
            visibility: cs.visibility,
        };
    };
    out.viewport = { w: innerWidth, h: innerHeight };
    out.wordGrid = rect(q('#word-grid'));
    out.gridHull = rect(q('#grid-wrapper'));
    out.bossHud = rect(q('#boss-hud'));
    out.bossHudClasses = q('#boss-hud') ? q('#boss-hud').className : null;
    out.txList = rect(q('#tx-list-container'));
    out.tabJogo = rect(q('#tab-jogo'));
    out.sidebar = rect(q('.sidebar-right'));
    // quantas células na grade
    out.cellCount = document.querySelectorAll('#word-grid .cell').length;
    // cell-size efetivo
    const cell = q('#word-grid .cell');
    out.cellSize = cell ? getComputedStyle(cell).width : null;
    // .hidden resolve?
    const hiddenTest = q('.hidden');
    out.hiddenExample = hiddenTest ? getComputedStyle(hiddenTest).display : 'none-found';
    // variáveis CSS
    const rs = getComputedStyle(document.documentElement);
    out.varHighFee = rs.getPropertyValue('--high-fee').trim() || 'UNDEFINED';
    out.varGoldenHash = rs.getPropertyValue('--golden-hash').trim() || 'UNDEFINED';
    out.varCellSize = rs.getPropertyValue('--cell-size').trim() || 'UNDEFINED';
    return out;
}
"""

def main():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        for name, w, h in VIEWPORTS:
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
            # espera o jogo tentar carregar (WS + catalog)
            page.wait_for_timeout(6000)
            shot = f"{OUT}/ui-{name}.png"
            page.screenshot(path=shot, full_page=False)
            try:
                data = page.evaluate(JS_INSPECT)
            except Exception as e:
                data = {"error": str(e)}
            results[name] = data
            print(f"=== {name} ===")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            page.close()
        browser.close()
    with open(f"{OUT}/inspect.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("DONE")

if __name__ == "__main__":
    main()
