"""Valida a Fase 3: cor do boss, loading dinâmico, hull alinhado, game.js.docker fora."""
import json
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8010/"
OUT = "/home/developer/mempool.miner/audit-shots"

JS_CHECK = """
() => {
    const out = {};

    // 3.1: cor do título no sucesso do boss
    const title = document.getElementById('result-title');
    const text = document.getElementById('result-text');
    if (typeof showBossResult === 'function') {
        showBossResult(true, 'BOSS DERROTADO! +50000 sats de loot!');
        out.bossSuccessColor = getComputedStyle(title).color;
        out.bossSuccessTitle = title.innerText;
        out.bossSuccessText = text.innerText;
        // fecha o modal
        const modal = document.getElementById('result-modal');
        if (typeof setModalState === 'function') setModalState(modal, false);
    } else {
        out.bossSuccessColor = 'showBossResult não é global';
    }

    // 3.4: loading dinâmico (checar se a função prepareNextBlock usa WORDS_PER_BLOCK)
    out.wordsPerBlock = (typeof WORDS_PER_BLOCK !== 'undefined') ? WORDS_PER_BLOCK : 'não global';

    // 3.5: hull em 1920px (fórmula alinhada)
    out.hullWidth = getComputedStyle(document.getElementById('grid-wrapper')).width;

    // 3.2: código morto removido
    out.bossWordsRequiredGlobal = (typeof window._bossWordsRequired !== 'undefined') ? 'AINDA EXISTE' : 'removido';

    return out;
}
"""

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)
        data = page.evaluate(JS_CHECK)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        page.screenshot(path=f"{OUT}/f3-validation.png")
        browser.close()

if __name__ == "__main__":
    main()
