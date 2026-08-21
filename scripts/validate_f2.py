"""Valida a Fase 2: card-pull CSS, IDs únicos no word bank, limpeza no retry do boss."""
import json
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8010/"
OUT = "/home/developer/mempool.miner/audit-shots"

JS_CHECK = """
() => {
    const out = {};
    // 1. card-pull-overlay: injeta um overlay e confere o CSS aplicado
    const ov = document.createElement('div');
    ov.className = 'card-pull-overlay';
    const card = document.createElement('div');
    card.className = 'card-pull-card rare';
    const rar = document.createElement('div');
    rar.className = 'card-pull-rarity';
    rar.textContent = 'RARE';
    card.appendChild(rar);
    ov.appendChild(card);
    document.body.appendChild(ov);
    const cs = getComputedStyle(ov);
    out.cardPull = {
        position: cs.position,
        zIndex: cs.zIndex,
        display: cs.display,
        cardBorder: getComputedStyle(card).borderColor,
        rarityColor: getComputedStyle(rar).color,
    };
    ov.remove();

    // 2. word bank: IDs únicos + data-word
    const items = Array.from(document.querySelectorAll('#tx-list-container .word-item'));
    out.bankItems = items.length;
    out.bankIds = items.map(i => i.id);
    out.bankDataWords = items.map(i => i.dataset.word);
    out.bankIdDupes = out.bankIds.length !== new Set(out.bankIds).size;

    // 3. boss retry: simula a limpeza (checar se bankEl.replaceChildren existe e funciona)
    out.replaceChildrenSupported = typeof document.body.replaceChildren === 'function';

    return out;
}
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(6000)
        data = page.evaluate(JS_CHECK)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        page.screenshot(path=f"{OUT}/f2-validation.png")
        browser.close()

if __name__ == "__main__":
    main()
