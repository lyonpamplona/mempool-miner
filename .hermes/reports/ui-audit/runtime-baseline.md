# Auditoria runtime da UI — baseline responsivo

**Data:** 2026-08-19  
**Aplicação:** `http://localhost:8010`  
**Método:** Chrome headless via CDP, sessão real em Signet, 4 tabs atuais testadas em 5 viewports.  
**Screenshots:** `.hermes/reports/ui-audit/screenshots-runtime/`

> Observação: o container auditado ainda servia o shell cache v4; o fonte já aponta para v5. As mudanças entre esses estados não alteram a estrutura responsiva medida (`.mecha-frame`, `.hud-body`, `.stage-center`, `.sidebar-right`, `.tab-pane`).

## Resumo executivo

O layout não apresenta overflow horizontal no documento, mas isso ocorre porque o corpo e os principais containers escondem o excedente. Há duas quebras críticas:

1. Em 320×700, a grade de 264 px é colocada em um palco de 191,5 px com `overflow: hidden`, cortando parte do caça-palavras.
2. Em 320×700, a navegação vertical consome quase toda a sidebar e deixa a tab ativa com zero pixels de altura; as mecânicas ficam inacessíveis.

No extremo de 2560×1440, o frame continua limitado a 1440 px e usa apenas 56,2% da largura disponível.

## Matriz de dimensões

| Viewport | Frame / viewport | Palco | Grade | Grade / palco | Altura visível de `PROTOCOL` | Conteúdo de `PROTOCOL` | Visível |
|---|---:|---:|---:|---:|---:|---:|---:|
| 320×700 | 300 px / 93,8% | 191,5 px | 264 px | 137,9% | 0 px | 1780 px | 0,0% |
| 768×1024 | 725,3 px / 94,4% | 371,1 px | 364 px | 98,1% | 65 px | 1738 px | 3,7% |
| 1024×768 | 989 px / 96,6% | 492 px | 483,2 px | 98,2% | 188 px | 1780 px | 10,6% |
| 1440×900 | 1401 px / 97,3% | 620 px | 569 px | 91,8% | 316 px | 1780 px | 17,8% |
| 2560×1440 | 1440 px / 56,2% | 1155 px | 584 px | 50,6% | 851 px | 1780 px | 47,8% |

## Achados confirmados

### UI-R01 — Caça-palavras cortado em 320 px — Crítico

- A grade mede 264×264 px.
- `.stage-center` mede 296×191,5 px.
- `frontend/pixel.css:200-208` aplica `overflow: hidden` ao palco.
- Cerca de 72,5 px verticais da grade excedem o palco.
- Evidência: `screenshots-runtime/320x700-tx.png`.

### UI-R02 — Tabs sem área útil em 320 px — Crítico

- Sidebar: 206 px de altura útil.
- Navegação vertical: 200 px.
- Tab ativa: `clientHeight = 0`.
- Conteúdo necessário: TX 46 px; UPGRADES 461 px; NETWORK 1059 px; PROTOCOL 1780 px.
- O `scrollHeight` da sidebar fica em 304 px e não incorpora o conteúdo interno das tabs.
- Causa: `frontend/pixel.css:350-358`, `375-380`, `428-435`, `544-550` e `2010-2086`.

### UI-R03 — Faixa de conteúdo quase inutilizável em 768 px — Alto

- Tabs avançadas recebem apenas 65 px de altura.
- `PROTOCOL` exibe 3,7% de seu conteúdo por vez.
- `NETWORK` exibe aproximadamente 7,1%.
- A navegação vertical continua consumindo 200 px mesmo no layout empilhado.

### UI-R04 — Mecânicas excessivamente empilhadas — Alto

- A tab `NETWORK` contém leaderboard, pools, missões, chat, amigos, mercado e sprint.
- A tab `PROTOCOL` contém regras, staking, skills, season pass, cards e decoder.
- Mesmo em 2560×1440, `PROTOCOL` ainda precisa rolar 1780 px dentro de 851 px.
- Evidência estrutural: `frontend/index.html:274-451`.

### UI-R05 — Tela 42" desperdiçada — Alto

- `.mecha-frame` usa `max-width: 1440px` em `frontend/pixel.css:109-112`.
- Em 2560 px, sobram aproximadamente 1120 px horizontais fora do frame.
- A grade fica em 584 px dentro de palco com 1155 px de altura.

### UI-R06 — Breakpoints insuficientes — Alto

- Só existem `max-width: 900px` e `max-width: 559px`.
- Não há estratégia específica para 768, 1024, 1440 ou 2560 px.
- A mudança em 900 px apenas empilha palco e sidebar, mantendo a navegação vertical.

### UI-R07 — Controles abaixo do tamanho recomendado — Médio

Controles abaixo de 24 px em pelo menos um estado:

- `#btn-install-app`
- botões de compra (`#btn-buy-hint`, `#btn-buy-hw`, `#btn-buy-ln`, `#btn-buy-energy`)
- `#btn-decoder-launch`
- `#friends-add-input`, `#btn-friends-add`
- `#staking-duration`, `#btn-stake`, `#btn-cancel-stake`

Há mais controles abaixo de 44 px, incluindo chat, mercado, sprint, crates, power-ups e season premium.

Referência: WCAG 2.2 SC 2.5.8 exige pelo menos 24×24 CSS px, salvo exceções: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html

### UI-R08 — Tipografia excessivamente pequena — Médio

- Labels recorrentes usam 5, 6, 7 e 8 px (`frontend/pixel.css:167-184`, `232-238`, `382-393`, `449-453`, `1940-2008`, `2034-2072`).
- O texto pode ter contraste matemático suficiente e ainda ser pouco legível pelo tamanho pixelado.
- `--text-dark` sobre `--hull-surface` tem contraste aproximado de 1,67:1.
- `--neon-red` sobre `--hull-panel` fica em aproximadamente 4,34:1, abaixo de 4,5:1 para texto pequeno.

Referência: WCAG 2.2 SC 1.4.3: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum

### UI-R09 — Ausência de redução de movimento — Médio

- Não existe `@media (prefers-reduced-motion: reduce)` em `pixel.css`.
- O shell usa animações, pulsações, spinners, flashes, scanlines e transições.

Referência: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion

### UI-R10 — Safe-area incompleta — Médio

- Algumas peças isoladas usam `env(safe-area-inset-*)`, mas o body/frame, footer e layout móvel não adotam uma estratégia consistente.
- Referência: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env

### UI-R11 — Divergência visual do protótipo aprovado — Alto

- O protótipo aprovado era claro/bege (`#f0deaf`, `#e2c992`, `#faedd0`) e usava vocabulário `.top-hud`, `.game-view`, `.btn-retro`.
- O CSS atual deriva de `new-design.html`, conceito escuro `MECHA_HUD_EDITION`, com `#0e1117`, `#161b22`, cyan neon e scanlines.
- Nenhuma das três cores-base aprovadas existe nos CSS atuais.

### UI-R12 — Emojis visíveis e inconsistentes — Alto

- Inventário inicial: 7 ocorrências no HTML e 68 ocorrências no JavaScript.
- Afeta energia, power-ups, boss, crates, sprint, eventos, notificações, achievements, chat, cards, raridades, mercado, season e level.
- Emojis mudam entre sistemas e quebram a linguagem pixel/CLI.

### UI-R13 — Variáveis visuais dinâmicas ausentes — Médio

Usadas pelo JavaScript, mas não definidas no CSS carregado:

- `--error-red`
- `--golden-hash`
- `--high-fee`
- `--lightning-blue`
- `--warning-orange`
- `--cell-size` (definida em runtime para a grade, sem fallback CSS)

O `style.css` legado contém as cinco cores, mas não é carregado por `index.html` nem cacheado pelo Service Worker; apesar disso, ainda é copiado na imagem por `frontend/Dockerfile:4`.

### UI-R14 — Navegação legada duplicada — Alto

- `showTab()` aparece em `frontend/game.js:21` e `frontend/game.js:140`.
- A segunda definição sobrescreve a primeira e procura `.tab-content`, `.nav-btn` e `.mobile-btn`, seletores inexistentes no HTML atual.
- O comentário ainda promete 5 tabs (`jogo`, `upgrades`, `competir`, `perfil`, `social`), mas o DOM oferece somente `tx`, `shop`, `rank`, `info`.

## Console/runtime

- Nenhuma exceção JavaScript foi registrada.
- Os 40 warnings coletados eram repetições do bloqueio de autoplay de `AudioContext` no Chrome headless.
- A sessão abriu e as quatro tabs atuais foram ativadas em todos os viewports.

## Evidências

Foram salvas 20 capturas:

- `320x700-{tx,shop,rank,info}.png`
- `768x1024-{tx,shop,rank,info}.png`
- `1024x768-{tx,shop,rank,info}.png`
- `1440x900-{tx,shop,rank,info}.png`
- `2560x1440-{tx,shop,rank,info}.png`
