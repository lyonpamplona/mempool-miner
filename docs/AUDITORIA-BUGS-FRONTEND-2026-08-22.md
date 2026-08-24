# Auditoria de Bugs do Frontend — Mempool Miner

**Data:** 2026-08-22
**Escopo:** `frontend/game.js` (7240 linhas), `frontend/index.html`, `frontend/pixel.css` (3157 linhas), `frontend/service-worker.js`, `backend/app/main.py` + `config.py` (contratos).
**Método:** auditorias paralelas somente leitura + implementação TDD, validação API/Redis/Chromium, rebuild e health check por fase.
**Foco:** 3 bugs específicos reportados pelo usuário + varredura geral de pontas soltas.

---

## Resumo Executivo

| # | Bug | Severidade | Causa raiz (arquivo:linha) |
|---|---|---|---|
| 1 | Painel de power-ups não fecha | **ALTA — CORRIGIDO FASE 1/v24** | `pixel.css:1530` — `display:flex` anulava o atributo `hidden` |
| 2 | F5 volta para regtest (perde rede + progresso) | **ALTA — CORRIGIDO FASE 2/v26** | `startSession` re-resolve a override após carregar o catálogo e restaura os inputs |
| 3 | Palavras colidem / timeline não aparece | **ALTA — CORRIGIDO FASE 2/v26** | validação por trajetória oficial + fill sem ocorrências incidentais |
| 4 | Rodada trava sem cronômetro (energia) | **CRÍTICO — CORRIGIDO FASE 1/v24** | gate movido antes do builder + UUID idempotente + refund compensatório |

**Achados adicionais da varredura geral:** 4 ALTO (boss perde última palavra, mercado de venda quebrado, sprint quebrado de ponta a ponta, skill tree desconectada), 9 MÉDIO, 8 BAIXO.

**Inventário original (varredura inicial):** 1 CRÍTICO, 7 ALTO, 9 MÉDIO, 8 BAIXO. Durante as auditorias de fase, 11 itens adicionais (D1–D11) foram descobertos e somados à tabela MÉDIO (D8 e D11 reclassificados como ALTO e corrigidos atomicamente), e 1 item BAIXO foi consolidado — por isso as tabelas finais listam **18 MÉDIO** (A3–A7, B5–B6, D1–D11) e **7 BAIXO** (A8, B7, C2–C6). **Backlog ativo após a Fase 5/v34:** 0 CRÍTICO, 0 ALTO, 0 MÉDIO, 0 BAIXO.

---

## Bug 1 — Painel de Power-ups não fecha

### Evidências

| Ponto | Local | Evidência |
|---|---|---|
| HTML do painel | `index.html:122` | `<div class="powerups-active" id="powerups-active" hidden></div>` |
| Botão de toggle | `index.html:120` | `<button id="btn-powerups-toggle" aria-controls="powerups-active">` |
| Handler de toggle | `game.js:6606-6623` | `powerupsToggleBtn.addEventListener('click', ...)` |
| Lógica de toggle | `game.js:6615-6617` | `powerupsActiveEl.hidden = !isHidden` (correta) |
| Classe CSS de visibilidade | `pixel.css:1530-1532` | `.powerups-active { display: flex; gap: 8px; flex-wrap: wrap; }` |

### Causa raiz

**O bug é 100% CSS.** O atributo `hidden` só esconde o elemento via user-agent stylesheet (`[hidden] { display: none }`). Qualquer regra author que defina `display` no mesmo elemento vence o user-agent, independentemente de especificidade. `pixel.css:1530` define `.powerups-active { display: flex }` → quando o handler executa `powerupsActiveEl.hidden = true`, o atributo é setado no DOM, **mas o elemento continua renderizado como `display: flex`**.

O painel abre normalmente (conteúdo renderizado por `renderPowerupsPanel`), mas o segundo clique no toggle só alterna o atributo invisível — o painel **nunca some**. Como ele vive na barra flex acima do grid (`flex-wrap: wrap`), cresce verticalmente e cobre o campo do jogo.

**Descartados (verificados):**
- Handler ausente/invertido — o toggle em `game.js:6615-6616` está correto.
- Outro código reabrindo o painel — `powerupsActiveEl` só é tocado nas linhas 383, 404, 406, 476, 6608-6621.
- z-index/positioning — `.powerups-active` não tem `position`/`z-index`.
- Evento não propagando — o clique chega (o `aria-expanded` alterna).

### Correção proposta

**Opção A — guarda global (recomendada; resolve o bug e protege futuros elementos com `hidden`):**

Em `frontend/pixel.css`, junto à regra `.hidden` (linha ~2449):

```css
/* Guarda global: atributo [hidden] deve sempre vencer qualquer display author */
[hidden] { display: none !important; }
```

**Opção B — fix cirúrgico (mínimo, só o power-ups):**

Em `frontend/pixel.css`, imediatamente após a linha 1532:

```css
.powerups-active[hidden] { display: none; }
```

### Pontas soltas relacionadas (mesmo padrão)

| Elemento | Evidência | Status |
|---|---|---|
| `#staking-active` | `index.html:372` usa `u-inline-046`, não `.staking-active` | ✅ Falso positivo eliminado: o `hidden` nativo já funcionava; `.staking-active` é CSS morto |
| `.mechanic-section` | `pixel.css:513` + `pixel.css:521-523` | ✅ Já protegido (modelo a copiar) |
| `.tab-pane` | `pixel.css:459-466` | ✅ OK |
| `.modal-wrap` | `pixel.css:592-600` | ✅ OK |

**Nota de deploy:** `CACHE_VERSION` foi incrementado de `v20` para `v24` durante a Fase 1; `v24` inclui merge seguro, UUID idempotente, refund compensatório e recuperação durável de spend incerto após reload.

---

## Bug 2 — F5 volta para regtest (perde rede + progresso)

### Evidências

| Camada | Onde | Evidência |
|---|---|---|
| Select da UI | `index.html:523` | `<select id="network-select">` vazio no HTML |
| Variável em memória | `game.js:234` | `let activeRealmId = null;` |
| Preferência persistente | `game.js:659-674` | `localStorage['mempool-miner-realm']` |
| Sessão (F5) | `game.js:256-282` | `sessionStorage['mempool-miner-session']` |
| Default do backend | `config.py:88` | `DEFAULT_REALM_ID=regtest` |
| Ordem do catálogo | `config.py:56-65` | regtest → signet → mainnet (regtest é o **primeiro**) |

### Causa raiz

**Causa primária — `startSession` descarta o `realmIdOverride` quando o catálogo ainda não carregou** (`game.js:1266-1297`):

1. A lookup da override (1267-1269) ocorre **antes** de qualquer garantia de que `networkCatalog` foi populado.
2. O Fallback 1 (1272-1275) faz `await loadNetworkCatalog()`, mas **não re-resolve** `selectedNetwork` depois.
3. O Fallback 2 (1278-1283) então escolhe a **primeira rede playable do catálogo = regtest** (ordem fixa em `config.py:56-65`).
4. A linha 1317 sobrescreve `activeRealmId` e a 1318 **contamina o localStorage** com "regtest".
5. Como `previousRealm ("signet") !== activeRealmId ("regtest")`: `balanceSatoshis = 0; hardwareLevel = 1; roundNumber = 1` (1321-1330) — o progresso restaurado é zerado.

**Causa secundária (determinística, a cada F5) — identidade perdida:** `minerName`/`poolName` são restaurados nas variáveis (1221-1222) mas `startSession` os rederive do input DOM vazio (1298-1309), gerando nome aleatório → `loadPlayerState`/WebSocket sob nova identidade → saldo 0 mesmo na rede certa.

**Descartado como causa:**
- Service worker: não serve estado — exclui `/api` e `/ws` do cache.
- Storage limpo no load: `sessionStorage` sobrevive ao F5.
- Default hardcoded no frontend: o fallback 3 força **signet**, não regtest.

### O que é preservado vs. perdido no F5

**Preservado:** nível/XP, conquistas, missões, energia, temporada, cartas, mercado, amigos, crates (persistidos no backend/Redis).

**Perdido:**
- **Rede** — sobrescrita para regtest.
- **Identidade** — novo nome aleatório a cada F5.
- **Saldo/hardware/round** — zerados na troca de realm.
- **Rodada em andamento** — `txBuffer`, `blockWords`, timer, células selecionadas.
- **Power-ups** — `powerupEffects`, `pendingPowerups` fora do `saveSessionState`.
- **Combo** — zerado pelo `teardownSession('network-change')` disparado pelo próprio `startSession`.

### Correção proposta

**Fix 1 — `startSession`: carregar o catálogo antes de resolver a override** (`game.js:1266-1297`):

```js
async function startSession(realmIdOverride = null) {
    // 1) Garante o catálogo ANTES de resolver a rede desejada
    if (networkCatalog.size === 0) {
        announceGameStatus('Carregando redes...');
        await loadNetworkCatalog();
    }

    // 2) Override (restauração/reconexão) tem prioridade absoluta
    let selectedNetwork = realmIdOverride
        ? networkCatalog.get(realmIdOverride)
        : networkCatalog.get(networkSelectEl.value);

    // 3) Fallback para a primeira playable só quando NÃO há override
    if (!selectedNetwork?.playable && networkCatalog.size > 0) {
        selectedNetwork = Array.from(networkCatalog.values()).find(n => n.playable);
        if (selectedNetwork) networkSelectEl.value = selectedNetwork.realm_id;
    }
    // Fallback 3 (signet) mantido
}
```

**Fix 2 — IIFE de restauração: gravar a identidade nos inputs** (após `game.js:1223`):

```js
document.getElementById('miner-input').value = saved.minerName;
document.getElementById('pool-tag-input').value = saved.poolName ?? '';
savePreferredRealm(saved.activeRealmId);
```

**Fix 3 (defesa em profundidade) — `loadNetworkCatalog` respeita a sessão já restaurada** (`game.js:719`):

```js
const preferredRealm = (activeRealmId && networkCatalog.get(activeRealmId)?.playable)
    ? activeRealmId
    : getPreferredRealm();
```

**Fix 4 (opcional) — `startSession` não zera o nome quando já há nome restaurado** (`game.js:1308`):

```js
minerName = safeInput || minerName || "Miner_" + Math.floor(Math.random() * 9999);
```

### Estado após a Fase 2/v26

- `startSession` re-resolve o `requestedRealmId` depois de `await loadNetworkCatalog()` e sincroniza o `<select>` com a rede validada.
- A restauração preenche `miner-input` e `pool-tag-input` antes de chamar `startSession`, sem `loadPlayerState` duplicado.
- Playwright sobre o container confirmou F5 com Signet, identidade `F5QA`, pool `F5Pool`, saldo 4.242 e operador preservados.
- A auditoria encontrou e corrigiu um race secundário: `spendEnergy` agora recebe o snapshot de realm/jogador capturado pela rodada; resposta stale não altera a UI da sessão nova e o refund volta ao realm correto.

---

## Bug 3 — Palavras colidem / timeline não aparece

### Evidências

| Ponto | Local | Evidência |
|---|---|---|
| Geração (backend) | `engine.py:83-96` | `tx_to_word()` — primeira palavra BIP39 dos 128 bits do TXID |
| Acumulação WS | `game.js:1475-1503` | `txBuffer` com dedupe por palavra (1491) |
| Placement normal (6 palavras) | `game.js:2181-2230` | `injectWordInGrid` impede sobreposição direta, mas não impede ocorrências incidentais após preencher o grid |
| Preenchimento aleatório | `game.js:2161-2165` | células vazias recebem letras aleatórias sem validar quantas ocorrências de cada palavra-alvo passaram a existir |
| Registro do alvo | `game.js:2203` | guarda `startX/startY`, mas não guarda a direção nem as coordenadas completas da palavra |
| Validação | `game.js:2506-2512` | compara apenas o texto selecionado; não confere se as células são as do placement oficial |
| Bloqueio de célula | `game.js:2467-2481, 2597-2604` | células selecionadas são marcadas `found` e não podem iniciar nem continuar outra seleção |
| Linha/timeline | `game.js:2593-2599` | `drawAnimatedLine()` só no ramo `if (match)` |
| Placement Sprint | `game.js:2237-2288` | escrita direta por linha; é uma fragilidade separada, mas não explica o fluxo normal atual de 6 palavras |

### Causa raiz

**Causa primária confirmada no fluxo normal:** o placement oficial não sobrepõe palavras, porém o sistema valida uma seleção **somente pelo texto** (`game.js:2506-2512`). Depois do placement, letras aleatórias e trechos de outras palavras podem formar uma segunda ocorrência incidental de uma palavra-alvo. O jogador pode selecionar essa ocorrência não oficial; ela é aceita como válida e suas células são marcadas `found`. Se essa ocorrência atravessar a posição oficial de outra palavra-alvo, as células compartilhadas passam a bloquear a seleção dessa outra palavra.

Isso explica exatamente o relato: uma palavra parece se formar "usando" letras da outra, a primeira é aceita, e a segunda fica impossível embora o placement original não tenha sobreposição direta.

**Reprodução determinística independente:** um harness que replica `injectWordInGrid`, o preenchimento aleatório e a busca textual testou 30.000 grades 12×12 com 6 palavras (`CLAIM`, `SATS`, `BLOCK`, `MINER`, `HASH`, `COIN`). Foram encontradas **165 rodadas perigosas (0,55%)**. Na seed `231`, uma ocorrência incidental de `HASH` nas coordenadas `(4,5)..(4,8)` atravessa a célula `(4,6)` da posição oficial de `CLAIM`; encontrar esse `HASH` marca a célula como `found` e bloqueia `CLAIM`. A taxa é demonstrativa para esse conjunto de palavras, não uma estimativa da produção.

**Fragilidades secundárias:**
- `blockWords` não armazena a direção nem o conjunto completo de coordenadas; `startX/startY` não bastam para validar a posição.
- `blockWords.find(...)` escolhe o primeiro match textual, não o alvo cuja trajetória foi selecionada.
- `renderWordBank()` (Sprint) escreve diretamente em linhas sem usar o algoritmo robusto. Entretanto, com as 4 palavras atuais e grade de pelo menos 8 linhas, `index % currentGridSize` produz linhas distintas; a conclusão anterior de que esse era o causador do relato normal foi rebaixada para **fragilidade latente**, não causa comprovada.
- O DOM do banco deduplica palavras por texto, enquanto `blockWords` pode manter entradas repetidas no Sprint.

### Por que a timeline não aparece

A linha SVG (`drawAnimatedLine`) é desenhada somente quando a seleção textual retorna um match. A ocorrência incidental aceita desenha a linha no caminho errado e marca suas células como `found`. A palavra oficial atravessada fica parcialmente bloqueada; uma tentativa de selecioná-la não consegue começar/continuar pelas células bloqueadas, portanto seu match nunca é processado e sua linha oficial não aparece. Como `wordsFoundInBlock` não alcança `blockWords.length`, a rodada termina apenas por timeout.

### Correção proposta

1. **Fonte de verdade por coordenadas:** ao posicionar cada palavra, salvar `coords` (lista ordenada de `{x,y}`) em `blockWords`, incluindo o caminho reverso válido.
2. **Validação por trajetória:** em `endSelection`, aceitar somente quando as coordenadas de `selectedCells` coincidirem com `match.coords` ou seu reverso; texto igual em outro lugar do grid deve ser rejeitado.
3. **Invariante pós-preenchimento:** depois de gerar as letras aleatórias, escanear cada palavra-alvo e garantir que exista exatamente uma ocorrência — a oficial. Se surgir ocorrência incidental, regenerar apenas as células filler envolvidas ou reconstruir a grade com limite de tentativas.
4. **Unificar o Sprint:** substituir a escrita direta de `renderWordBank` por uma função de placement compartilhada que também devolva coordenadas e deduplique o conjunto de palavras antes de criar `blockWords`/DOM.
5. **Teste de regressão:** usar a seed `231` como fixture e afirmar que a ocorrência incidental de `HASH` não é aceita e não bloqueia `CLAIM`.

### Estado após a Fase 2/v26

- Cada alvo guarda a lista ordenada `coords`; `endSelection` aceita somente a trajetória oficial ou seu reverso.
- O filler é regenerado até não existir ocorrência incidental; se não convergir, o builder reconstrói placement e grade com limite de tentativas.
- Sprint deduplica palavras e usa o mesmo `injectWordInGrid`, produzindo coordenadas oficiais.
- Harness Playwright: ocorrência incidental rejeitada, `CLAIM` oficial/reverso aceito, Sprint deduplicado e **3.000 grades** com zero incidentais, zero falhas e zero coordenadas inválidas.

---

## Varredura Geral — Pontas Soltas Adicionais

### CRÍTICO

**B1. Gate de energia: rodada pode travar sem cronômetro** — **CORRIGIDO E AUDITADO NA FASE 1/v24**
- O monkey-patch posterior de `startNetworkRace` foi removido e substituído por `requestPlayableBlockBuild()`, que consome energia antes de expor a rodada.
- Em falha, reexibe o overlay, mantém `isPlaying=false`, não cria timer e preserva as seis transações para retomada após refill/compra.
- Spend/refund agora usam scripts Lua atômicos e `round_id` UUID idempotente; stale epoch e falha total de placement enfileiram refund persistente no `localStorage` até confirmação do backend.
- API e Playwright comprovaram retry sem débito duplo e refund único nos dois caminhos de aborto.
- A tentativa de spend também é persistida antes do fetch; após timeout + reload, o cliente resolve o mesmo UUID e o compensa, evitando um segundo débito.

### ALTO

**A1. Vencer o boss perde a última palavra — CORRIGIDO NA FASE 3/v28**
- O `return` em 2487 pula todo o fluxo comum: pontos, XP, save, linha SVG, marcação de células.
- **Impacto:** a última palavra do boss não é marcada; o jogador perde pontos/XP; o saldo com o loot não é salvo.
- O fluxo comum agora termina antes do modal especial: pontos, XP, save, linha, células, score e sync são preservados; métricas/crate/round avançam uma vez e `showResult` normal é suprimido.

**A2. Mercado — dropdown de venda nunca é populado — CORRIGIDO NA FASE 3/v28**
- `populateSellDropdown` faz `Object.entries(marketInventory)` sobre o objeto de resposta inteiro (`{inventory, definitions}`), iterando as chaves `inventory` e `definitions` (valores = objetos, não contagens).
- **Impacto:** a aba "Vender" do mercado é inutilizável.
- `loadMarketInventory` extrai `payload.inventory`; o POST envia `username` conforme `MarketSellRequest` e o refresh mantém o dropdown sincronizado.
- A auditoria também corrigiu compra selecionada: cada listing tem ID estável, o frontend envia `username + listing_id`, histórico lê `sales` e o Lua remove/transfere atomicamente sem janela de rollback.

**B2. Modo Sprint: `sprintWordsFound` nunca incrementa + fim de rodada duplo — CORRIGIDO NA FASE 3/v28**
- `sprintWordsFound` é sempre 0 no `sprint/submit`.
- Quando todas as palavras são encontradas, `endSelection` dispara o fluxo **normal** + o `sprintTimerInterval` continua rodando → dois modais sobrepostos.
- O suposto vazamento de DOM era falso positivo: `#sprint-timer-display` é estático em `index.html` e `showSprintTimer()` só cria fallback se estiver ausente.
- **Impacto:** feature Sprint quebrada de ponta a ponta.
- Uma máquina idempotente unifica conclusão/timeout, submete o contador real uma vez, preserva o timer estático e invalida respostas stale por geração/realm/jogador.

**B3. Skill Tree: bônus desconectados do jogo — CORRIGIDO NA FASE 3/v28**
- `applySkillBonuses` nunca é chamado no load da sessão → bônus perdidos ao recarregar.
- `baseTimeLimit` e `hintCost` **não são lidos em lugar nenhum** do loop de jogo.
- **Impacto:** o jogador compra habilidades que **não têm nenhum efeito**.
- Os bônus usam as chaves backend corretas, são derivados idempotentemente e alimentam timer normal, preço real da dica e recompensa base; reload/upgrade reaplicam sem acumular.

### MÉDIO

| # | Item | Evidência |
|---|---|---|
| A3 | **CORRIGIDO FASE 4/v32** — `buySeasonPremium`: botão reabilitado após a compra | `game.js` — lifecycle Premium |
| A4 | **CORRIGIDO FASE 4/v32** — Decoder: após 429, botão fica invisível | `game.js` — `startDecoderGame` |
| A5 | **CORRIGIDO FASE 4/v32** — Crates: notificação "Bônus Legendário" repetida | `game.js` — crate render/open |
| A6 | **CORRIGIDO FASE 4/v32** — chat re-buscado a cada abertura | cache + guard in-flight por sessão |
| A7 | **CORRIGIDO FASE 4/v32** — mercado re-buscado a cada clique | cache por seção + guard in-flight |
| B5 | **CORRIGIDO FASE 4/v32** — `loadPlayerState` sem guarda | snapshot geração/realm/jogador |
| B6 | **CORRIGIDO FASE 4/v32** — `window.NETWORK_TIME_BONUS` morto/acumulativo | `levelTimeBonus` derivado e separado do hardware |
| D1 | **CORRIGIDO FASE 4/v32** — respostas REST stale | guardas nos loaders e locks pós-`await` |
| D2 | **CORRIGIDO FASE 4/v32** — refund 4xx repetido | classificação terminal/transitória |
| D3 | **CORRIGIDO FASE 4/v32** — resposta perdida de spend | retry do mesmo UUID + resync imediato |
| D4 | **CORRIGIDO FASE 4/v32** — MEV não causa dano ao Boss | toda palavra causa um dano |
| D5 | **CORRIGIDO FASE 4/v32** — Boss sob `result-modal` | evento ignorado enquanto modal ativo |
| D6 | **CORRIGIDO FASE 4/v32** — `block_mined` durante Sprint abre RBF | término Sprint tem precedência |
| D7 | **CORRIGIDO FASE 4/v32** — vendedor online stale | evento público `market_sale` no relay |
| D8 | **ALTO — CORRIGIDO FASE 4/v32** — race no upgrade de Skill | Lua atômico para check + mutação |
| D9 | **CORRIGIDO FASE 4/v32** — bônus Mining ausente em Boss/Sprint | `skillTimeBonus` em todos os timers |
| D10 | **CORRIGIDO FASE 4/v32** — reward Sprint não atualiza HUD | espelho local após confirmação backend |
| D11 | **ALTO — CORRIGIDO FASE 4/v32** — compra de energia read/write concorrente | Lua atômico saldo + energia |

**Mismatch de energia — CORRIGIDO NA FASE 1:** `energy/spend` e `energy/buy` retornam payload parcial (`current`, sem `max`/`next_refill_at`). `mergeEnergyState()` agora preserva os metadados do status; teste RED→GREEN adicionado.

### BAIXO

| # | Item | Evidência |
|---|---|---|
| A8 | **CORRIGIDO FASE 5/v34** — `toggleChatPanel()` morta removida | navegação real usa `showTab('social')` |
| B7 | **CORRIGIDO FASE 5/v34** — símbolos mortos removidos | estatística viva `poolRank1` preservada |
| C2 | **CORRIGIDO FASE 5/v34** — mensagens de sistema respeitam teto 50 | helper único de append/evicção |
| C3 | **CORRIGIDO FASE 5/v34** — histórico/echo oldest-first | array e DOM limitados a 50 |
| C4 | **CORRIGIDO FASE 5/v34** — sinks externos endurecidos | DOM/textContent/dataset + escaping explícito |
| C5 | **CORRIGIDO FASE 5/v34** — botão restaura markup original | conteúdo HTML estático preservado |
| C6 | **CORRIGIDO FASE 5/v34** — Boss é dono incondicional da rota | sem fall-through ao buffer normal |

---

## Plano de Ação

### Fase 1 — Crítico + Quick Wins (est. 2-3h)

| Item | Arquivo | Esforço |
|---|---|---|
| B1: Gate de energia (mover para antes de `buildPlayableBlock`) | `game.js` | 1h |
| Bug 1: Power-ups não fecha (guarda global `[hidden]`) | `pixel.css` | 15min |
| Bump `CACHE_VERSION` | `service-worker.js` | 5min |

**Validação:** `docker compose up --build -d` → health check → testar power-ups (abrir/fechar) → testar energia insuficiente (rodada não trava).

### Fase 2 — Bugs Específicos ALTO (est. 4-5h)

| Item | Arquivo | Esforço |
|---|---|---|
| Bug 2: F5 persiste rede + identidade (Fix 1-4) | `game.js` | 2h |
| Bug 3: Coordenadas oficiais + unicidade pós-fill + unificação do Sprint | `game.js` + teste | 3h |
| Bump `CACHE_VERSION` | `service-worker.js` | 5min |

**Validação:** `docker compose up --build -d` → health check → testar F5 em signet (rede + saldo + nome preservados) → executar fixture normal de 6 palavras/seed `231` (ocorrência incidental rejeitada, `CLAIM` permanece selecionável) → testar Sprint com palavras repetidas e final antecipado.

### Fase 3 — ALTO restantes (est. 4-6h)

| Item | Arquivo | Esforço |
|---|---|---|
| A1: Boss perde última palavra (mover `return` para após o fluxo comum) | `game.js` | 1h |
| A2: Mercado de venda (corrigir shape `{inventory, definitions}`) | `game.js` | 1h |
| B2: Sprint (contador + timer + limpeza de DOM) | `game.js` | 2h |
| B3: Skill Tree (chamar `applySkillBonuses` no load + ler `baseTimeLimit`/`hintCost`) | `game.js` | 2h |
| Bump `CACHE_VERSION` | `service-worker.js` | 5min |

**Validação:** `docker compose up --build -d` → health check → testar boss (última palavra marcada) → testar mercado (dropdown populado) → testar sprint (contador correto, 1 modal) → testar skill tree (bônus aplicados).

### Fase 4 — MÉDIO + D8/D11 reclassificados ALTO — CONCLUÍDA/v32

| Item | Esforço |
|---|---|
| A3-A7: lifecycle, Decoder, crates e caches concorrentes | concluído |
| B5/D1: guards de sessão e locks stale | concluído |
| D2/D3: recuperação idempotente de energia | concluído |
| D4-D6/D9/D10: Boss/Sprint/timers/reward | concluído |
| D7: evento `market_sale` e refresh do vendedor | concluído |
| D8: upgrade Skill atômico em Lua | concluído |
| D11: compra de energia atômica em Lua | concluído |
| B6: bônus de nível derivado sem acumular | concluído |
| `CACHE_VERSION` | `v32` |

**Evidências:** 74 testes focados; 158 testes globais aprovados + 3 falhas WebSocket preexistentes; concorrência real Skill 1×200/4×400; compra de energia concorrente terminou saldo 0/energia 6; PubSub real `market_sale`; Chromium comprovou Sprint start 1× e caches 1/1/1; 7/7 serviços saudáveis.

**Auditoria independente de fechamento:** UI/async, Energia, Sprint e Mercado foram **APROVADOS**, sem CRÍTICO/ALTO/MÉDIO remanescente ou introduzido.

### Fase 5 — BAIXO + Limpeza — CONCLUÍDA/v34

| Item | Esforço |
|---|---|
| A8: remover `toggleChatPanel` morta | concluído |
| B7: remover símbolos mortos sem tocar `poolRank1` vivo | concluído |
| C2/C3: teto compartilhado e ordem oldest-first | concluído |
| C4: DOM/textContent/dataset + escaping dos sinks externos | concluído |
| C5: preservar markup original do botão de energia | concluído |
| C6: gate Boss incondicional | concluído |
| `CACHE_VERSION` | `v34` |

**Evidências:** 79 testes focados; 163 testes globais aprovados + 3 falhas WebSocket preexistentes; Chromium confirmou ordem oldest-first, teto 50, payloads XSS sem nós/handlers injetados, markup do botão preservado, dead code ausente e zero erros de console; harness Fase 4 reaprovado; 7/7 serviços saudáveis.

### Auditoria Final

Após cada fase: `docker compose up --build -d` → health check → validação funcional → agent de auditoria independente.

**Fechamento (4 agentes paralelos, somente leitura):**

| Auditoria | Veredito | Evidência |
|---|---|---|
| Fase 5 — comportamento/limpeza | **APROVADO** | dead code ausente, `poolRank1` vivo preservado; chat oldest-first + teto 50; C5 preserva markup; C6 gate Boss incondicional |
| Segurança C4 (XSS) | **APROVADO** | zero sink explorável; `escapeHtml` correto; mercado/crate/staking/chat via `textContent`/`createElement`/`dataset` |
| Transversal do diff (fases 1–5) | **APROVADO** | ~20 contratos FE↔BE consistentes; suíte 163 passed + 3 WS preexistentes (não agravadas) |
| Testes, docs e deploy | **APROVADO** | `v34` no arquivo **e** servido; 7/7 healthy; `git diff --check` limpo; contagens reconciliadas |

**Achados do agente transversal — todos desconfirmados com evidência real:**

| Achado | Severidade declarada | Veredito real |
|---|---|---|
| Lua `redis.call('type', key)['ok']` → `nil` | ALTO/CRÍTICO | **FALSO POSITIVO** — `EVAL` no Redis 7.4 real: `type()` retorna table, `['ok']` extrai o tipo; guard exato dos 3 scripts (`upgrade_skill`, `ENERGY_BUY_SCRIPT`, `buy_from_market`) passa com chaves `none` |
| `startSprintRound` sem guard de `isPlaying` | MÉDIO | **FALSO POSITIVO** — só é chamado entre rodadas (`startNetworkRace` via "próxima rodada" e `playAgainBtn` pós-sprint); o botão `btn-sprint-mode` só alterna a flag, não inicia rodada |
| Boss não chama `submitScore()` | MÉDIO | **FALSO POSITIVO** — `submitScore()` roda em **toda** palavra (`game.js:2757`), incluindo as do boss; o branch `bossDefeatHandled` não precisa repeti-lo |
| 409 tratado como 400 (UX enganosa) | MÉDIO | **FALSO POSITIVO** — já tratado em `game.js:5402-5406` com mensagem própria ("A tentativa anterior já foi compensada") |

**Observações BAIXO (não bloqueantes, pré-existentes):**
- `chatMessages` (array) não recebe mensagens de sistema (`appendSystemMessage` só toca o DOM) — divergência array↔DOM pré-existente; o teto de 50 no DOM é o efetivo.
- `updateRateLimitInfo(4)` hardcodeia "assume 1 usado" (`game.js:4264`) — comportamento pré-existente.
- `docs/AUDITORIA-BUGS-FRONTEND-2026-08-22.md:19` declara "8 BAIXO" mas a tabela lista 7 itens (A8, B7, C2–C6); a contagem original "9 MÉDIO" não reconcilia aritmeticamente com a tabela (18 linhas, D1–D11 são descobertas tardias de fase).

**Veredito geral: APROVADO** — 0 CRÍTICO, 0 ALTO, 0 MÉDIO, 0 BAIXO ativo. As 3 falhas WebSocket de `test_models.py` eram preexistentes (o diff não toca `events.py`/`EventRelay`/`pubsub`/`serve_websocket`) e não foram agravadas; foram **corrigidas em seguida** (ver seção abaixo).

### Correção das 3 falhas WebSocket (testes obsoletos)

As 3 falhas de `test_models.py` eram **testes obsoletos** que não foram atualizados quando a arquitetura evoluiu (intencionalmente, conforme git log `2c99050` e `f2006fa`). Causa raiz de cada uma:

| Teste | Causa raiz | Correção |
|---|---|---|
| `test_public_event_removes_runtime_and_source_identity` | Esperava que `txid` **não** estivesse no payload público, mas `txid` foi adicionado ao `PUBLIC_EVENT_FIELDS["transaction_received"]` (`main.py:119`) de forma intencional (documentado no CHANGELOG: "txid completo no payload público") | Atualizado o teste para **esperar** `txid` no payload público (comportamento correto e documentado) |
| `test_ws_sender_filters_each_redis_message` | O `FakeRelay` usava um único `queue`, mas o `EventRelay` foi refatorado para `add_queue()`/`remove_queue()` (filas por-sender) | `FakeRelay` atualizado para o contrato `add_queue`/`remove_queue` |
| `test_public_websocket_handshake_remains_compatible` | O `WaitingPubSub.unsubscribe(_channel)` exigia argumento, mas `EventRelay.stop()` chama `unsubscribe()` sem argumento; e faltava `get_message()` | `WaitingPubSub` atualizado: `unsubscribe()` sem argumento + `get_message()` |

**Validação:** 3 testes passam; suíte global **166 passed, 0 failed**. WebSocket validado ao vivo na rota canônica `/ws/v1/game/signet` (a que o frontend usa, `game.js:236`): `action: game_start`, `realm_id: signet`, `status: ready`, `playable: true`, `event_id` como hash opaco. O log do backend confirma `('172.20.0.3', ...) - "WebSocket /ws/v1/game/signet" [accepted]` — o navegador conecta e é aceito normalmente.

> Nota: a rota `/ws/regtest` (usada em testes antigos) não existe mais; a rota canônica é `/ws/v1/game/{realm_id}` (`main.py:4850`) e o alias legado é `/ws/game` (`main.py:4856`).

---

## Notas de Deploy

- **`CACHE_VERSION`** em `service-worker.js:7` deve ser incrementado a cada deploy que altere o shell (Fase 5 publicada como `v34`).
- **Sem commit** — as mudanças ficam no working tree (estilo de trabalho do usuário).
- **Backend foi alterado nas Fases 1, 3 e 4**: energia idempotente; compra selecionada/atômica; upgrade Skill atômico; evento público de venda; limite Sprint com bônus.
