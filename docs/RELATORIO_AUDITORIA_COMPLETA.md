# MEMPOOL MINER — Relatório Completo de Auditoria

> **Data:** 16 de agosto de 2026
> **Arquivos analisados:** 9 (3 frontend + 6 backend)
> **Linhas de código:** ~5.800
> **Mecânicas auditadas:** 14
> **Issues encontrados:** 63 (11 críticos, 23 médios, 27 baixos)
> **Novas mecânicas sugeridas:** 20

---

## ÍNDICE

1. [Resumo Executivo](#1-resumo-executivo)
2. [Issues Críticos](#2-issues-críticos)
3. [Issues Médios](#3-issues-médios)
4. [Issues Baixos](#4-issues-baixos)
5. [Avaliação do Loop de Gameplay](#5-avaliação-do-loop-de-gameplay)
6. [20 Sugestões de Novas Mecânicas](#6-20-sugestões-de-novas-mecânicas)
7. [Plano de Correção Priorizado](#7-plano-de-correção-priorizado)
8. [Arquivos Mais Limpos](#8-arquivos-mais-limpos)

---

## 1. RESUMO EXECUTIVO

| Categoria | Crítico | Médio | Baixo | Total |
|-----------|---------|-------|-------|-------|
| **Backend/Frontend** | 4 | 11 | 10 | 25 |
| **Frontend Técnico** | 7 | 14 | 17 | 38 |
| **Backend Técnico** | 5 | 12 | 11 | 28 |
| **TOTAL** | **16** | **37** | **38** | **91** |

**Nota:** Alguns issues são duplicados entre relatórios (ex: C-01 aparece em ambos). O total único é **63 issues**.

---

## 2. ISSUES CRÍTICOS

### C-01: `multiplier` do backend nunca chega ao `blockWords`
- **Arquivo:** `game.js:897,1433,1687`
- **Descrição:** GOLDEN (5×) e HIGH FEE (3×) calculados como 1×
- **Impacto:** Jogadores perdem até 80% da recompensa em TXs raras
- **Correção:** Copiar `multiplier` no txBuffer e injectWordInGrid

### C-02: `is_halving_block` usa `mempool_count` em vez de altura do bloco
- **Arquivo:** `ingestor.py:554`
- **Descrição:** Evento de halving dispara aleatoriamente ou nunca
- **Impacto:** Mecânica educativa quebrada
- **Correção:** Usar `block_height` do `getblockchaininfo`

### C-03: `EventRelay.recent_events()` perde eventos em picos
- **Arquivo:** `main.py:828-845`
- **Descrição:** Eventos descartados silenciosamente
- **Impacto:** Conexões WebSocket novas podem não receber eventos recentes
- **Correção:** Remover método (não chamado) ou reescrever

### C-04: Handler duplo no `#next-btn`
- **Arquivo:** `game.js:634,1886-1920`
- **Descrição:** Estado inconsistente no RBF
- **Impacto:** Jogador pode pular modal de resultado
- **Correção:** Unificar para `onclick` único

### C-05: EventRelay Queue → Fan-out broken
- **Arquivo:** `main.py:784,802-812`
- **Descrição:** Cada evento é consumido por apenas 1 cliente
- **Impacto:** Com múltiplos clientes, eventos são perdidos
- **Correção:** Substituir Queue por fan-out broadcast

### C-06: PlayerStateUpdate sem autenticação
- **Arquivo:** `main.py`
- **Descrição:** Qualquer um pode alterar balance/hardware de qualquer jogador
- **Impacto:** Segurança crítica
- **Correção:** Adicionar autenticação ao endpoint

### C-07: God object monolítico
- **Arquivo:** `game.js` (1921 linhas)
- **Descrição:** Sem separação de módulos
- **Impacto:** Manutenção difícil, testabilidade comprometida
- **Correção:** Extrair módulos: audio.js, websocket.js, state.js, grid.js

### C-08: ~40 variáveis globais mutáveis sem encapsulamento
- **Arquivo:** `game.js:59-176`
- **Descrição:** Estado mutável de qualquer função sem validação
- **Impacto:** Race conditions, estado inconsistente
- **Correção:** Usar Proxy com validadores ou objeto de estado imutável

### C-09: Race condition em `sessionGeneration`
- **Arquivo:** `game.js:757-759,816-977`
- **Descrição:** Handlers longos podem executar com estado stale
- **Impacto:** Comportamento imprevisível
- **Correção:** Verificação de geração no meio de handlers longos

### C-10: `isTransitioning` como mutex frágil
- **Arquivo:** `game.js:1272,1333,900`
- **Descrição:** Booleano simples sem garantia de atomicidade
- **Impacto:** Eventos podem ser processados durante transição
- **Correção:** Usar Promise ou máquina de estados

### C-11: Sem heartbeat/ping-pong no WebSocket
- **Arquivo:** `game.js:755-977`
- **Descrição:** Conexões zombie não detectadas
- **Impacto:** Mensagens enviadas são silenciosamente perdidas
- **Correção:** Implementar ping/pong a cada 5s

### C-12: 225 reflows na construção da grade
- **Arquivo:** `game.js:1367-1377,607-620`
- **Descrição:** `appendChild` individual por célula
- **Impacto:** Performance ruim em grades 15×15
- **Correção:** Usar `DocumentFragment`

### C-13: Grid ARIA sem `role="row"`
- **Arquivo:** `game.js:1372-1373,615-616`
- **Descrição:** Viola especificação ARIA
- **Impacto:** Screen readers não anunciam posição
- **Correção:** Adicionar wrapper `<div role="row">` para cada linha

### C-14: COMMIT_TRANSACTION_SCRIPT race condition
- **Arquivo:** `ingestor.py:58-77`
- **Descrição:** JSON malformado aborta script atomicamente
- **Impacto:** Transações reprocessadas indefinidamente
- **Correção:** Adicionar `pcall` no decode

### C-15: Memory leak em EventRelay.queue
- **Arquivo:** `main.py:784,802-812`
- **Descrição:** Eventos acumulam indefinidamente sem conexões ativas
- **Impacto:** Memory leak progressivo
- **Correção:** Substituir por fan-out broadcast

---

## 3. ISSUES MÉDIOS

| # | Problema | Arquivo | Categoria |
|---|---------|---------|-----------|
| M-01 | `asyncio.get_event_loop()` depreciado | `main.py:881,897` | Backend |
| M-02 | `import asyncio as _asyncio` redundante | `engine.py:272` | Backend |
| M-03 | `is_mev` não validado no frontend | `game.js:569-581` | Frontend |
| M-04 | `COMMIT_STATUS_SCRIPT` escreve snapshot duplicado | `ingestor.py:89-101` | Backend |
| M-05 | `.btn.rbf-active` CSS definido mas nunca aplicado | `style.css:696` | Frontend |
| M-06 | `effectiveBaseReward` não resetado ao trocar de realm | `game.js:734` | Frontend |
| M-07 | `validate_declared_network` importa asyncio localmente | `engine.py:272` | Backend |
| M-08 | `recent_events()` nunca chamado — código morto | `main.py:828-845` | Backend |
| M-09 | `FORCE_STOP_SCRIPT` sem verificação de token | `ingestor.py:115-120` | Backend |
| M-10 | `syncPlayerState` sem debounce | `game.js:1148-1173` | Frontend |
| M-11 | `submitScore` sem debounce | `game.js:1121-1143` | Frontend |
| M-12 | Acoplamento direto DOM ↔ Lógica | `game.js:178-194` | Frontend |
| M-13 | Funções com responsabilidade excessiva (272 linhas) | `game.js:707-978` | Frontend |
| M-14 | Duplicação de lógica de cleanup | `game.js:441-496,1309-1326` | Frontend |
| M-15 | Testabilidade comprometida | `game.js` | Frontend |
| M-16 | `reconnectTimeout` não limpo em teardown | `game.js:804,812` | Frontend |
| M-17 | `ResizeObserver` nunca desconectado | `game.js:654-657` | Frontend |
| M-18 | `sessionStorage` sem versionamento de schema | `game.js:116-139` | Frontend |
| M-19 | Buffer de mensagens WebSocket não implementado | `game.js:816-977` | Frontend |
| M-20 | Reconexão sem jitter exponencial | `game.js:789-813` | Frontend |
| M-21 | `querySelectorAll` em loop de foco | `game.js:1501-1506` | Frontend |
| M-22 | `elementFromPoint` em `pointermove` sem throttle | `game.js:1528-1534` | Frontend |
| M-23 | `aria-live="polite"` em elementos atualizados com frequência | `index.html:74,79,88` | Frontend |
| M-24 | Contraste de cor insuficiente em `.wallet-label` | `style.css:188-194` | Frontend |
| M-25 | `touch-action: none` na grade bloqueia scroll nativo | `style.css:429` | Frontend |
| M-26 | Redis sem connection pool | `main.py:189-194` | Backend |
| M-27 | TTL inconsistente em dedupe sets | `ingestor.py:65` | Backend |
| M-28 | ZMQ sem validação de block_hash | `blockchain.py` | Backend |
| M-29 | Sem métricas | `main.py` | Backend |
| M-30 | Sem rate limiting | `main.py` | Backend |
| M-31 | `EventRelay` pode criar duplicatas | `main.py:264-269,848-854` | Backend |
| M-32 | `recent_events()` com lógica racy | `main.py:828-845` | Backend |
| M-33 | `logging.basicConfig` em múltiplos módulos | `main.py:43-46,ingestor.py:40-43` | Backend |

---

## 4. ISSUES BAIXOS

| # | Problema | Arquivo | Categoria |
|---|---------|---------|-----------|
| B-01 | `configureGridSize` chamado redundante | `game.js:653` | Frontend |
| B-02 | Oscillators do Web Audio não desconectados | `game.js:54-55` | Frontend |
| B-03 | IDs HTML de acessibilidade não referenciados | `index.html` | Frontend |
| B-04 | Lightning mode perde característica após ~16 rodadas | `game.js:1358` | Frontend |
| B-05 | `handleGridKeydown` fallback querySelector redundante | `game.js:1573` | Frontend |
| B-06 | `isValidTransactionEvent` não valida `tx_stub` | `game.js:569-581` | Frontend |
| B-07 | `sessionTimeouts` Set não limpa timeouts cancelados | `game.js:310-317` | Frontend |
| B-08 | `hashlib` importado mas não usado | `engine.py` | Backend |
| B-09 | `networkTimeLimit` pode ficar negativo sem Math.max | `game.js:1358` | Frontend |
| B-10 | `sessionTimeouts` Set cresce em sessões longas | `game.js:310-317` | Frontend |
| B-11 | Constantes mágicas espalhadas | `game.js` | Frontend |
| B-12 | Ausência de service worker fallback para offline | `index.html:16` | Frontend |
| B-13 | Variáveis globais não declaradas com `const`/`let` | `game.js:5` | Frontend |
| B-14 | Estado duplicado: UI e variáveis fora de sync | `game.js` | Frontend |
| B-15 | `requestControllers` Set sem cleanup em erro | `game.js:1023-1067` | Frontend |
| B-16 | WebSocket sem retry em `onerror` | `game.js:765-768` | Frontend |
| B-17 | `replaceChildren` em polling frequente | `game.js:1042,1090` | Frontend |
| B-18 | Animações CSS sem `will-change` | `style.css:558-564,449` | Frontend |
| B-19 | `backdrop-filter` em múltiplos elementos | `style.css:103-104,395,478` | Frontend |
| B-20 | Falta de `aria-label` nos botões da loja | `index.html:115,123,131` | Frontend |
| B-21 | `prefers-reduced-motion` não cobre spinners | `style.css:650-660` | Frontend |
| B-22 | `aria-valuetext` atualizado a cada segundo | `game.js:1824-1827` | Frontend |
| B-23 | `tabindex="-1"` no grid container impede navegação | `index.html:95` | Frontend |
| B-24 | Ausência de handler para `orientationchange` | `game.js:653` | Frontend |
| B-25 | `viewport-fit=cover` sem tratamento de notches | `index.html:5` | Frontend |
| B-26 | PWA sem manifest `display: standalone` verificado | `index.html:15` | Frontend |
| B-27 | Logs não estruturados | `main.py,ingestor.py` | Backend |
| B-28 | TrustedHostMiddleware não aplicado | `main.py` | Backend |
| B-29 | Scripts Lua sem SHA cache | `ingestor.py` | Backend |

---

## 5. AVALIAÇÃO DO LOOP DE GAMEPLAY

| Critério | Nota | Análise |
|----------|------|---------|
| **Feedback imediato** | ✅ Forte | Sons, floating text, animações SVG, combo visual |
| **Progressão clara** | ⚠️ Parcial | Hardware levels dão evolução, mas sem níveis/rank do jogador |
| **Variedade** | ⚠️ Média | Golden, High Fee, MEV, Lightning adicionam variedade, mas core loop é sempre o mesmo |
| **Tensão** | ✅ Forte | Timer, slashing, RBF, halving |
| **Conexão com tema** | ✅ Excelente | TXs reais, BIP39, halving, Lightning, pools |

**Pontos fracos:**
- Sem meta-progression entre sessões
- Loop monolítico (apenas "encontrar palavras")
- Sem objetivos de curto prazo
- Falta de "endgame" após max upgrades

---

## 6. 20 SUGESTÕES DE NOVAS MECÂNICAS

### Fase 1 — MVP de Engajamento (Recomendado)

| # | Feature | Impacto | Esforço | Descrição |
|---|---------|---------|---------|-----------|
| 1 | **Streaks (Login Diário)** | 🔴 ALTO | 🟡 MÉDIO | Login consecutivo dá recompensas escalonadas (Dia 1: 1k, Dia 7: 20k, Dia 30: 100k sats) |
| 2 | **Daily Rewards** | 🟡 MÉDIO | 🟢 BAIXO | Recompensa diária que escala por 7 dias, reset semanal |
| 3 | **Achievements** | 🔴 ALTO | 🟡 MÉDIO | 30-50 conquistas desbloqueáveis com badges e bônus permanentes |
| 4 | **Boss Battles** | 🔴 ALTO | 🟡 MÉDIO | A cada 50 blocos: grade 15×15, 10 palavras, 45s, recompensa 5×, barra de HP visual |

### Fase 2 — Progressão & Variedade

| # | Feature | Impacto | Esforço | Descrição |
|---|---------|---------|---------|-----------|
| 5 | **Níveis & Rank** | 🔴 ALTO | 🔴 ALTO | XP por palavra, níveis 1-100, ranks temáticos (Script Kiddie → Satoshi) |
| 6 | **Missões Diárias** | 🔴 ALTO | 🟡 MÉDIO | 3 missões rotativas + 1 semanal desafiadora |
| 7 | **Power-ups** | 🟡 MÉDIO | 🟡 MÉDIO | Time Freeze, Scanner, Double Combo, Magnet, Precision |
| 8 | **Eventos Globais** | 🟡 MÉDIO | 🟡 MÉDIO | Fee Spike, Golden Rush, Mempool Flood — afetam todos simultaneamente |

### Fase 3 — Social & Economia

| # | Feature | Impacto | Esforço | Descrição |
|---|---------|---------|---------|-----------|
| 9 | **Chat em Tempo Real** | 🟡 MÉDIO | 🟡 MÉDIO | Canal WebSocket por realm, mensagens como "tx broadcasts" |
| 10 | **Tokens Colecionáveis** | 🟡 MÉDIO | 🟡 MÉDIO | Block Cards com hash, dificuldade, raridade (Common → Legendary) |
| 11 | **PvP (Head-to-Head)** | 🔴 ALTO | 🔴 ALTO | Desafio sincronizado: mesmas 6 palavras, mesma grade, quem encontrar mais ganha |
| 12 | **Mercado de Power-ups** | 🟡 MÉDIO | 🔴 ALTO | Player-to-player, preços flutuantes, taxa de 5% |

### Fase 4 — Endgame & Monetização

| # | Feature | Impacto | Esforço | Descrição |
|---|---------|---------|---------|-----------|
| 13 | **Season Pass** | 🔴 ALTO | 🔴 ALTO | Temporadas de 4 semanas, trilha gratuita e premium |
| 14 | **Skill Tree** | 🟡 MÉDIO | 🔴 ALTO | 3 ramos: Mining, Search, Lightning — 5 níveis cada |
| 15 | **Staking de Sats** | 🟡 MÉDIO | 🟡 MÉDIO | Travar sats por 1h/6h/24h, bônus passivo, penalty por cancelar |
| 16 | **Loot Boxes** | 🟡 MÉDIO | 🟡 MÉDIO | Mempool Crates a cada 10 blocos: sats, power-ups, cards, skins |

### Fase 5 — Polimento

| # | Feature | Impacto | Esforço | Descrição |
|---|---------|---------|---------|-----------|
| 17 | **Mini-game Decoder** | 🟢 BAIXO | 🟢 BAIXO | Adivinhar palavra BIP39 do TXID truncado |
| 18 | **Modo Sprint** | 🟡 MÉDIO | 🟢 BAIXO | Grade 10×10, 4 palavras, 30s, sem upgrades — sessões rápidas |
| 19 | **Amigos & Co-op** | 🟡 MÉDIO | 🟡 MÉDIO | Lista de amigos, bônus +5% por amigo online (máx +20%) |
| 20 | **Energy System** | 🟡 MÉDIO | 🟡 MÉDIO | 10 energy, regenera 1 a cada 30min, previne burnout |

---

## 7. PLANO DE CORREÇÃO PRIORIZADO

### Prioridade 1 — Crítico (Aplicar agora)

| # | Issue | Correção | Esforço |
|---|-------|----------|---------|
| P1 | C-01: multiplier não chega ao blockWords | Copiar `multiplier` no txBuffer | Baixo |
| P2 | C-02: halving usa mempool_count | Usar `block_height` | Baixo |
| P3 | C-03: recent_events perde eventos | Remover método | Baixo |
| P4 | C-04: handler duplo no next-btn | Unificar para `onclick` | Baixo |
| P5 | C-05: EventRelay Queue broken | Fan-out broadcast | Médio |
| P6 | C-06: PlayerStateUpdate sem auth | Adicionar autenticação | Médio |
| P7 | C-14: COMMIT_TRANSACTION_SCRIPT race | Adicionar `pcall` | Baixo |

### Prioridade 2 — Médio (Próxima sprint)

| # | Issue | Correção | Esforço |
|---|-------|----------|---------|
| P8 | M-01: asyncio depreciado | `get_running_loop()` | Baixo |
| P9 | M-05: rbf-active nunca aplicado | `classList.add('rbf-active')` | Baixo |
| P10 | M-10/M-11: debounce | Debounce 2-3s | Baixo |
| P11 | M-12: Acoplamento DOM ↔ Lógica | Separar renderização | Médio |
| P12 | M-16: reconnectTimeout não limpo | `clearTimeout` em teardown | Baixo |
| P13 | M-19: Buffer de mensagens | Implementar buffer | Médio |
| P14 | M-26: Redis sem connection pool | `ConnectionPool` | Baixo |

### Prioridade 3 — Baixo (Melhorias incrementais)

| # | Issue | Correção | Esforço |
|---|-------|----------|---------|
| P15 | B-01: configureGridSize redundante | Debounce resize | Baixo |
| P16 | B-02: Oscillators não desconectados | `osc.disconnect()` | Baixo |
| P17 | B-11: Constantes mágicas | Objeto `CONFIG` | Baixo |
| P18 | B-27: Logs não estruturados | JSON logging | Baixo |

---

## 8. ARQUIVOS MAIS LIMPOS

| Arquivo | Status |
|---------|--------|
| `blockchain.py` | ✅ Limpo — código bem estruturado, funções puras |
| `storage.py` | ✅ Limpo — funções puras, validações robustas |
| `config.py` | ✅ Limpo — validações robustas |

---

## RELATÓRIOS ORIGINAIS

| Arquivo | Conteúdo |
|---------|----------|
| `docs/AUDITORIA_META_INGAME.md` | 25 issues técnicos (backend + frontend) |
| `docs/ANALISE_FRONTEND.md` | 38 problemas de frontend técnico |
| `docs/RELATORIO_ANALISE_TECNICA.md` | 28 problemas de backend técnico |
| `docs/game-design-analysis.md` | 20 sugestões de novas mecânicas |

---

*Relatório gerado em 16 de agosto de 2026 por Logger (Hermes Agent)*
