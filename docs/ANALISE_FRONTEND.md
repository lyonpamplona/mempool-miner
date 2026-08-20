# Relatório de Análise Técnica — Mempool Miner Frontend

**Data:** 2026-08-16
**Arquivos analisados:** `frontend/index.html` (178 linhas), `frontend/game.js` (1921 linhas), `frontend/style.css` (700 linhas)
**Total de problemas identificados:** 38 (7 críticos, 14 médios, 17 baixos)

---

## Índice de Problemas por Categoria

| Categoria | Crítico | Médio | Baixo | Total |
|---|---|---|---|---|
| Arquitetura | 2 | 4 | 3 | 9 |
| Gerenciamento de Estado | 2 | 3 | 2 | 7 |
| WebSocket | 1 | 2 | 1 | 4 |
| Performance | 1 | 3 | 3 | 7 |
| Acessibilidade | 1 | 2 | 4 | 7 |
| Mobile | 0 | 0 | 4 | 4 |

---

## 1. ARQUITETURA DO CÓDIGO

### P-01 | Padrão God Object — arquivo monolítico
- **Localização:** `game.js` (linhas 1–1921)
- **Impacto:** **Crítico**
- **Descrição:** Todo o frontend (áudio, WebSocket, estado do jogo, UI, PWA, loja, grid, input, timer, leaderboard, pools, RBF, Lightning) está em um único arquivo de 1921 linhas sem separação de responsabilidades. Funções como `startSession()` (linhas 707–978) fazem 15 coisas diferentes: validação de input, teardown, WebSocket, handshake, timer de handshake, handlers de eventos, e inicialização de polling.
- **Sugestão:** Extrair módulos: `audio.js`, `websocket.js`, `state.js`, `grid.js`, `input.js`, `store.js`, `pwa.js`. Cada módulo expõe uma API mínima.

### P-02 | Ausência de padrão de gerenciamento de estado
- **Localização:** `game.js` (linhas 59–176)
- **Impacto:** **Crítico**
- **Descrição:** ~40 variáveis globais (`let`) espalhadas sem encapsulamento. O estado é mutável de qualquer função — `balanceSatoshis`, `isPlaying`, `comboMultiplier`, `hardwareLevel` podem ser alterados de qualquer lugar, sem validação de transições. Não há invariantes protegidos.
- **Sugestão:** Usar um objeto de estado imutável ou Proxy com validadores:
  ```js
  const state = new Proxy({ balance: 0, playing: false }, {
    set(target, key, value) { /* valida transição */ }
  });
  ```

### P-03 | Acoplamento direto DOM ↔ Lógica
- **Localização:** `game.js` (linhas 178–194, 602–623, 1367–1400)
- **Impacto:** **Médio**
- **Descrição:** Referências DOM são capturadas no topo do módulo (linhas 178–194) e usadas diretamente em funções de lógica. `buildPlayableBlock()` cria 144–225 elementos DOM inline, mistura layout com dados. `initEmptyGrid()` faz o mesmo. Não há separação entre modelo e view.
- **Sugestão:** Criar uma camada de renderização (`renderGrid(data)`, `renderBank(words)`) que recebe dados puros e produz DOM.

### P-04 | Funções com responsabilidade excessiva
- **Localização:** `game.js` — `startSession()` (707–978), `buildPlayableBlock()` (1331–1405), `endSelection()` (1667–1762)
- **Impacto:** **Médio**
- **Descrição:** `startSession()` tem 272 linhas e faz: validação de input, sanitização de strings, teardown de sessão anterior, reset de UI, criação de WebSocket, configuração de 4 handlers, handshake timeout, e inicialização de 3 intervalos de polling. Viola SRP.
- **Sugestão:** Decompor em: `validateInput()`, `sanitizeUsername()`, `resetForNewRealm()`, `createWebSocket()`, `setupWebSocketHandlers()`, `startPolling()`.

### P-05 | Duplicação de lógica de cleanup
- **Localização:** `game.js` — `teardownSession()` (441–496), `prepareNextBlock()` (1309–1326)
- **Impacto:** **Médio**
- **Descrição:** `prepareNextBlock()` repete lógica de cleanup que já existe em `teardownSession()`: limpa `selectedCells`, reseta `isSelecting`, `activePointerId`, `isPlaying`, `txBuffer`, `networkTimePassed`, `comboMultiplier`. Se uma nova variável for adicionada ao estado, ela precisa ser limpa em ambos os lugares.
- **Sugestão:** Extrair `resetGameUI()` e `resetGameState()` como funções únicas chamadas por ambos.

### P-06 | Testabilidade comprometida
- **Localização:** `game.js` (todo o arquivo)
- **Impacto:** **Médio**
- **Descrição:** Sem exports, sem injeção de dependências, sem mocks. O WebSocket é criado inline (`new WebSocket(gameSocketUrl(...))`), o DOM é acessado globalmente, e o tempo é controlado por `setInterval`/`setTimeout` sem clock fake. Testes unitários exigiriam um ambiente completo de navegador.
- **Sugestão:** Usar ES modules com `export`, injetar WebSocket factory, DOM factory, e clock. Ou pelo menos extrair lógica pura (cálculo de pontos, validação de palavras, geração de grid) para funções testáveis.

### P-07 | Constantes mágicas espalhadas
- **Localização:** `game.js` — linhas 59, 152–153, 162–163, 176, 897, 1680, 1685, 1689, 1693, 1859–1860
- **Impacto:** **Baixo**
- **Descrição:** Valores como `60` (segundos), `500` (recompensa base), `8000` (combo window), `10` (tempo de hardware), `50000` (MEV bonus), `100000` (RBF price) estão espalhados sem documentação centralizada.
- **Sugestão:** Consolidar em um objeto `CONFIG` no topo do arquivo com comentários explicativos.

### P-08 | Ausência de service worker fallback para offline
- **Localização:** `index.html` (linha 16), `game.js` (linha 244)
- **Impacto:** **Baixo**
- **Descrição:** O service worker é registrado (`registerPwa()`) mas não há estratégia de cache documentada. Se o SW não existir ou falhar, o jogo quebra completamente offline sem mensagem amigável.
- **Sugestão:** Adicionar fallback de cache-first para assets estáticos e network-first para API.

### P-09 | Variáveis globais não declaradas com `const`/`let`
- **Localização:** `game.js` — `audioContext` (linha 5)
- **Impacto:** **Baixo**
- **Descrição:** `audioContext` é declarada com `let` no topo mas usada como singleton. Em strict mode, não é problema, mas a semântica sugere que deveria ser uma variável privada em um closure ou módulo.
- **Sugestão:** Mover para dentro de um IIFE ou módulo ES.

---

## 2. GERENCIAMENTO DE ESTADO

### P-10 | Race condition: `sessionGeneration` vs handlers assíncronos
- **Localização:** `game.js` — `startSession()` (757–759), `socket.onmessage` (816–977)
- **Impacto:** **Crítico**
- **Descrição:** O padrão `generation !== sessionGeneration` protege contra execuções stale, mas há uma janela de race: quando `teardownSession()` incrementa `sessionGeneration` (linha 442), handlers de WebSocket já disparados podem ainda executar antes da verificação. O `handshakeTimeout` (linha 757) usa `scheduleForSession()` que verifica geração, mas `socket.onmessage` (linha 817) só verifica no início — se o handler demorar (ex: `buildPlayableBlock()`), o estado pode mudar durante a execução.
- **Sugestão:** Adicionar verificação de geração no meio de handlers longos, ou usar uma abordagem de cancelamento explícito com AbortController para cada mensagem.

### P-11 | Race condition: `isTransitioning` sem sincronização
- **Localização:** `game.js` — `buyLightning()` (1272), `buildPlayableBlock()` (1333), `socket.onmessage` (900)
- **Impacto:** **Crítico**
- **Descrição:** `isTransitioning` é usado como mutex para prevenir ações durante animações, mas é um booleano simples sem garantia de atomicidade. Se `buyLightning()` seta `isTransitioning = true` (linha 1272) e um evento `block_mined` chega antes do modal fechar, a condição `!isTransitioning` em `prepareNextBlock()` (linha 931) pode falhar silenciosamente. O flag é reset em `scheduleForSession()` (linha 1297) com delay de 1500ms — janela grande para eventos WebSocket.
- **Sugestão:** Usar uma Promise ou estado com máquina de estados finita: `IDLE | TRANSITIONING | PLAYING | PAUSED`.

### P-12 | Memory leak potencial: `reconnectTimeout` não limpo em teardown
- **Localização:** `game.js` — `socket.onclose` (804, 812), `teardownSession()` (441–496)
- **Impacto:** **Médio**
- **Descrição:** `reconnectTimeout` é declarado (linha 101) e usado em `socket.onclose` (linhas 804, 812), mas `teardownSession()` não faz `clearTimeout(reconnectTimeout)`. Se o usuário trocar de rede enquanto uma reconexão está pendente, o timeout dispara e chama `startSession()` com um realm antigo. A verificação `generation === sessionGeneration` (linha 805) mitiga parcialmente, mas o timeout continua ocupando memória.
- **Sugestão:** Adicionar `clearTimeout(reconnectTimeout)` em `teardownSession()` e setar `reconnectTimeout = null`.

### P-13 | Memory leak: `ResizeObserver` nunca desconectado
- **Localização:** `game.js` (linhas 654–657)
- **Impacto:** **Médio**
- **Descrição:** `gridResizeObserver` é criado e observa `gridWrapperEl`, mas nunca é desconectado em `teardownSession()` ou `pagehide`. Em navegadores que suportam `ResizeObserver`, isso mantém uma referência ao elemento e ao callback, impedindo garbage collection se o elemento for removido e recriado.
- **Sugestão:** Guardar referência e chamar `gridResizeObserver.disconnect()` em `teardownSession()`.

### P-14 | `sessionStorage` sem versionamento de schema
- **Localização:** `game.js` — `saveSessionState()` (116–131), `loadSessionState()` (133–139)
- **Impacto:** **Médio**
- **Descrição:** O estado salvo em `sessionStorage` não tem versão. Se o schema mudar (ex: adicionar/remover campos), `loadSessionState()` pode carregar dados incompatíveis. O `??` operator (linhas 670–676) mitiga parcialmente para campos novos, mas campos removidos podem causar comportamento inesperado.
- **Sugestão:** Adicionar `version` ao objeto salvo e validar na leitura:
  ```js
  if (raw.version !== CURRENT_SCHEMA_VERSION) return null;
  ```

### P-15 | Estado duplicado: UI e variáveis fora de sync
- **Localização:** `game.js` — `balanceSatoshis` vs `#ui-balance`, `comboMultiplier` vs `#ui-combo`
- **Impacto:** **Baixo**
- **Descrição:** O saldo é mantido em `balanceSatoshis` (variável) e `#ui-balance` (DOM) separadamente. Há ~15 locais onde `balanceSatoshis` é modificado e o DOM é atualizado manualmente. Se um `throw` ou `return` ocorrer entre a mutação e a atualização do DOM, o estado fica inconsistente.
- **Sugestão:** Criar função `setBalance(value)` que atualiza variável e DOM atomicamente, ou usar um observer no estado.

### P-16 | `requestControllers` Set sem cleanup em erro
- **Localização:** `game.js` — `fetchLeaderboard()` (1023–1067), `fetchPools()` (1073–1116)
- **Impacto:** **Baixo**
- **Descrição:** O bloco `finally` remove o controller do Set (linhas 1062, 1111), mas se `requestControllers.add(controller)` (linha 1031) falhar por algum motivo, o controller não está no Set e o `delete` em `finally` é inofensivo. O problema real é que `leaderboardRequestController` (variável global) pode apontar para um controller que já foi abortado, causando comportamento inconsistente na próxima chamada.
- **Sugestão:** Setar `leaderboardRequestController = undefined` antes de criar o novo controller, não apenas no finally.

---

## 3. WEBSOCKET

### P-17 | Ausência de heartbeat/ping-pong no WebSocket
- **Localização:** `game.js` — `startSession()` (755–977)
- **Impacto:** **Crítico**
- **Descrição:** Não há mecanismo de ping/pong no WebSocket. A detecção de conexão morta depende exclusivamente de `pollNetworkHealth()` (HTTP polling a cada 10s, linha 868), que é uma camada separada. Se o WebSocket ficar em estado "zombie" (conexão TCP aberta mas aplicação morta), `ws.readyState` continua `WebSocket.OPEN` e mensagens enviadas são silenciosamente perdidas. O `onclose` só dispara quando o TCP cai.
- **Sugestão:** Implementar ping/pong:
  ```js
  let lastPong = Date.now();
  const pingInterval = setInterval(() => {
    if (Date.now() - lastPong > 15000) {
      ws.close(4000, 'Heartbeat timeout');
    } else {
      ws.send(JSON.stringify({ action: 'ping' }));
    }
  }, 5000);
  socket.onmessage = (e) => {
    if (data.action === 'pong') lastPong = Date.now();
    // ...
  };
  ```

### P-18 | Buffer de mensagens não implementado
- **Localização:** `game.js` — `socket.onmessage` (816–977)
- **Impacto:** **Médio**
- **Descrição:** Quando `isPlaying` é `false` (ex: durante transição ou modal), mensagens `transaction_received` são descartadas silenciosamente (linha 886: `&& !isPlaying`). Se o backend enviar transações durante essa janela, elas são perdidas e nunca reenviadas. O `txBuffer` só acumula quando `!isPlaying` é falso, mas se o jogo estiver em `isTransitioning`, transações válidas são ignoradas.
- **Sugestão:** Implementar um buffer de mensagens pendentes que é processado quando o jogo volta ao estado receptivo, ou pedir replay ao backend na reconexão.

### P-19 | Reconexão sem jitter exponencial
- **Localização:** `game.js` — `socket.onclose` (789–813)
- **Impacto:** **Médio**
- **Descrição:** O backoff exponencial usa `baseDelay * Math.pow(2, reconnectAttempt - 1)` (linha 801) sem jitter aleatório. Se múltiplos clientes desconectarem simultaneamente (ex: restart do servidor), todos reconectarão nos mesmos intervalos, causando thundering herd.
- **Sugestão:** Adicionar jitter: `delay * (0.5 + Math.random())`.

### P-20 | WebSocket sem retry em `onerror`
- **Localização:** `game.js` — `socket.onerror` (765–768)
- **Impacto:** **Baixo**
- **Descrição:** `onerror` apenas loga o erro. A reconexão depende de `onclose` disparar, mas em alguns navegadores, erros de WebSocket não disparam `onclose` imediatamente (ex: erros de protocolo). O usuário pode ficar preso em estado "Conectando" sem feedback.
- **Sugestão:** Adicionar timeout em `onerror` que força `close()` se `onclose` não disparar em 3s.

---

## 4. PERFORMANCE

### P-21 | Reflow massivo na construção da grade
- **Localização:** `game.js` — `buildPlayableBlock()` (1367–1377), `initEmptyGrid()` (607–620)
- **Impacto:** **Crítico**
- **Descrição:** Cada célula é criada com `document.createElement('div')` e appendada individualmente com `gridEl.appendChild(cell)` (linha 1374). Para uma grade 15×15, são 225 operações de DOM que causam 225 reflows. O `configureGridSize()` (linha 1363) já forçou um reflow ao setar `gridTemplateColumns`.
- **Sugestão:** Usar `DocumentFragment` ou `innerHTML` com template string:
  ```js
  const fragment = document.createDocumentFragment();
  // ... criar células e appendar ao fragment
  gridEl.appendChild(fragment);
  ```

### P-22 | `querySelectorAll` em loop de foco
- **Localização:** `game.js` — `focusGridCell()` (1501–1506)
- **Impacto:** **Médio**
- **Descrição:** Toda vez que o foco muda (a cada movimento de seta ou toque), `gridEl.querySelectorAll('.cell[tabindex="0"]')` varre toda a grade para encontrar a célula com `tabindex="0"`. Em uma grade 15×15, isso é 225 elementos varridos a cada tecla pressionada.
- **Sugestão:** Manter referência à célula com `tabindex="0"` em uma variável e atualizar diretamente:
  ```js
  let focusedCell = null;
  function focusGridCell(cell) {
    if (focusedCell) focusedCell.tabIndex = -1;
    cell.tabIndex = 0;
    focusedCell = cell;
    cell.focus();
  }
  ```

### P-23 | `elementFromPoint` em `pointermove` sem throttle
- **Localização:** `game.js` — `handlePointerMove()` (1528–1534)
- **Impacto:** **Médio**
- **Descrição:** `getCellFromPoint()` chama `document.elementFromPoint()` (linha 1492) a cada evento `pointermove`. Em dispositivos touch, `pointermove` pode disparar 60–120 vezes por segundo durante um arraste. Cada chamada força o browser a fazer hit testing, que é uma operação cara.
- **Sugestão:** Throttle para 16ms (60fps) ou usar `getElementsFromPoint()` com cache. Alternativamente, calcular a célula baseada nas coordenadas e no layout da grade (matemática pura).

### P-24 | `replaceChildren` em polling frequente
- **Localização:** `game.js` — `fetchLeaderboard()` (1042), `fetchPools()` (1090)
- **Impacto:** **Baixo**
- **Descrição:** A cada 10s (leaderboard) e 15s (pools), `replaceChildren()` destrói e recria todos os elementos da lista. Se os dados não mudaram, isso causa reflow desnecessário e pisca visualmente.
- **Sugestão:** Diff seletivo: comparar dados antigos vs novos e atualizar apenas os itens que mudaram. Ou usar `requestIdleCallback` para atualizações não críticas.

### P-25 | Animações CSS sem `will-change`
- **Localização:** `style.css` — `.floating-text` (558–564), `.cell.selected` (449)
- **Impacto:** **Baixo**
- **Descrição:** `.floating-text` usa `transform` e `opacity` em animação, e `.cell.selected` usa `transform: scale(1.08)`. Sem `will-change`, o browser pode não promover essas camadas para composited layers, causando repaints na GPU.
- **Sugestão:** Adicionar `will-change: transform, opacity` aos elementos animados. Remover após a animação com `animationend`.

### P-26 | `backdrop-filter` em múltiplos elementos
- **Localização:** `style.css` — `.glass-panel` (103–104), `.grid-overlay` (395), `.modal-overlay` (478)
- **Impacto:** **Baixo**
- **Descrição:** `backdrop-filter: blur()` é aplicado a ~10 elementos `.glass-panel` simultaneamente. Em dispositivos móveis, cada `backdrop-filter` cria uma camada de composição separada, consumindo memória GPU. Em dispositivos fracos, isso causa jank.
- **Sugestão:** Usar `backdrop-filter` apenas nos painéis visíveis, ou substituir por `background: rgba()` com opacidade em dispositivos sem suporte hardware.

### P-27 | Event delegation ausente na grade
- **Localização:** `game.js` — `handlePointerStart()` (1511–1523), `handleGridKeydown()` (1557–1608)
- **Impacto:** **Médio** → já usa delegation via `gridEl.addEventListener` (linhas 647–649)
- **Descrição:** Na verdade, os eventos de pointer e keyboard já usam delegation no container `gridEl`. Porém, `handlePointerStart` usa `event.target.closest('.cell')` (linha 1517) que faz traversal no DOM a cada toque. Para 225 células, o traversal é curto, mas ainda assim pode ser otimizado.
- **Sugestão:** Aceitável como está. O traversal é O(depth) e a profundidade é 1–2 níveis.

---

## 5. ACESSIBILIDADE

### P-28 | `role="grid"` sem `role="row"` e `role="gridcell"` sem ordem de tabulação correta
- **Localização:** `game.js` — `buildPlayableBlock()` (1372–1373), `initEmptyGrid()` (615–616)
- **Impacto:** **Crítico**
- **Descrição:** O grid usa `role="grid"` no container (linha 95 do HTML) e `role="gridcell"` nas células, mas não tem `role="row"` nos intermediários. Segundo o ARIA spec, grids devem ter a estrutura: `grid > row > gridcell`. Sem rows, screen readers não anunciam a posição corretamente. Além disso, apenas a célula (0,0) tem `tabindex="0"` — o usuário de teclado precisa navegar célula por célula com setas, mas o foco não é gerenciado como um grid ARIA nativo esperaria.
- **Sugestão:** Adicionar wrapper `<div role="row">` para cada linha, ou usar `<table>` semântico. Implementar roving tabindex pattern corretamente.

### P-29 | `aria-live="polite"` em elementos atualizados com frequência
- **Localização:** `index.html` — `#leaderboard-list` (linha 74), `#pools-list` (linha 79), `#word-bank-list` (linha 88)
- **Impacto:** **Médio**
- **Descrição:** `aria-live="polite"` em containers que são completamente substituídos a cada 10–15s (`replaceChildren`). Screen readers anunciarão toda a lista a cada atualização, mesmo quando nada mudou. Isso é particularmente problemático para o leaderboard, onde os dados raramente mudam entre polls.
- **Sugestão:** Remover `aria-live` dos containers de polling e usar `aria-atomic="true"` apenas no `#game-status` que já tem. Ou verificar se os dados mudaram antes de atualizar o DOM.

### P-30 | Contraste de cor insuficiente em `.wallet-label`
- **Localização:** `style.css` — `.wallet-label` (188–194)
- **Impacto:** **Médio**
- **Descrição:** `color: var(--text-muted)` onde `--text-muted: #94a3b8` sobre `--bg-dark: #050505`. O contraste é ~4.6:1, que passa WCAG AA para texto normal mas falha para texto pequeno (10px, linha 190). O requisito para texto < 18px é 4.5:1, e o valor real de `#94a3b8` sobre `#050505` é aproximadamente 7.5:1 — na verdade passa. Porém, `.node-status` (linha 222) usa `font-size: 10px` com `color: var(--text-muted)` e `text-transform: uppercase`, o que reduz a legibilidade.
- **Sugestão:** Aumentar `font-size` para mínimo 12px em labels, ou usar `--text-main` para labels críticos.

### P-31 | Falta de `aria-label` nos botões da loja
- **Localização:** `index.html` — `#btn-buy-hint` (115), `#btn-buy-hw` (123), `#btn-buy-lightning` (131)
- **Impacto:** **Baixo**
- **Descrição:** Os botões da loja têm texto visível ("5,000 SATS", "100,000 SATS") mas sem `aria-label` descritivo. O texto do botão é apenas o preço, não a ação. Screen readers anunciam "5,000 SATS button" sem contexto de qual upgrade está sendo comprado.
- **Sugestão:** Adicionar `aria-label="Comprar dica por 5.000 sats"` etc., ou mudar o texto do botão para "Comprar — 5,000 SATS".

### P-32 | `prefers-reduced-motion` não cobre `animation-iteration-count` para spinners
- **Localização:** `style.css` — `@media (prefers-reduced-motion: reduce)` (650–660)
- **Impacto:** **Baixo**
- **Descrição:** O media query reduz `animation-duration` para 0.01ms e `animation-iteration-count` para 1, mas o spinner de loading (`.loader-spinner`, linha 406) continua "animando" por 0.01ms — o que pode causar um flash visual. Para spinners, o ideal é `animation: none` ou `opacity: 1` fixo.
- **Sugestão:** Adicionar regra específica:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .loader-spinner { animation: none; border-color: var(--btc-orange); }
  }
  ```

### P-33 | `aria-valuetext` atualizado a cada segundo no progress bar
- **Localização:** `game.js` — `startNetworkRace()` (1824–1827)
- **Impacto:** **Baixo**
- **Descrição:** `aria-valuetext` é atualizado a cada segundo com "X segundos restantes". Screen readers com `aria-live` podem anunciar essa mudança a cada segundo, interrompendo o usuário. Como o elemento tem `role="progressbar"` sem `aria-live` explícito, o comportamento depende do user agent.
- **Sugestão:** Atualizar `aria-valuetext` apenas em marcos (30s, 15s, 5s, 0s) ou remover `aria-valuetext` e confiar em `aria-valuenow`.

### P-34 | `tabindex="-1"` no grid container impede navegação por teclado
- **Localização:** `index.html` — `#word-grid` (linha 95)
- **Impacto:** **Baixo**
- **Descrição:** O container do grid tem `tabindex="-1"` e `role="grid"`. Isso impede que o grid receba foco via Tab, forçando o usuário a navegar diretamente para as células. Como apenas a célula (0,0) tem `tabindex="0"`, o usuário de teclado pode pular o grid completamente se não houver um link ou botão antes dele.
- **Sugestão:** Remover `tabindex="-1"` do container e confiar no roving tabindex das células, ou adicionar um botão "Iniciar seleção" antes do grid.

---

## 6. MOBILE

### P-35 | `touch-action: none` na grade bloqueia scroll nativo
- **Localização:** `style.css` — `.word-grid` (429)
- **Impacto:** **Baixo**
- **Descrição:** `touch-action: none` na grade desabilita todos os gestos nativos do browser (scroll, zoom, swipe-back). Se a grade ocupar toda a tela em mobile, o usuário não consegue rolar a página enquanto o dedo está sobre a grade. O `event.preventDefault()` em `handlePointerStart` (linha 1519) e `handlePointerMove` (linha 1530) reforça esse bloqueio.
- **Sugestão:** Usar `touch-action: manipulation` em vez de `none`, ou remover `preventDefault()` quando o toque não está selecionando.

### P-36 | Ausência de handler para `orientationchange`
- **Localização:** `game.js` — `window.addEventListener('resize')` (linha 653)
- **Impacto:** **Baixo**
- **Descrição:** O resize handler chama `configureGridSize(currentGridSize)` que recalcula o tamanho das células. Em rotação de tela, o `ResizeObserver` (linha 655) também dispara. Porém, não há handler específico para `orientationchange`, que em alguns navegadores mobile dispara antes do `resize`. A grade pode ficar com células incorretas por alguns frames durante a rotação.
- **Sugestão:** Adicionar `window.addEventListener('orientationchange', () => configureGridSize(currentGridSize))` como fallback.

### P-37 | `viewport-fit=cover` sem tratamento de notches em elementos fixos
- **Localização:** `index.html` (linha 5), `style.css` — `.mobile-nav` (566–575), `.update-banner` (150–161)
- **Impacto:** **Baixo**
- **Descrição:** O viewport usa `viewport-fit=cover` e os elementos fixos usam `env(safe-area-inset-*)` para padding. Isso está correto para iOS. Porém, em Android com notches, `env(safe-area-inset-*)` pode retornar 0 em alguns browsers, fazendo conteúdo ser cortado.
- **Sugestão:** Adicionar fallback com `constant(safe-area-inset-*)` para iOS < 11.1 e testar em dispositivos Android com notch.

### P-38 | PWA sem manifest `display: standalone` verificado
- **Localização:** `index.html` (linha 15)
- **Impacto:** **Baixo**
- **Descrição:** O manifest é referenciado (`manifest.webmanifest`) mas não foi analisado. Se o manifest não tiver `"display": "standalone"` ou `"fullscreen"`, o app instalado mostrará a barra de navegação do browser, reduzindo o espaço disponível e quebrando o layout que assume tela cheia.
- **Sugestão:** Verificar que `manifest.webmanifest` contém `"display": "standalone"` e `"orientation": "any"`.

---

## Resumo de Prioridades

### Corrigir imediatamente (Crítico):
1. **P-01** — Modularizar o código monolítico
2. **P-02** — Implementar gerenciamento de estado com encapsulamento
3. **P-10** — Proteger race conditions em handlers assíncronos
4. **P-11** — Substituir `isTransitioning` por máquina de estados
5. **P-17** — Implementar heartbeat/ping-pong no WebSocket
6. **P-21** — Usar `DocumentFragment` para construção da grade
7. **P-28** — Adicionar `role="row"` na estrutura do grid ARIA

### Corrigir na próxima sprint (Médio):
1. **P-03** — Separar lógica de renderização
2. **P-04** — Decompor funções grandes
3. **P-05** — Unificar lógica de cleanup
4. **P-12** — Limpar `reconnectTimeout` em teardown
5. **P-13** — Desconectar `ResizeObserver` em teardown
6. **P-18** — Implementar buffer de mensagens WebSocket
7. **P-19** — Adicionar jitter na reconexão
8. **P-22** — Otimizar `focusGridCell` com referência direta
9. **P-23** — Throttle `elementFromPoint` em pointermove
10. **P-29** — Remover `aria-live` de containers de polling
11. **P-30** — Revisar contraste de labels pequenos

### Melhorias incrementais (Baixo):
1. **P-07** — Consolidar constantes mágicas
2. **P-08** — Adicionar fallback offline no SW
3. **P-09** — Encapsular `audioContext`
4. **P-14** — Versionar schema do sessionStorage
5. **P-15** — Criar setter atômico para balance
6. **P-16** — Resetar controller antes de criar novo
7. **P-20** — Adicionar timeout em `onerror` do WebSocket
8. **P-24** — Diff seletivo no leaderboard
9. **P-25** — Adicionar `will-change` em animações
10. **P-26** — Otimizar `backdrop-filter` em mobile
11. **P-31** — Adicionar `aria-label` nos botões da loja
12. **P-32** — Tratar spinner no `prefers-reduced-motion`
13. **P-33** — Atualizar `aria-valuetext` em marcos
14. **P-34** — Revisar `tabindex` no grid container
15. **P-35** — Ajustar `touch-action` na grade
16. **P-36** — Adicionar handler `orientationchange`
17. **P-37** — Fallback para safe areas no Android
18. **P-38** — Verificar manifest PWA

---

## Pontos Positivos (o que está bem feito)

1. **PWA completo:** Manifest, service worker, install prompt, update banner — implementação sólida.
2. **Acessibilidade parcial:** Skip link, `aria-live`, `aria-hidden` em modais, trap focus, `prefers-reduced-motion`, `forced-colors`.
3. **Geração de sessão:** O padrão `sessionGeneration` para invalidar callbacks stale é uma boa prática.
4. **AbortController:** Uso consistente em todas as requisições HTTP com cleanup em `teardownSession()`.
5. **Validação de input:** Sanitização de username e pool tag com Unicode regex (linhas 716–724).
6. **Validação de dados:** `isValidTransactionEvent()` e `isValidLeaderboardPayload()` protegem contra payloads malformados.
7. **Pointer Events:** Uso correto de Pointer Events (não touch/mouse separados) com `isPrimary`, `pointerType`, e captura.
8. **CSS moderno:** `clamp()`, `env(safe-area-inset-*)`, `dvh`, `contain: layout paint`, `color-scheme`.
9. **Teardown robusto:** `teardownSession()` limpa intervalos, timeouts, controllers, WebSocket, e estado de forma abrangente.
10. **Realm scoping:** Mensagens WebSocket são validadas contra `activeRealmId` (linha 833), prevenindo cross-realm injection.
