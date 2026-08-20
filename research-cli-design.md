# Pesquisa de Design: Interfaces CLI/IDE para Mempool Miner

> **Data:** 17 de agosto de 2026
> **Objetivo:** Identificar padrões de design aplicáveis à interface do Mempool Miner — uma interface de jogo de mineração Bitcoin com tema terminal/IDE.

---

## 1. Padrões de Design CLI/IDE

### 1.1 Hierarquia de Informação por Camadas (Layered Information)

**Descrição:** Organizar informações em camadas de profundidade crescente — visão geral → detalhes → dados brutos. O usuário pode "aprofundar" conforme a necessidade.

**Exemplo:** O CLI do Specify mostra primeiro um resumo do sync, depois expande para regras processadas individualmente, e finalmente logs brutos.

**Aplicação no Mempool Miner:**
- **Camada 1 (HUD):** Hashrate, blocos encontrados, status da pool — sempre visível no topo
- **Camada 2 (Painel lateral):** Lista de workers, status de conexão, dificuldade atual
- **Camada 3 (Detalhes):** Transações na mempool, detalhes do bloco, logs de mineração

**Referências:**
- https://lucasfcosta.com/blog/ux-patterns-cli-tools
- https://yannglt.com/writing/designing-for-command-line-interface

---

### 1.2 Barra de Status Inferior (Bottom Status Bar)

**Descrição:** Padrão clássico de IDEs (VS Code, IntelliJ) e jogos RTS que mantém informações críticas sempre visíveis na parte inferior da tela.

**Exemplo:** VS Code mantém status bar com branch Git, encoding, linha/coluna. Age of Empires mantém barra inferior com recursos, unidades e comandos.

**Aplicação no Mempool Miner:**
- Barra inferior fixa com: status da conexão, hashrate atual, dificuldade, tempo desde o último bloco
- Indicadores coloridos: verde (online), amarelo (degradado), vermelho (offline)
- Hotkeys visíveis na barra para ações rápidas

**Referências:**
- https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
- https://waywardstrategy.com/2015/05/04/lets-talk-rts-user-interface-part-1-interview-with-dave-pottinger/

---

### 1.3 Progresso Visual com Spinners e Barras (Progress Indicators)

**Descrição:** Usar spinners para tarefas sem métrica definida, X/Y para tarefas com contagem conhecida, e barras de progresso para múltiplos processos simultâneos.

**Exemplo:** `cargo build` mostra spinner com nome do crate; `wget` mostra X/Y KB; múltiplos downloads com barras paralelas.

**Aplicação no Mempool Miner:**
- Spinner animado durante busca de blocos (sem métrica definida)
- Barra de progresso para sincronização de bloco (X/Y blocos)
- Barras paralelas para cada worker mostrando hashrate individual
- Indicador de "block found" com animação de confetti/celebração

**Referências:**
- https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays
- https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis

---

### 1.4 Código de Cores Semântico (Semantic Color Coding)

**Descrição:** Usar cores consistentes para transmitir significado — verde para sucesso, vermelho para erro, amarelo para aviso, azul para informação.

**Exemplo:** Yarn destaca partes da saída por semântica; NPM usa vermelho para erros com explicação clara.

**Aplicação no Mempool Miner:**
- **Verde:** Bloco encontrado, worker online, pool conectada
- **Vermelho:** Worker offline, erro de conexão, share rejeitada
- **Amarelo:** Dificuldade ajustando, alta latência, share próxima do limite
- **Azul/Ciano:** Informações informativas, hash do bloco, nonce
- **Laranja:** Alertas de temperatura, fan speed alto
- **Dourado/Amarelo brilhante:** Block found! — destaque máximo

**Referências:**
- https://lucasfcosta.com/blog/ux-patterns-cli-tools
- https://yannglt.com/writing/designing-for-command-line-interface

---

### 1.5 Tipografia Monoespaçada com Hierarquia de Peso (Monospace Typography)

**Descrição:** Usar fonte monoespaçada para alinhamento de colunas, com variação de peso (bold, regular, dim) para hierarquia visual.

**Exemplo:** Specify usa Fira Code com spacing cuidadoso, bold para títulos, dim (50% opacity) para texto secundário.

**Aplicação no Mempool Miner:**
- Fonte monoespaçada (Fira Code, JetBrains Mono, ou Monaspace)
- **Bold:** Títulos de seção, valores críticos (hashrate, reward)
- **Regular:** Dados normais, logs
- **Dim/Italic:** Timestamps, hashes longos, dados secundários
- Alinhamento em colunas para dados tabulares (workers, shares)

**Referências:**
- https://yannglt.com/writing/designing-for-command-line-interface
- https://github.com/davila7/claude-code-templates/blob/main/cli-tool/components/agents/development-team/cli-ui-designer.md

---

## 2. Padrões de Design Dark Dashboard

### 1.6 Fundo Escuro Elevado por Camadas (Lifted Dark Surfaces)

**Descrição:** Usar tons de cinza/azul escuro em vez de preto puro (#000), com camadas de superfície em diferentes níveis de luminosidade para criar profundidade.

**Exemplo:** Dashboard dark-first usa #0f172a (base), #1e293b (cards), #263449 (modais), #334155 (bordas).

**Aplicação no Mempool Miner:**
- Fundo principal: #0a0e17 (quase preto, mas não puro)
- Painéis/cards: #111827 (um passo mais claro)
- Painel ativo/selecionado: #1e293b (destaque)
- Bordas/separadores: #1f2937 (subtil)
- Cria profundidade sem sombras (que não funcionam em dark mode)

**Referências:**
- https://artofstyleframe.com/blog/dashboard-dark-mode-design-patterns/
- https://adminlte.io/blog/dark-dashboard-templates/

---

### 1.7 Paleta de Acentos Reservada para Significado (Reserved Accent Colors)

**Descrição:** Usar cores saturadas apenas para elementos significativos — status, gains/losses, calls to action. Desaturar tudo o resto.

**Exemplo:** Linear usa near-black surfaces com um único accent color; PostHog usa verde sparingly para guiar o olhar.

**Aplicação no Mempool Miner:**
- **Dourado (#f59e0b):** Bitcoin, rewards, block found — cor temática principal
- **Verde (#22c55e):** Shares aceitas, hashrate subindo
- **Vermelho (#ef4444):** Shares rejeitadas, erros
- **Ciano (#06b6d4):** Hashes, dados técnicos, links
- **Roxo (#a855f7):** Power users, configurações avançadas
- Fundo e painéis: desaturados para não competir com os acentos

**Referências:**
- https://artofstyleframe.com/blog/dashboard-dark-mode-design-patterns/
- https://adminlte.io/blog/dark-dashboard-templates/

---

### 1.8 Cards de Métricas com Destaque Visual (KPI Card Pattern)

**Descrição:** Métricas principais em cards destacados com ícone, valor grande, e tendência (seta para cima/baixo).

**Exemplo:** Dashboards financeiros e DevOps usam cards com KPIs grandes, cores de tendência, e sparklines.

**Aplicação no Mempool Miner:**
- Card "HASHRATE" com valor grande e sparkline dos últimos 24h
- Card "BLOCKS FOUND" com contador e tempo desde último bloco
- Card "REWARD" com BTC e valor em USD
- Card "SHARES" com ratio aceito/rejeitado
- Cards com borda colorida indicando status (verde=ótimo, amarelo=atenção, vermelho=problema)

**Referências:**
- https://adminlte.io/blog/dark-dashboard-templates/
- https://adminlte.io/blog/crypto-dashboard-templates/

---

## 3. Padrões de Design Crypto/Blockchain

### 1.9 Tabela de Dados Densos com Ordenação (Dense Data Tables)

**Descrição:** Tabelas compactas com múltiplas colunas, ordenação por clique, e destaque de linhas relevantes.

**Exemplo:** Etherscan mostra transações com hash, block, from/to, value, gas — tudo em tabela densa e ordenável.

**Aplicação no Mempool Miner:**
- Tabela de transações na mempool: hash, fee rate, size, age, RBF
- Tabela de workers: nome, hashrate, shares, uptime, status
- Tabela de blocos: height, hash, reward, timestamp, difficulty
- Ordenação por clique no header
- Highlight da transação/bloco mais recente

**Referências:**
- https://adminlte.io/blog/crypto-dashboard-templates/
- https://artofstyleframe.com/blog/dashboard-data-density-dense-table/

---

### 1.10 Gráfico de Velas (Candlestick Chart)

**Descrição:** Gráfico de velas para mostrar variação de métricas ao longo do tempo — aberto, fechado, máximo, mínimo.

**Exemplo:** TradingView e exchanges de crypto usam candlesticks para preço; podem ser adaptados para hashrate/dificuldade.

**Aplicação no Mempool Miner:**
- Gráfico de hashrate ao longo do tempo (velas de 1h, 4h, 24h)
- Velas verdes = hashrate acima da média, vermelhas = abaixo
- Overlay de dificuldade (linha) sobre o gráfico de hashrate
- Toggle entre diferentes períodos (1h, 24h, 7d, 30d)

**Referências:**
- https://adminlte.io/blog/crypto-dashboard-templates/
- https://www.tradingview.com/markets/cryptocurrencies/prices-all/

---

### 1.11 Minimap / Visão Geral (Minimap Overview)

**Descrição:** Uma visão compacta e sempre visível do estado geral do sistema, permitindo navegação rápida.

**Exemplo:** VS Code tem minimap à direita; jogos RTS têm minimap no canto inferior.

**Aplicação no Mempool Miner:**
- "Minimap" da blockchain: barra horizontal mostrando blocos recentes
- Blocos encontrados pelo usuário destacados em dourado
- Clique em um bloco para ver detalhes
- Mini-gráfico de hashrate na barra do minimap

**Referências:**
- https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
- https://waywardstrategy.com/2015/05/04/lets-talk-rts-user-interface-part-1-interview-with-dave-pottinger/

---

## 4. Padrões de Design Game HUD

### 1.12 HUD Contextual Dinâmico (Dynamic Contextual HUD)

**Descrição:** O HUD muda conteúdo e layout baseado no contexto atual do jogador — o que está selecionado, onde está, o que está acontecendo.

**Exemplo:** RTS games mostram comandos diferentes dependendo se você selecionou uma unidade, edifício, ou está no menu.

**Aplicação no Mempool Miner:**
- Se nenhum bloco selecionado: mostrar resumo geral (hashrate, blocks, reward)
- Se um bloco selecionado: mostrar detalhes do bloco (hash, transactions, reward)
- Se uma transação selecionada: mostrar mempool position, fee rate, size
- Se um worker selecionado: mostrar stats individuais, logs, temperatura
- Transições suaves entre estados contextuais

**Referências:**
- https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
- https://waywardstrategy.com/2015/05/04/lets-talk-rts-user-interface-part-1-interview-with-dave-pottinger/

---

### 1.13 Sistema de Hotkeys com Feedback Visual (Hotkey System with Visual Feedback)

**Descrição:** Cada comando tem um atalho de teclado visível na UI, com feedback visual imediato quando pressionado.

**Exemplo:** Rise of Nations tem hotkeys extensivos visíveis na UI; SC2 mostra hotkeys em todos os botões.

**Aplicação no Mempool Miner:**
- Hotkeys visíveis em todos os botões e menus (ex: [B]lock, [W]orker, [S]earch)
- Feedback visual: highlight do botão quando hotkey é pressionado
- Atalhos para ações frequentes: iniciar/parar mineração, refresh, fullscreen
- Configuração de hotkeys pelo usuário

**Referências:**
- https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
- https://waywardstrategy.com/2015/05/04/lets-talk-rts-user-interface-part-1-interview-with-dave-pottinger/

---

### 1.14 Notificações Não-Intrusivas (Non-Intrusive Notifications)

**Descrição:** Alertas que aparecem sem interrompir a experiência principal — toasts, badges, ou indicadores sutis.

**Exemplo:** Jogos mostram notificações no canto da tela; IDEs mostram badges em abas e ícones.

**Aplicação no Mempool Miner:**
- Toast notification no canto superior direito quando bloco é encontrado
- Badge com contador de shares rejeitadas no ícone do worker
- Indicador pulsante quando hashrate cai abaixo do esperado
- Som de celebração (opcional) ao encontrar bloco
- Notificações desaparecem automaticamente após 5 segundos

**Referências:**
- https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
- https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis

---

### 1.15 Feedback Imediato para Cada Ação (Reaction for Every Action)

**Descrição:** Cada ação do usuário gera uma resposta visual clara e imediata — confirmação, animação, ou mudança de estado.

**Exemplo:** Forge CLI mostra mensagem de sucesso após `forge logout`; git sugere comandos corretos após typos.

**Aplicação no Mempool Miner:**
- Animação de "share accepted" com checkmark verde quando share é aceita
- Shake animation + vermelho quando share é rejeitada
- Mensagem clara ao iniciar/parar mineração
- Sugerir próximo passo: "Próximo: configure seu worker com `miner worker add`"
- Correção automática de typos em comandos (como git faz)

**Referências:**
- https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis
- https://lucasfcosta.com/blog/ux-patterns-cli-tools

---

## Resumo: 15 Padrões Identificados

| # | Padrão | Categoria | Prioridade |
|---|--------|-----------|------------|
| 1 | Hierarquia de Informação por Camadas | CLI/IDE | Alta |
| 2 | Barra de Status Inferior | Game HUD | Alta |
| 3 | Progresso Visual (Spinners/Barras) | CLI/IDE | Alta |
| 4 | Código de Cores Semântico | CLI/IDE | Alta |
| 5 | Tipografia Monoespaçada com Hierarquia | CLI/IDE | Alta |
| 6 | Fundo Escuro Elevado por Camadas | Dark Dashboard | Alta |
| 7 | Paleta de Acentos Reservada | Dark Dashboard | Alta |
| 8 | Cards de Métricas com Destaque | Dark Dashboard | Média |
| 9 | Tabela de Dados Densos com Ordenação | Crypto | Média |
| 10 | Gráfico de Velas (Candlestick) | Crypto | Média |
| 11 | Minimap / Visão Geral | Game HUD | Média |
| 12 | HUD Contextual Dinâmico | Game HUD | Alta |
| 13 | Sistema de Hotkeys com Feedback | Game HUD | Alta |
| 14 | Notificações Não-Intrusivas | Game HUD | Média |
| 15 | Feedback Imediato para Cada Ação | CLI/IDE | Alta |

---

## Guia de Implementação Prioritária

### Fase 1 — Fundamentos (MVP)
1. **Fundo Escuro Elevado** — definir tokens de cor (#0a0e17 base, #111827 cards)
2. **Código de Cores Semântico** — mapear cores para significados
3. **Tipografia Monoespaçada** — escolher fonte e definir pesos
4. **Barra de Status Inferior** — hashrate, status, dificuldade
5. **Feedback Imediato** — confirmações visuais para cada ação

### Fase 2 — Dashboard
6. **Cards de Métricas** — hashrate, blocks, reward, shares
7. **Progresso Visual** — spinners e barras para processos
8. **HUD Contextual** — painéis que mudam conforme seleção
9. **Sistema de Hotkeys** — atalhos visíveis e funcionais

### Fase 3 — Avançado
10. **Tabelas Densas** — mempool, workers, blocos
11. **Gráfico de Velas** — hashrate ao longo do tempo
12. **Minimap** — visão geral da blockchain
13. **Notificações** — toasts e badges
14. **Hierarquia por Camadas** — drill-down de dados

---

## Referências Completas

### CLI/IDE Design
1. Lucas F. Costa — UX patterns for CLI tools: https://lucasfcosta.com/blog/ux-patterns-cli-tools
2. Evil Martians — CLI UX best practices (progress displays): https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays
3. Atlassian — 10 design principles for delightful CLIs: https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis
4. Yann-Edern Gillet — Designing for the Command Line Interface: https://yannglt.com/writing/designing-for-command-line-interface
5. CLI Guidelines (clig.dev): https://clig.dev/
6. Claude Code CLI UI Designer Template: https://github.com/davila7/claude-code-templates/blob/main/cli-tool/components/agents/development-team/cli-ui-designer.md

### Dark Dashboard Design
7. Art of Styleframe — Dashboard Dark Mode Patterns: https://artofstyleframe.com/blog/dashboard-dark-mode-design-patterns/
8. AdminLTE — 19 Best Dark Mode Dashboard Templates: https://adminlte.io/blog/dark-dashboard-templates/
9. AdminLTE — 10 Best Crypto & DeFi Dashboard Templates: https://adminlte.io/blog/crypto-dashboard-templates/

### Game HUD / RTS Design
10. Wayward Strategy — RTS UI Design Interview (Dave Pottinger): https://waywardstrategy.com/2015/05/04/lets-talk-rts-user-interface-part-1-interview-with-dave-pottinger/
11. Game Developer — UI Strategy Game Design Dos and Don'ts: https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts
12. Game Design Skills — RTS Game Design Fundamentals: https://gamedesignskills.com/game-design/real-time-strategy/

### Crypto/Blockchain UI
13. CoinMarketCap — Layout reference: https://coinmarketcap.com/
14. Etherscan — Block explorer reference: https://etherscan.io/
15. TradingView — Charting reference: https://www.tradingview.com/
16. DeFiLlama — DeFi analytics reference: https://defillama.com/
