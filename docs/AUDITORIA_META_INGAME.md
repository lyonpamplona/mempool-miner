# MEMPOOL MINER — Auditoria Completa do Meta-in-Game

> Gerado em: 2026-08-16 | Arquivos analisados: 9 (3 frontend + 6 backend)
> Total de linhas: ~5.800 (JS: 1.921, CSS: 700, HTML: 178, Python: ~3.000)

---

## ÍNDICE

1. [CRÍTICOS — Funções quebradas / bugs de lógica](#1-críticos)
2. [MÉDIOS — Pontas soltas / comportamento incorreto](#2-médios)
3. [BAIXOS — Performance / inconsistências / código morto](#3-baixos)
4. [Resumo por arquivo](#4-resumo-por-arquivo)

---

## 1. CRÍTICOS

### C-01: `multiplier` do backend nunca chega ao `blockWords`
- **Tipo:** Função quebrada
- **Localização:** `game.js:897` + `game.js:1687`
- **Descrição:** O backend envia `multiplier` no evento `transaction_received` (calculado em `engine.py:194` como 5× para GOLDEN, 3× para HIGH FEE). Porém, ao empurrar para `txBuffer` (linha 897), o campo `multiplier` **não é copiado**. Depois, em `injectWordInGrid` (linha 1433), `blockWords.push()` também omite `multiplier`. Na validação (linha 1687), `match.multiplier || 1.0` sempre retorna `1.0`.
- **Impacto:** Recompensas GOLDEN (5×) e HIGH FEE (3×) são calculadas como 1×. Jogadores perdem até 80% da recompensa esperada em transações raras.
- **Sugestão:**
  ```js
  // game.js:897 — adicionar multiplier ao txBuffer
  txBuffer.push({ word: data.word, isHighFee: data.is_high_fee, isGolden: data.is_golden,
    vsize: data.vsize, isMev: data.is_mev, multiplier: data.multiplier });

  // game.js:1433 — passar multiplier para blockWords
  blockWords.push({ word, found: false, isHighFee, isGolden, startX, startY,
    hinted: false, isMev: isMev, multiplier: tx.multiplier || 1.0 });
  ```

### C-02: `is_halving_block` usa `mempool_count` em vez de altura do bloco
- **Tipo:** Função quebrada
- **Localização:** `ingestor.py:554`
- **Descrição:** O halving do Bitcoin ocorre a cada 210.000 **blocos**, não a cada 210.000 transações no mempool. O código faz `current_count % 210000 == 0` onde `current_count` é o tamanho do mempool (tipicamente 100–50.000). A chance de disparar é ~0.05% e completamente aleatória.
- **Impacto:** O evento visual de halving (flash laranja, anúncio) dispara de forma imprevisível ou nunca, quebrando a mecânica educativa da Fase 2.
- **Sugestão:** Usar o número do bloco do `getblockchaininfo`:
  ```python
  # ingestor.py:554 — usar blocks em vez de mempool_count
  block_height = info.get("blocks", 0) if info else 0
  "is_halving_block": (block_height % 210000 == 0),
  ```
  Nota: `info` já é obtido em `update_status()` mas não está disponível em `handle_block()`. Precisa ser passado ou consultado.

### C-03: `EventRelay.recent_events()` pode perder eventos (lógica de fila quebrada)
- **Tipo:** Função quebrada
- **Localização:** `main.py:828-845`
- **Descrição:** O método drena toda a fila para `items`, tenta reinsertar, mas se a fila atingir `maxsize=1000` durante a reinsersão, o `except QueueFull: break` silencia a perda. Eventos são descartados permanentemente. Além disso, o `while` com `tmp or (not tmp and self.queue.qsize() > 0)` é logicamente equivalente a `while self.queue.qsize() > 0` — `tmp` é sempre populado e nunca usado para decisão.
- **Impacto:** Em picos de tráfego, eventos são perdidos silenciosamente. Conexões WebSocket novas podem não receber eventos recentes.
- **Sugestão:** Remover `recent_events()` (não é chamado em nenhum lugar do código) ou reescrever usando `queue.copy()` se disponível, ou iterar sem remover:
  ```python
  def recent_events(self) -> list[str]:
      # Não drena — apenas retorna snapshot sem remover
      items = []
      try:
          while True:
              item = self.queue.get_nowait()
              items.append(item)
              self.queue.put_nowait(item)  # reinsere imediatamente
      except asyncio.QueueEmpty:
          pass
      return items
  ```

### C-04: Handler duplo no botão `next-btn` (addEventListener + onclick)
- **Tipo:** Função quebrada
- **Localização:** `game.js:634-637` + `game.js:1886-1920`
- **Descrição:** O botão `#next-btn` tem um `addEventListener('click')` permanente (linha 634) que chama `prepareNextBlock()`. Simultaneamente, `showOrphanBlockSalvage()` define `btn.onclick = rbfHandler` (linha 1920). Quando o modo RBF é ativo, o `addEventListener` verifica `isRbfMode` e retorna — OK. Porém, quando o usuário clica e **não tem saldo suficiente** para RBF (linha 1914-1917), `isRbfMode` é setado para `false` e `showResult(false, ...)` é chamado via `scheduleForSession`. Se o usuário clicar novamente antes dos 500ms, o `addEventListener` original chama `prepareNextBlock()` enquanto `showResult` ainda está pendente — estado inconsistente.
- **Impacto:** Em cenários de saldo insuficiente, o jogador pode pular o modal de resultado e ir direto para a próxima rodada sem feedback adequado.
- **Sugestão:** Usar um único mecanismo de handler. Remover o `addEventListener` do `next-btn` e gerenciar todos os estados via `onclick` com um estado machine claro:
  ```js
  // Remover game.js:634-637
  // document.getElementById('next-btn').addEventListener('click', ...);
  // Gerenciar tudo via btn.onclick em showResult e showOrphanBlockSalvage
  ```

---

## 2. MÉDIOS

### M-01: `asyncio.get_event_loop()` depreciado (Python 3.10+)
- **Tipo:** Inconsistência / depreciação
- **Localização:** `main.py:881` e `main.py:897`
- **Descrição:** `asyncio.get_event_loop()` está depreciado desde Python 3.10 e será removido em 3.12. O ambiente usa Python 3.13. Ambas as ocorrências estão em `ws_sender()`.
- **Impacto:** Funciona atualmente mas gera `DeprecationWarning`. Quebrará em Python 3.12+.
- **Sugestão:** Substituir por `asyncio.get_running_loop()`:
  ```python
  # main.py:881 e 897
  last_activity = asyncio.get_running_loop().time()
  ```

### M-02: `import asyncio as _asyncio` redundante dentro de função
- **Tipo:** Ponta solta
- **Localização:** `engine.py:272`
- **Descrição:** `validate_declared_network()` faz `import asyncio as _asyncio` localmente, embora `asyncio` já esteja importado no topo do módulo (linha 5). O alias `_asyncio` nunca é usado — o código usa `asyncio.sleep()` diretamente (linha 311).
- **Impacto:** Confusão de leitura, importação desnecessária.
- **Sugestão:** Remover a linha 272.

### M-03: `is_mev` não validado no frontend
- **Tipo:** Inconsistência
- **Localização:** `game.js:569-581`
- **Descrição:** `isValidTransactionEvent()` valida `word`, `is_high_fee`, `is_golden`, `vsize` mas não valida `is_mev`. O backend envia `is_mev` (engine.py:185) e o frontend o usa (game.js:897, 1380). Se o campo estiver ausente ou for do tipo errado, `data.is_mev` retorna `undefined` (falsy), o que é "seguro" mas não explícito.
- **Impacto:** Baixo — o fallback para `false` é aceitável, mas a validação incompleta viola o princípio de defesa em profundidade.
- **Sugestão:** Adicionar validação:
  ```js
  && (typeof data.is_mev === 'boolean' || data.is_mev === undefined)
  ```

### M-04: `COMMIT_STATUS_SCRIPT` escreve o mesmo snapshot duas vezes
- **Tipo:** Inconsistência
- **Localização:** `ingestor.py:89-101`
- **Descrição:** O script Lua faz `redis.call('set', KEYS[3], ARGV[3])` e `redis.call('set', KEYS[4], ARGV[3])` — o mesmo valor (`stored_snapshot`) é escrito em `node_status_key` E `realm_state_key`. Se uma chave for lida antes da outra em um momento de race, os dados são consistentes, mas a duplicação é custosa e confusa.
- **Impacto:** Leitura duplicada no Redis, manutenção mais difícil.
- **Sugestão:** Documentar por que ambas as chaves precisam do mesmo valor ou usar `COPY` do Redis se o objetivo é redundância.

### M-05: `rbf-active` CSS class definida mas nunca aplicada
- **Tipo:** Ponta solta
- **Localização:** `style.css:696-700`
- **Descrição:** A classe `.btn.rbf-active` define uma animação de pulso para o botão RBF, mas nenhum código JS adiciona esta classe ao botão `#next-btn`. O botão recebe estilos inline (`btn.style.display = 'inline-flex'`) mas nunca `classList.add('rbf-active')`.
- **Impacto:** A animação de urgência do RBF nunca é exibida.
- **Sugestão:** Em `showOrphanBlockSalvage()`, adicionar:
  ```js
  btn.classList.add('rbf-active');
  // E remover em rbfHandler:
  btn.classList.remove('rbf-active');
  ```

### M-06: `effectiveBaseReward` não resetado ao trocar de realm
- **Tipo:** Ponta solta
- **Localização:** `game.js:734-743` + `game.js:157`
- **Descrição:** Quando o jogador troca de rede (linha 734), `balanceSatoshis`, `hardwareLevel`, `networkTimeBonus` e `roundNumber` são resetados. Porém `effectiveBaseReward` (calculado em `buildPlayableBlock` com base em `roundNumber`) não é explicitamente resetado para `baseReward` (500). Como `roundNumber` volta a 1, o próximo `buildPlayableBlock` recalcula corretamente — mas se o jogador trocar de rede **durante** uma rodada em andamento, `effectiveBaseReward` mantém o valor antigo até a próxima chamada de `buildPlayableBlock`.
- **Impacto:** Baixo — só afeta se trocar de rede no meio de uma rodada (cenário raro).
- **Sugestão:** Adicionar `effectiveBaseReward = baseReward;` no bloco de reset de realm (linha 734).

### M-07: `validate_declared_network` importa `asyncio` localmente
- **Tipo:** Ponta solta
- **Localização:** `engine.py:272`
- **Descrição:** Já coberto em M-02. A linha `import asyncio as _asyncio` é morta — o alias nunca é referenciado.

### M-08: `recent_events()` nunca chamado
- **Tipo:** Ponta solta
- **Localização:** `main.py:828-845`
- **Descrição:** O método `EventRelay.recent_events()` é definido mas nunca invocado em nenhum lugar do código. Foi provavelmente deixado de uma iteração anterior onde novas conexões WebSocket recebiam eventos históricos.
- **Impacto:** Código morto que consome memória e pode causar bugs (ver C-03).
- **Sugestão:** Remover o método ou adicionar seu uso no handshake do WebSocket.

### M-09: `FORCE_STOP_SCRIPT` definido mas uso condicional
- **Tipo:** Ponta solta
- **Localização:** `ingestor.py:115-120` + `ingestor.py:729-737`
- **Descrição:** O script é usado como fallback quando `STOP_AND_RELEASE_SCRIPT` falha (lease expirada). Funciona corretamente, mas o script não verifica o token — se outro ingestor assumiu a lease, este script sobrescreve o status do novo dono.
- **Impacto:** Em cenários de crash/restart rápido, um ingestor antigo pode sobrescrever o status de um novo.
- **Sugestão:** Adicionar verificação de token ou TTL no `FORCE_STOP_SCRIPT`.

---

## 3. BAIXOS

### B-01: `configureGridSize` chamado redundante (resize + ResizeObserver)
- **Tipo:** Melhoria de performance
- **Localização:** `game.js:653` + `game.js:654-657`
- **Descrição:** `configureGridSize(currentGridSize)` é registrado como handler de `window.resize` E como callback de `ResizeObserver` no `gridWrapperEl`. Em um resize de janela, ambos disparam — o ResizeObserver pode fire múltiplas vezes por frame.
- **Impacto:** Cálculos redundantes de layout, especialmente em dispositivos móveis com virtual keyboards.
- **Sugestão:** Usar apenas `ResizeObserver` (mais preciso) ou adicionar debounce ao handler de resize:
  ```js
  let resizeRaf;
  window.addEventListener('resize', () => {
      cancelAnimationFrame(resizeRaf);
      resizeRaf = requestAnimationFrame(() => configureGridSize(currentGridSize));
  });
  ```

### B-02: `syncPlayerState` sem debounce/throttle
- **Tipo:** Melhoria de performance
- **Localização:** `game.js:1148-1173`
- **Descrição:** Chamado após cada palavra encontrada (linha 1723), cada compra na loja (linhas 1244, 1263, 1282, 1901) e ao carregar estado (linha 1196). Se o jogador encontrar 6 palavras rapidamente, 6 requisições HTTP são disparadas em sequência.
- **Impacto:** Overhead de rede, especialmente em conexões lentas. O backend processa cada uma individualmente.
- **Sugestão:** Adicionar debounce de 2-3 segundos:
  ```js
  let syncTimeout;
  function syncPlayerState() {
      clearTimeout(syncTimeout);
      syncTimeout = setTimeout(doSync, 2000);
  }
  ```

### B-03: `submitScore` sem debounce
- **Tipo:** Melhoria de performance
- **Localização:** `game.js:1121-1143`
- **Descrição:** Mesma issue de B-02. Chamado em `endSelection()` (linha 1721), `buyHint()` (1241), `buyHardware()` (1260), `buyLightning()` (1279) e ao expirar o timer (1830).
- **Impacto:** Múltiplas requisições POST redundantes em sequência.
- **Sugestão:** Mesma abordagem de debounce de B-02.

### B-04: Oscillators do Web Audio não desconectados explicitamente
- **Tipo:** Melhoria de performance
- **Localização:** `game.js:54-55`
- **Descrição:** `osc.stop()` é chamado mas `osc.disconnect()` não. O oscillator é coletado pelo GC eventualmente, mas em dispositivos com muitos sons rápidos, acumula nós de áudio não desconectados.
- **Impacto:** Baixo — memory leak lento no AudioContext.
- **Sugestão:** Adicionar `osc.disconnect(); gain.disconnect();` após `osc.stop()`.

### B-05: IDs HTML não referenciados pelo JS
- **Tipo:** Inconsistência
- **Localização:** `index.html`
- **Descrição:** Os seguintes IDs existem no HTML mas nunca são acessados via `getElementById` no JS:
  - `#game-panel` — usado apenas como anchor de navegação
  - `#grid-instructions` — referenciado apenas em `aria-describedby`
  - `#leaderboard-panel`, `#store-panel` — usados apenas para CSS `order`/`grid-column`
  - `#leaderboard-title`, `#store-title`, `#pools-title` — usados apenas em `aria-labelledby`
  - `#tutorial-title` — usado apenas em `aria-labelledby`
  - `#pwa-update-message` — usado apenas em `aria-labelledby`
- **Impacto:** Nenhum funcional — são usados para acessibilidade (ARIA) e CSS. Documentar que são intencionais.
- **Sugestão:** Adicionar comentário no HTML explicando que são IDs de acessibilidade/CSS.

### B-06: `hashlib` importado no `engine.py` mas não usado
- **Tipo:** Ponta solta
- **Localização:** `engine.py` — verificar imports
- **Descrição:** O módulo `engine.py` não importa `hashlib` (confirmando: não está nos imports). Porém, o comentário na docstring menciona "128 bits do TXID" e a função `tx_to_word` usa `bytes.fromhex()` — tudo correto. Sem issue aqui.
- **Impacto:** Nenhum.

### B-07: `networkTimeLimit` pode ficar negativo sem o `Math.max`
- **Tipo:** Melhoria de robustez
- **Localização:** `game.js:1358`
- **Descrição:** `networkTimeLimit = Math.max(networkTimeLimit - halvingPenalty, 15)` — o `Math.max(, 15)` protege contra valores negativos. Porém, em Lightning mode (linha 1348), `networkTimeLimit = 20` é setado **antes** do halving penalty. Com `roundNumber = 36+`, o penalty é 30, resultando em `Math.max(20 - 30, 15) = 15`. Funciona, mas a intenção de "Lightning = ultra rápido (20s)" é anulada pelo halving.
- **Impacto:** Lightning mode perde sua característica de ser mais rápido após ~16 rodadas.
- **Sugestão:** Aplicar halving penalty antes de Lightning mode ou usar um floor diferente para Lightning:
  ```js
  if (isLightningMode) {
      currentGridSize = 8;
      networkTimeLimit = Math.max(20 - halvingPenalty, 10); // floor menor para Lightning
  }
  ```

### B-08: `handleGridKeydown` fallback querySelector redundante
- **Tipo:** Inconsistência
- **Localização:** `game.js:1573-1575`
- **Descrição:** `grid[nextY]?.[nextX]?.element || gridEl.querySelector(...)` — o fallback `querySelector` nunca é necessário porque `grid[][]` é populado em `buildPlayableBlock` antes de qualquer interação. Se `grid` estiver vazio, `isPlaying` é false e o handler retorna antes.
- **Impacto:** Código defensivo excessivo que nunca executa.
- **Sugestão:** Remover o fallback ou manter como documentação de intenção.

### B-09: `isValidTransactionEvent` não valida `tx_stub`
- **Tipo:** Inconsistência
- **Localização:** `game.js:569-581`
- **Descrição:** O backend envia `tx_stub` no evento (ingestor.py:468) mas o frontend não o valida nem usa. O campo existe no contrato público (`PUBLIC_EVENT_FIELDS` em main.py:76-88) mas é ignorado.
- **Impacto:** Nenhum funcional — `tx_stub` é um campo cosmético não usado no frontend.
- **Sugestão:** Remover `tx_stub` do contrato público ou usá-lo no word bank para identificação visual.

### B-10: `sessionTimeouts` Set não limpa timeouts cancelados imediatamente
- **Tipo:** Melhoria de performance
- **Localização:** `game.js:310-317`
- **Descrição:** `scheduleForSession` adiciona o `timeoutId` ao Set, e o callback o remove. Mas se `cancelSessionTimeout` for chamado, o timeout é cleared mas o ID permanece no Set até `teardownSession` limpar tudo. Em sessões longas com muitos timeouts cancelados, o Set cresce.
- **Impacto:** Memory leak lento — insignificante na prática (< 100 IDs).
- **Sugestão:** Já funciona corretamente em `teardownSession`. Aceitável.

---

## 4. RESUMO POR ARQUIVO

### frontend/game.js (1.921 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Crítico | 2 | C-01 (multiplier), C-04 (handler duplo) |
| Médio | 5 | M-03 (is_mev), M-05 (rbf-active), M-06 (effectiveBaseReward), + 2 |
| Baixo | 6 | B-01, B-02, B-03, B-04, B-08, B-10 |

### frontend/style.css (700 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Médio | 1 | M-05 (.rbf-active nunca aplicada) |
| Baixo | 0 | CSS bem estruturado, todas as classes usadas |

### frontend/index.html (178 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Baixo | 1 | B-05 (IDs de acessibilidade não referenciados pelo JS) |

### backend/app/main.py (1.013 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Crítico | 1 | C-03 (recent_events) |
| Médio | 2 | M-01 (get_event_loop), M-08 (recent_events não chamado) |
| Baixo | 0 | |

### backend/app/ingestor.py (802 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Crítico | 1 | C-02 (is_halving_block) |
| Médio | 2 | M-04 (COMMIT_STATUS duplicado), M-09 (FORCE_STOP) |
| Baixo | 0 | |

### backend/app/engine.py (324 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Médio | 1 | M-02 (import asyncio redundante) |
| Baixo | 0 | |

### backend/app/blockchain.py (135 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Nenhum | 0 | Código limpo, bem documentado |

### backend/app/storage.py (122 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Nenhum | 0 | Código limpo, funções puras |

### backend/app/config.py (214 linhas)
| Severidade | Qtd | Items |
|---|---|---|
| Nenhum | 0 | Código limpo, validações robustas |

---

## TOTAIS

| Categoria | Contagem |
|---|---|
| **Críticos** | **4** |
| **Médios** | **11** |
| **Baixos** | **10** |
| **Total** | **25** |

### Prioridade de correção
1. **C-01** (multiplier) — impacto direto na economia do jogo
2. **C-02** (halving) — mecânica educativa quebrada
3. **C-03** (recent_events) — perda de eventos em produção
4. **C-04** (handler duplo) — estado inconsistente no RBF
5. **M-01** (depreciação) — quebra em Python 3.12+
6. **M-05** (rbf-active) — feedback visual faltando
7. **B-02/B-03** (debounce) — performance em rede lenta
