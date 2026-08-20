# Auditoria Frontend Final — Login e Mecânicas
**Data:** 2026-08-19  
**Projeto:** `/home/developer/mempool.miner`  
**Arquivos auditados:** `frontend/index.html` (568 linhas), `frontend/game.js` (6248 linhas), `frontend/pixel.css`, `frontend/nginx.conf`, `frontend/service-worker.js`  
**Método:** Validação linha-a-linha no código atual em disco + relatórios de reprodução determinística (Chrome CDP) e auditorias anteriores.  

---

## 1. CAUSAS CONFIRMADAS

### C1 — CSP bloqueia todos os handlers inline (CAUSA RAIZ DO LOGIN)

| Diretiva | Valor | O que bloqueia |
|----------|-------|----------------|
| `script-src 'self'` | sem `'unsafe-inline'` | 11 atributos `onclick="..."` |
| `style-src 'self'` | sem `'unsafe-inline'` | 135 atributos `style="..."` |
| `font-src 'self'` | sem dominos externos | Google Fonts (JetBrains Mono, Press Start 2P, VT323) |

**Arquivo:** `frontend/nginx.conf:16`  
**Evidência:** Headers reais capturados via `curl -sI http://127.0.0.1:8010/`. Reprodução Chrome CDP confirma: clique em EXECUTE_NODE não chama `startSession()`, modal permanece aberto, `ws=null`. Chamada direta `startSession()` pelo console fecha modal e abre WebSocket com sucesso.

**Handlers inline bloqueados:**

| Linha | Elemento | Handler | Impacto |
|-------|----------|---------|---------|
| `index.html:192` | Nav button | `switchTab('tx', this)` | ❌ Navegação TAB 1 |
| `index.html:196` | Nav button | `switchTab('shop', this)` | ❌ Navegação TAB 2 (Loja) |
| `index.html:200` | Nav button | `switchTab('rank', this)` | ❌ Navegação TAB 3 (Rank) |
| `index.html:204` | Nav button | `switchTab('info', this)` | ❌ Navegação TAB 4 (Info) |
| `index.html:221` | Shop button | `buyHint()` | ⚠️ Mitigado: `addEventListener` duplicado em `game.js:745` |
| `index.html:229` | Shop button | `buyHardware()` | ⚠️ Mitigado: `addEventListener` duplicado em `game.js:746` |
| `index.html:237` | Shop button | `buyLightning()` | ⚠️ Mitigado: `addEventListener` duplicado em `game.js:747` |
| **`index.html:478`** | **Auth button** | **`startSession()`** | **❌ CRÍTICO — LOGIN TRAVADO** |
| `index.html:490` | RBF button | `useRbf()` | ❌ `useRbf()` não existe + CSP bloqueia |
| `index.html:493` | Next block | `prepareNextBlock()` | ❌ Próximo bloco |
| `index.html:528` | Lightning modal | `classList.add('hidden')` | ❌ Fechar modal Lightning |

### C2 — ReferenceError aborta o script em game.js:5421

```javascript
// game.js:5421
const originalHandleWebSocketMessage = handleWebSocketMessage;
// ReferenceError: handleWebSocketMessage is not defined
```

`handleWebSocketMessage` **nunca é definido** como variável global antes desta linha. O handler real do WebSocket está inline em `socket.onmessage` (`game.js:963`). A exceção aborta toda execução top-level subsequente.

**Arquivo:** `frontend/game.js:5421`  
**Evidência:** `Runtime.exceptionThrown` capturado via Chrome CDP. Busca exaustiva no arquivo confirma zero definições de `handleWebSocketMessage` antes da linha 5421.

### C3 — Listener `submit` em `<div>` nunca dispara

```javascript
// game.js:741
document.getElementById('auth-modal').addEventListener('submit', event => {
```

`#auth-modal` é um `<div class="modal-wrap">`, não um `<form>`. Eventos `submit` não disparam em `<div>`. O botão dentro do modal (`index.html:478`) tem `type` implícito `submit`, mas fora de `<form>` o comportamento é indefinido — e com CSP bloqueando o `onclick`, nada acontece.

**Arquivo:** `frontend/game.js:741` + `frontend/index.html:468`  
**Evidência:** Análise estática do DOM confirma `<div>` sem `<form>` envolvendo o botão.

### C4 — 25 URLs com path errado

O backend usa exclusivamente `/api/v1/networks/{realm_id}/...`. O frontend constrói 25 chamadas com `/api/${activeRealmId}/...` — path que **não existe** no backend.

**Arquivo:** `frontend/game.js` (linhas 4188–6126)  
**Evidência:** 25 ocorrências confirmadas via busca regex. Todas retornam 404.

| Mecânica | URL no JS | Endpoint real |
|----------|-----------|---------------|
| Skills | `/api/{realm}/skills/{user}` | `/api/v1/networks/{realm}/skills/{user}` |
| Skills unlock | `/api/{realm}/skills/{user}/unlock` | `/api/v1/networks/{realm}/skills/{user}/upgrade` |
| Energy status | `/api/{realm}/energy/status/{user}` | `/api/v1/networks/{realm}/energy/status` |
| Energy spend | `/api/{realm}/energy/spend/{user}` | `/api/v1/networks/{realm}/energy/spend` |
| Energy buy | `/api/{realm}/energy/buy/{user}` | `/api/v1/networks/{realm}/energy/buy` |
| Season | `/api/{realm}/season/{user}` | `/api/v1/networks/{realm}/season/{user}` |
| Season claim | `/api/{realm}/season/{user}/claim/{level}` | `/api/v1/networks/{realm}/season/{user}/claim/{reward_level}` |
| Season premium | `/api/{realm}/season/{user}/buy-premium` | `/api/v1/networks/{realm}/season/{user}/buy-premium` |
| Cards | `/api/{realm}/cards/{user}` | `/api/v1/networks/{realm}/cards/{user}` |
| Market list | `/api/{realm}/market/list` | `/api/v1/networks/{realm}/market/list` |
| Market sell | `/api/{realm}/market/sell` | `/api/v1/networks/{realm}/market/sell` |
| Market buy | `/api/{realm}/market/buy` | `/api/v1/networks/{realm}/market/buy` |
| Market history | `/api/{realm}/market/history` | `/api/v1/networks/{realm}/market/history` |
| Powerups | `/api/{realm}/powerups/{user}` | `/api/v1/networks/{realm}/powerups/{user}` |
| Global events | `/api/{realm}/global-events` | `/api/v1/networks/{realm}/global-events` |
| Sprint start | `/api/{realm}/sprint/start` | `/api/v1/networks/{realm}/sprint/start` |
| Sprint submit | `/api/{realm}/sprint/submit` | `/api/v1/networks/{realm}/sprint/submit` |
| Sprint leaderboard | `/api/{realm}/sprint/leaderboard` | `/api/v1/networks/{realm}/sprint/leaderboard` |
| Friends list | `/api/{realm}/friends/{user}` | `/api/v1/networks/{realm}/friends/{user}` |
| Friends add | `/api/{realm}/friends/add` | `/api/v1/networks/{realm}/friends/add` |
| Friends remove | `/api/{realm}/friends/remove` | `/api/v1/networks/{realm}/friends/remove` |
| Crates inventory | `/api/{realm}/crates/inventory/{user}` | `/api/v1/networks/{realm}/crates/inventory` |
| Crates open | `/api/{realm}/crates/open` | `/api/v1/networks/{realm}/crates/open` |
| Level | `/api/{realm}/level/{user}` | `/api/v1/networks/{realm}/level/{user}` |
| Level add-xp | `/api/{realm}/level/{user}/add-xp` | `/api/v1/networks/{realm}/level/{user}/add-xp` |

---

## 2. IMPACTO POR MECÂNICA

| Mecânica | Status | Causas | Detalhe |
|----------|--------|--------|---------|
| **Login/Auth** | ❌ TRAVADO | C1, C3 | `onclick` bloqueado por CSP; `submit` listener inútil em `<div>` |
| **Jogo Core** | ✅ FUNCIONAL | — | Grid, seleção, timer, recompensa, combo, slashing — tudo conectado via WebSocket |
| **Navegação (abas)** | ❌ TRAVADA | C1 | 4 botões `switchTab` bloqueados por CSP |
| **Loja** | ⚠️ PARCIAL | C1 | `addEventListener` duplicado mitiga parcialmente; sem endpoint backend dedicado |
| **Leaderboard** | ✅ FUNCIONAL | — | URL correta, polling ativo |
| **Combo/Slashing** | ✅ FUNCIONAL | — | Puramente client-side |
| **Boss Battles** | ✅ FUNCIONAL | — | Ponta a ponta comprovado |
| **Missions** | ✅ FUNCIONAL | — | URL correta, wrapper antes do abort |
| **Chat** | ✅ FUNCIONAL | — | URL correta, wrapper antes do abort |
| **Staking** | ✅ FUNCIONAL | — | URL correta, wrapper antes do abort |
| **Achievements** | ✅ FUNCIONAL | — | URL correta, tracking ativo |
| **Decoder** | ✅ FUNCIONAL | — | URL correta, endpoint existe |
| **PWA** | ✅ FUNCIONAL | — | Registro e update banner antes do abort |
| **Energia** | ❌ QUEBRADA | C4 | URL errada retorna 404 |
| **Crates** | ❌ QUEBRADA | C2, C4 | Abort + URL errada (duplo bloqueio) |
| **Sprint** | ❌ QUEBRADA | C2, C4 | Abort + URL errada |
| **Friends** | ❌ QUEBRADA | C2, C4 | Abort + URL errada |
| **Market** | ❌ QUEBRADA | C4 | Wrapper carrega mas URL errada retorna 404 |
| **Skills** | ❌ QUEBRADA | C4 | URL errada + endpoint `/unlock` vs `/upgrade` |
| **Season Pass** | ❌ QUEBRADA | C4 | Wrapper carrega mas URL errada retorna 404 |
| **Cards** | ❌ QUEBRADA | C4 | Wrapper carrega mas URL errada retorna 404 |
| **Level System** | ❌ QUEBRADA | C2, C4 | Abort + URL errada |
| **Eventos Globais** | ⚠️ PARCIAL | C2, C4 | WebSocket funciona (handler antes do abort); HTTP não (abort + URL errada) |

**Resumo:** 8 funcionais (40%) · 3 parciais (15%) · 9 quebradas (45%)

---

## 3. PROBLEMAS ESTRUTURAIS

### S1 — 11 wrappers de `startSession` em cadeia

`startSession` é redefinida 11 vezes no `game.js`, formando uma cadeia frágil de monkey-patches:

| # | Linha | Mecânica | Executa? |
|---|-------|----------|----------|
| 1 | 824 | Definição original | ✅ |
| 2 | 3144 | Missions | ✅ |
| 3 | 3531 | Chat (+ Staking) | ✅ |
| 4 | 4493 | Energy | ✅ |
| 5 | 4741 | Season | ✅ |
| 6 | 4934 | Cards | ✅ |
| 7 | 5261 | Market | ✅ |
| 8 | 5433 | Global Events | ❌ DEPOIS DO ABORT |
| 9 | 5863 | Friends | ❌ DEPOIS DO ABORT |
| 10 | 6036 | Crates | ❌ DEPOIS DO ABORT |
| 11 | 6173 | Level | ❌ DEPOIS DO ABORT |

**Arquivo:** `frontend/game.js` (linhas 824–6173)  
**Risco:** Ordem de definição importa; qualquer nova mecânica adicionada ao topo quebra a cadeia. Debug impossível sem rastrear todas as 11 redefinições.

### S2 — Botões duplicados/confusos para RBF

- `#rbf-btn` (`index.html:490`) — visível, chama `useRbf()` **inexistente**
- `#next-btn` (`index.html:541`) — oculto, usado pela lógica real de RBF em `showOrphanBlockSalvage()` (`game.js:2128`)
- `#btn-start-session` (`index.html:545`) — oculto, referenciado em `game.js:250` mas nunca usado; botão visível é outro (`index.html:478`)

**Arquivo:** `frontend/index.html:490,541,545` + `frontend/game.js:250,2128`

### S3 — Stubs vazios

| Função | Linha | Problema |
|--------|-------|----------|
| `loadPowerupsInventory()` | `game.js:267` | Corpo vazio; chamada em `game.js:6029` (depois do abort) |
| `renderWordBank()` | `game.js:1683` | Corpo vazio; chamada em `game.js:5483` (depois do abort) |
| `useRbf()` | `index.html:490` | Referenciada em HTML mas **nunca definida** no JS |

### S4 — Service Worker sem `pixel.css` no precache

`pixel.css` é referenciado em `index.html:19` mas ausente de `SHELL_ASSETS` em `service-worker.js:5-13`. Em modo offline, o CSS principal carrega mas o CSS pixel (53KB) não.

**Arquivo:** `frontend/service-worker.js:5-13`

### S5 — `pixel.css` sem Cache-Control no nginx

`pixel.css` não é coberto pela regex `location ~* ^/(?:style\.css|game\.js)$` em `nginx.conf:71`. Sem `Cache-Control` nem `Expires` no response header.

**Arquivo:** `frontend/nginx.conf:71`

### S6 — Google Fonts bloqueadas

`font-src 'self'` não permite `https://fonts.googleapis.com` nem `https://fonts.gstatic.com`. As 3 fontes (JetBrains Mono, Press Start 2P, VT323) nunca carregam.

**Arquivo:** `frontend/nginx.conf:16` + `frontend/index.html:15`

---

## 4. RECOMENDAÇÕES (arquivo:linha)

### Fase 1 — Críticos (bloqueiam o jogo)

| # | Ação | Arquivo:linha | Prioridade |
|---|------|---------------|------------|
| 1 | Definir `handleWebSocketMessage` como função global antes da linha 5421, ou remover o monkey-patch (linhas 5421–5429) | `game.js:5421` | 🔴 P0 |
| 2 | Converter `onclick="startSession()"` para `addEventListener('click', startSession)` no botão do auth-modal | `index.html:478` + `game.js` | 🔴 P0 |
| 3 | Adicionar `<form>` ao `#auth-modal` ou remover o listener `submit` inútil | `index.html:468` + `game.js:741` | 🔴 P0 |
| 4 | Corrigir 25 URLs: substituir `/api/${activeRealmId}/` por `/api/v1/networks/${activeRealmId}/` | `game.js:4188-6126` | 🔴 P0 |
| 5 | Corrigir endpoint Skills: `/unlock` → `/upgrade` | `game.js:4282` | 🔴 P0 |
| 6 | Remover `onclick="useRbf()"` do HTML ou implementar a função | `index.html:490` | 🔴 P0 |

### Fase 2 — Estruturais

| # | Ação | Arquivo:linha | Prioridade |
|---|------|---------------|------------|
| 7 | Migrar todos os 11 `onclick` inline para `addEventListener` no JS | `index.html:192-528` + `game.js` | 🟡 P1 |
| 8 | Consolidar os 11 wrappers de `startSession` em um sistema de hooks/plugins | `game.js:824-6173` | 🟡 P1 |
| 9 | Criar helper `apiUrl(path)` centralizando construção de URLs | `game.js` | 🟡 P1 |
| 10 | Preencher stubs `loadPowerupsInventory()` e `renderWordBank()` | `game.js:267,1683` | 🟡 P1 |

### Fase 3 — Completude

| # | Ação | Arquivo:linha | Prioridade |
|---|------|---------------|------------|
| 11 | Adicionar `pixel.css` ao precache do service worker | `service-worker.js:5-13` | 🟢 P2 |
| 12 | Adicionar `pixel.css` à regex do nginx ou criar `location` dedicado | `nginx.conf:71` | 🟢 P2 |
| 13 | Adicionar Google Fonts à CSP: `font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com` | `nginx.conf:16` | 🟢 P2 |
| 14 | Endpoint dedicado para loja (persistência de compras) | `backend/app/main.py` | 🟢 P2 |
| 15 | Limpar botões ocultos/duplicados (`#btn-start-session`, `#rbf-btn`) | `index.html:490,545` | 🟢 P2 |

### Fase 4 — Qualidade

| # | Ação | Arquivo:linha | Prioridade |
|---|------|---------------|------------|
| 16 | Versionar cache do service worker baseado em hash dos assets | `service-worker.js:4` | 🔵 P3 |
| 17 | Testes de integração ponta a ponta por mecânica | — | 🔵 P3 |
| 18 | Tratamento de erro unificado (padronizar try/catch) | `game.js` | 🔵 P3 |

---

## 5. INTEGRIDADE DOS ARTEFATOS

SHA-256 de todos os assets (host, container, HTTP) **coincidem perfeitamente**. O bug não é causado por imagem Docker desatualizada.

| Asset | SHA-256 (prefixo) | Match |
|-------|-------------------|-------|
| index.html | `13ae1b3e...d71` | ✅ |
| style.css | `6a360562...972` | ✅ |
| pixel.css | `d6cb1ee9...e8e` | ✅ |
| game.js | `ee46f080...d4f` | ✅ |
| manifest.webmanifest | `ba2c641c...e45` | ✅ |
| service-worker.js | `bd0cfd5c...9f` | ✅ |

---

## 6. BACKEND — SEM ERROS CAUSAIS

- API HTTP: `/api/v1/health/live` → 200, `/api/v1/networks` → 200 (3 redes)
- WebSocket: handshake 101 OK com Origin válido; dados fluindo (signet)
- 7 containers healthy, 0 restarts
- Signet ingestor: `getmempoolentry` 500 intermitente — **ruído, não causal**

---

*Relatório consolidado a partir de: `repro-execute-node.md`, `auditoria-runtime-infra.md`, `auditoria-mecanicas-e-contratos.md` e validação direta no código atual.*
