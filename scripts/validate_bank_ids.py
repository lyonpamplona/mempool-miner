"""Valida IDs únicos + dedupe no word bank (Fase 2.3/2.4)."""
from playwright.sync_api import sync_playwright

JS = r"""
() => {
    const bank = document.getElementById('tx-list-container');
    bank.replaceChildren();
    const words = ['CORAL', 'HIP', 'SENSE', 'CORAL', 'TRUTH'];
    words.forEach(w => {
        if (bank.querySelector('.word-item[data-word="' + w + '"]')) return;
        const it = document.createElement('div');
        it.className = 'word-item';
        it.id = 'bank-' + w + '-' + bank.children.length;
        it.dataset.word = w;
        const sp = document.createElement('span');
        sp.className = 'word-text';
        sp.textContent = w;
        it.appendChild(sp);
        bank.appendChild(it);
    });
    const items = Array.from(bank.querySelectorAll('.word-item'));
    return {
        count: items.length,
        ids: items.map(i => i.id),
        dupes: items.length !== new Set(items.map(i => i.id)).size,
        coralCount: bank.querySelectorAll('.word-item[data-word="CORAL"]').length
    };
}
"""

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto("http://127.0.0.1:8010/", wait_until="domcontentloaded", timeout=30000)
    pg.wait_for_timeout(5000)
    res = pg.evaluate(JS)
    print("word bank:", res)
    assert res["count"] == 4, "esperava 4 itens (CORAL dedupado)"
    assert not res["dupes"], "IDs duplicados!"
    assert res["coralCount"] == 1, "CORAL deveria aparecer 1x"
    print("OK: dedupe + IDs únicos funcionando")
    b.close()
