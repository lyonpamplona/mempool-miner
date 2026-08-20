# Audit: IDs do game.js vs Novo Design (new-design.html)

**Data:** 2026-08-19
**Objetivo:** Mapear todos os 149 IDs do game.js que NÃO existem no novo design e determinar ação para cada um.

---

## Resumo Executivo

| Categoria | Total IDs | Ativos | Remover | Adaptar |
|-----------|-----------|--------|---------|---------|
| Core Game (grid, race, modais) | 18 | 12 | 6 | 0 |
| Loja de Upgrades | 4 | 3 | 1 | 0 |
| Achievements | 8 | 8 | 0 | 0 |
| Boss Battles | 7 | 7 | 0 | 0 |
| Missões | 3 | 3 | 0 | 0 |
| Chat | 7 | 7 | 0 | 0 |
| Staking | 10 | 10 | 0 | 0 |
| Decoder | 10 | 10 | 0 | 0 |
| Skills Tree | 6 | 6 | 0 | 0 |
| Energy System | 4 | 4 | 0 | 0 |
| Season Pass | 12 | 12 | 0 | 0 |
| Cards/Colecionáveis | 9 | 9 | 0 | 0 |
| Market | 8 | 8 | 0 | 0 |
| Global Events | 6 | 6 | 0 | 0 |
| Sprint Mode | 5 | 5 | 0 | 0 |
| Friends | 6 | 6 | 0 | 0 |
| Crates/Loot Boxes | 5 | 5 | 0 | 0 |
| Powerups | 2 | 2 | 0 | 0 |
| Level System | 6 | 6 | 0 | 0 |
| Network Selection | 6 | 4 | 2 | 0 |
| PWA | 4 | 4 | 0 | 0 |
| Tutorial/Auth | 4 | 3 | 1 | 0 |
| **TOTAL** | **149** | **139** | **10** | **0** |

---

## Tabela Completa de IDs Faltantes

### 1. CORE GAME — Grid, Seleção, Palavras, Race Bar

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `word-bank-list` | Lista de palavras alvo (word bank) | SIM | Substituir | `tx-list-container` (nova design usa cards de TX como word bank) |
| `ui-network-progress` | Barra de progresso da corrida contra a rede | SIM | Substituir | `race-fill` |
| `ui-miner-name` | Nome do minerador | SIM | Substituir | `ui-operator-tag` |
| `ui-hardware` | Nível de hardware atual | SIM | Substituir | `ui-hw` |
| `game-status` | Região ARIA live para status do jogo | SIM | Criar novo | `game-status` (adicionar no footer) |
| `connectivity-status` | Indicador online/offline | SIM | Criar novo | `connectivity-status` (adicionar no footer) |
| `tx-loading` | Texto de loading "Recebendo transações" | SIM | Já existe | `tx-loading` (já está no novo design) |
| `hw-title` | Título do hardware na loja | SIM | Já existe | `hw-title` (já está no novo design) |
| `next-btn` | Botão "Próxima rodada" no modal de resultado | SIM | Substituir | Botão inline no `result-box` (nova design usa botão direto no HTML) |
| `btn-buy-hint` | Botão comprar dica | SIM | Já existe | `btn-buy-hint` |
| `btn-buy-hw` | Botão comprar hardware | SIM | Já existe | `btn-buy-hw` |
| `btn-buy-lightning` | Botão comprar Lightning | SIM | Substituir | `btn-buy-ln` |
| `result-modal` | Modal de resultado (block mined/orphan) | SIM | Já existe | `result-modal` |
| `result-title` | Título do modal de resultado | SIM | Já existe | `result-title` |
| `result-text` | Texto do modal de resultado | SIM | Já existe | `result-text` |
| `lightning-modal` | Modal de ativação do Lightning | SIM | Remover | Não há equivalente — nova design ativa Lightning inline sem modal |
| `lightning-text` | Texto do modal Lightning | SIM | Remover | Mesma razão acima |
| `miner-input` | Input de nome do minerador | SIM | Já existe | `miner-input` |

### 2. NETWORK SELECTION — Seleção de Rede

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `network-select` | Select de seleção de rede | SIM | Remover | Nova design não tem seleção de rede — usa auth direto |
| `network-status` | Status do nó selecionado | SIM | Remover | Mesma razão acima |
| `btn-start-session` | Botão "Iniciar sessão" | SIM | Remover | Nova design usa botão "EXECUTE_NODE" no auth modal |
| `ui-active-network` | Nome da rede ativa | SIM | Remover | Mesma razão acima |
| `ui-node-status` | Status do nó (conectando/pronta) | SIM | Adaptar | Integrar no footer como status |
| `btn-change-network` | Botão trocar rede | SIM | Remover | Nova design não tem troca de rede |

### 3. TUTORIAL / AUTH

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `tutorial-modal` | Modal de tutorial/login | SIM | Substituir | `auth-modal` |
| `tutorial-form` | Formulário do tutorial | SIM | Substituir | Formulário inline no `auth-modal` |
| `pool-tag-input` | Input de tag de pool | SIM | Remover | Nova design não tem pool tag — usa `[TAG] NOME` no input único |

### 4. PWA — Progressive Web App

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `btn-install-app` | Botão instalar PWA | SIM | Criar novo | `btn-install-app` (adicionar no header) |
| `pwa-update-banner` | Banner de atualização PWA | SIM | Criar novo | `pwa-update-banner` (adicionar como overlay) |
| `btn-update-app` | Botão atualizar app | SIM | Criar novo | `btn-update-app` (dentro do banner) |
| `btn-dismiss-update` | Botão descartar atualização | SIM | Criar novo | `btn-dismiss-update` (dentro do banner) |

### 5. ACHIEVEMENTS — Sistema de Conquistas (Fase 7)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `achievement-toast` | Toast de notificação de achievement | SIM | Criar novo | `achievement-toast` (overlay no topo) |
| `achievement-toast-icon` | Ícone do toast | SIM | Criar novo | `achievement-toast-icon` |
| `achievement-toast-title` | Título do toast | SIM | Criar novo | `achievement-toast-title` |
| `achievement-toast-desc` | Descrição do toast | SIM | Criar novo | `achievement-toast-desc` |
| `achievements-modal` | Modal de achievements | SIM | Criar novo | `achievements-modal` |
| `achievements-grid` | Grid de achievements | SIM | Criar novo | `achievements-grid` |
| `achievements-summary` | Resumo de progresso | SIM | Criar novo | `achievements-summary` |
| `achievements-filters` | Filtros por categoria | SIM | Criar novo | `achievements-filters` |
| `btn-achievements` | Botão abrir achievements | SIM | Criar novo | `btn-achievements` (na sidebar) |
| `btn-close-achievements` | Botão fechar achievements | SIM | Criar novo | `btn-close-achievements` |

### 6. BOSS BATTLES — Batalhas contra Boss (a cada 50 blocos)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `boss-hud` | HUD do boss (barra de HP + info) | SIM | Criar novo | `boss-hud` (overlay acima da grid) |
| `boss-hp-bar` | Barra de HP do boss | SIM | Criar novo | `boss-hp-bar` |
| `boss-hp-text` | Texto de HP (ex: "7/10") | SIM | Criar novo | `boss-hp-text` |
| `boss-defeat-modal` | Modal de derrota do boss | SIM | Criar novo | `boss-defeat-modal` |
| `boss-defeat-title` | Título do modal de derrota | SIM | Criar novo | `boss-defeat-title` |
| `boss-defeat-text` | Texto do modal de derrota | SIM | Criar novo | `boss-defeat-text` |
| `boss-defeat-btn` | Botão continuar após derrota | SIM | Criar novo | `boss-defeat-btn` |

### 7. MISSÕES DIÁRIAS & SEMANAIS (Fase 8)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `missions-panel` | Painel de missões | SIM | Criar novo | `missions-panel` (na aba NETWORK/tab-rank) |
| `missions-loading` | Estado de loading das missões | SIM | Criar novo | `missions-loading` |
| `missions-list` | Lista de missões | SIM | Criar novo | `missions-list` |

### 8. CHAT EM TEMPO REAL (Fase 9)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `chat-panel` | Painel de chat | SIM | Criar novo | `chat-panel` (na aba NETWORK) |
| `chat-messages` | Área de mensagens | SIM | Criar novo | `chat-messages` |
| `chat-input` | Input de mensagem | SIM | Criar novo | `chat-input` |
| `chat-send-btn` | Botão enviar | SIM | Criar novo | `chat-send-btn` |
| `chat-emoji-bar` | Barra de emojis temáticos | SIM | Criar novo | `chat-emoji-bar` |
| `chat-rate-info` | Info de rate limit | SIM | Criar novo | `chat-rate-info` |
| `btn-chat-toggle` | Botão toggle do chat | SIM | Criar novo | `btn-chat-toggle` |

### 9. STAKING DE SATS (Fase 10)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `staking-panel` | Painel de staking | SIM | Criar novo | `staking-panel` (na aba PROTOCOL/tab-info) |
| `staking-active` | Seção de stake ativo | SIM | Criar novo | `staking-active` |
| `staking-form` | Formulário de stake | SIM | Criar novo | `staking-form` |
| `staking-amount` | Valor staked | SIM | Criar novo | `staking-amount` |
| `staking-bonus` | Bônus de staking | SIM | Criar novo | `staking-bonus` |
| `staking-duration` | Duração do stake | SIM | Criar novo | `staking-duration` |
| `staking-timer` | Countdown do stake | SIM | Criar novo | `staking-timer` |
| `staking-amount-input` | Input de valor para stake | SIM | Criar novo | `staking-amount-input` |
| `btn-stake` | Botão realizar stake | SIM | Criar novo | `btn-stake` |
| `btn-cancel-stake` | Botão cancelar stake | SIM | Criar novo | `btn-cancel-stake` |
| `staking-history-list` | Histórico de stakes | SIM | Criar novo | `staking-history-list` |

### 10. DECODER — Mini-game de Decodificação

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `decoder-modal` | Modal do decoder | SIM | Criar novo | `decoder-modal` |
| `decoder-txid` | TXID truncado para decodificar | SIM | Criar novo | `decoder-txid` |
| `decoder-hint-letter` | Letra de dica | SIM | Criar novo | `decoder-hint-letter` |
| `decoder-timer-bar` | Barra de tempo | SIM | Criar novo | `decoder-timer-bar` |
| `decoder-timer-text` | Texto do timer | SIM | Criar novo | `decoder-timer-text` |
| `decoder-input` | Input de resposta | SIM | Criar novo | `decoder-input` |
| `btn-decoder-submit` | Botão enviar resposta | SIM | Criar novo | `btn-decoder-submit` |
| `decoder-feedback` | Feedback de acerto/erro | SIM | Criar novo | `decoder-feedback` |
| `decoder-streak` | Streak atual | SIM | Criar novo | `decoder-streak` |
| `decoder-wins` | Total de vitórias | SIM | Criar novo | `decoder-wins` |
| `btn-close-decoder` | Botão fechar decoder | SIM | Criar novo | `btn-close-decoder` |
| `btn-decoder-launch` | Botão iniciar decoder | SIM | Criar novo | `btn-decoder-launch` |

### 11. SKILLS TREE — Árvore de Habilidades

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `skills-panel` | Painel de skills | SIM | Criar novo | `skills-panel` (na aba PROTOCOL) |
| `skills-header` | Header com pontos e nível | SIM | Criar novo | `skills-header` |
| `skills-points-value` | Pontos disponíveis | SIM | Criar novo | `skills-points-value` |
| `skills-level-value` | Nível de skills | SIM | Criar novo | `skills-level-value` |
| `skills-loading` | Estado de loading | SIM | Criar novo | `skills-loading` |
| `skills-content` | Conteúdo da skill tree | SIM | Criar novo | `skills-content` |
| `btn-skills` | Botão abrir skills | SIM | Criar novo | `btn-skills` |

### 12. ENERGY SYSTEM — Sistema de Energia

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `ui-energy-bar` | Barra de energia | SIM | Criar novo | `ui-energy-bar` (no header) |
| `ui-energy-count` | Contador de energia | SIM | Criar novo | `ui-energy-count` |
| `ui-energy-timer` | Timer de regeneração | SIM | Criar novo | `ui-energy-timer` |
| `btn-buy-energy` | Botão comprar energia | SIM | Criar novo | `btn-buy-energy` |

### 13. SEASON PASS — Passaporte de Temporada

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `season-panel` | Painel de season pass | SIM | Criar novo | `season-panel` (na aba PROTOCOL) |
| `season-id-value` | ID da temporada | SIM | Criar novo | `season-id-value` |
| `season-level-value` | Nível na temporada | SIM | Criar novo | `season-level-value` |
| `season-xp-value` | XP na temporada | SIM | Criar novo | `season-xp-value` |
| `season-progress-bar` | Barra de progresso | SIM | Criar novo | `season-progress-bar` |
| `season-progress-fill` | Preenchimento da barra | SIM | Criar novo | `season-progress-fill` |
| `season-progress-text` | Texto de progresso | SIM | Criar novo | `season-progress-text` |
| `season-timer` | Timer da temporada | SIM | Criar novo | `season-timer` |
| `btn-buy-season-premium` | Botão comprar premium | SIM | Criar novo | `btn-buy-season-premium` |
| `season-loading` | Estado de loading | SIM | Criar novo | `season-loading` |
| `season-content` | Conteúdo da temporada | SIM | Criar novo | `season-content` |
| `season-rewards-free` | Recompensas grátis | SIM | Criar novo | `season-rewards-free` |
| `season-rewards-premium` | Recompensas premium | SIM | Criar novo | `season-rewards-premium` |
| `btn-season` | Botão abrir season | SIM | Criar novo | `btn-season` |

### 14. CARDS/COLECIONÁVEIS — Block Cards

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `cards-panel` | Painel de cards | SIM | Criar novo | `cards-panel` (na aba PROTOCOL) |
| `cards-total` | Total de cards | SIM | Criar novo | `cards-total` |
| `cards-common` | Contagem common | SIM | Criar novo | `cards-common` |
| `cards-rare` | Contagem rare | SIM | Criar novo | `cards-rare` |
| `cards-epic` | Contagem epic | SIM | Criar novo | `cards-epic` |
| `cards-legendary` | Contagem legendary | SIM | Criar novo | `cards-legendary` |
| `cards-bonus` | Bônus de coleção | SIM | Criar novo | `cards-bonus` |
| `cards-loading` | Estado de loading | SIM | Criar novo | `cards-loading` |
| `cards-grid` | Grid de cards | SIM | Criar novo | `cards-grid` |
| `btn-cards` | Botão abrir cards | SIM | Criar novo | `btn-cards` |

### 15. MARKET — Mercado de Power-ups

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `market-panel` | Painel do mercado | SIM | Criar novo | `market-panel` (na aba NETWORK) |
| `market-browse` | Lista de compras | SIM | Criar novo | `market-browse` |
| `market-sell` | Seção de venda | SIM | Criar novo | `market-sell` |
| `market-history` | Histórico de transações | SIM | Criar novo | `market-history` |
| `market-filter-powerup` | Filtro por tipo | SIM | Criar novo | `market-filter-powerup` |
| `btn-refresh-market` | Botão atualizar | SIM | Criar novo | `btn-refresh-market` |
| `market-sell-select` | Select de power-up para vender | SIM | Criar novo | `market-sell-select` |
| `market-sell-price` | Input de preço | SIM | Criar novo | `market-sell-price` |
| `btn-market-sell` | Botão vender | SIM | Criar novo | `btn-market-sell` |
| `btn-market` | Botão abrir mercado | SIM | Criar novo | `btn-market` |

### 16. GLOBAL EVENTS — Eventos Globais

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `global-event-banner` | Banner de evento global | SIM | Criar novo | `global-event-banner` (overlay no topo) |
| `global-event-icon` | Ícone do evento | SIM | Criar novo | `global-event-icon` |
| `global-event-label` | Label do evento | SIM | Criar novo | `global-event-label` |
| `global-event-description` | Descrição do evento | SIM | Criar novo | `global-event-description` |
| `global-event-countdown` | Countdown do evento | SIM | Criar novo | `global-event-countdown` |
| `btn-dismiss-event` | Botão descartar evento | SIM | Criar novo | `btn-dismiss-event` |

### 17. SPRINT MODE — Modo Sprint

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `btn-sprint-mode` | Botão toggle sprint | SIM | Criar novo | `btn-sprint-mode` |
| `sprint-timer-display` | Display do timer sprint | SIM | Criar novo | `sprint-timer-display` |
| `sprint-timer-value` | Valor do timer | SIM | Criar novo | `sprint-timer-value` |
| `sprint-leaderboard-list` | Leaderboard sprint | SIM | Criar novo | `sprint-leaderboard-list` |

### 18. FRIENDS — Sistema de Amigos

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `friends-panel` | Painel de amigos | SIM | Criar novo | `friends-panel` (na aba NETWORK) |
| `friends-add-input` | Input para adicionar amigo | SIM | Criar novo | `friends-add-input` |
| `btn-friends-add` | Botão adicionar | SIM | Criar novo | `btn-friends-add` |
| `friends-coop-bonus` | Bônus co-op | SIM | Criar novo | `friends-coop-bonus` |
| `friends-loading` | Estado de loading | SIM | Criar novo | `friends-loading` |
| `friends-list` | Lista de amigos | SIM | Criar novo | `friends-list` |
| `btn-friends` | Botão abrir amigos | SIM | Criar novo | `btn-friends` |

### 19. CRATES/LOOT BOXES — Mempool Crates

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `btn-open-crate-free` | Botão abrir crate grátis | SIM | Criar novo | `btn-open-crate-free` |
| `btn-open-crate-buy` | Botão comprar crate | SIM | Criar novo | `btn-open-crate-buy` |
| `crate-free-count` | Contador de crates grátis | SIM | Criar novo | `crate-free-count` |
| `crate-icon` | Ícone da crate aberta | SIM | Criar novo | `crate-icon` |
| `btn-close-crate` | Botão fechar crate | SIM | Criar novo | `btn-close-crate` |

### 20. POWERUPS — Sistema de Power-ups

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `btn-powerups-toggle` | Botão toggle power-ups | SIM | Criar novo | `btn-powerups-toggle` |
| `powerups-bar-container` | Container da barra de power-ups | SIM | Criar novo | `powerups-bar-container` |

### 21. LEVEL SYSTEM — Sistema de Níveis

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `level-bar-container` | Container da barra de nível | SIM | Criar novo | `level-bar-container` (no header) |
| `level-icon` | Ícone do rank | SIM | Criar novo | `level-icon` |
| `level-name` | Nome do rank | SIM | Criar novo | `level-name` |
| `level-value` | Nível atual | SIM | Criar novo | `level-value` |
| `level-bar-fill` | Preenchimento da barra XP | SIM | Criar novo | `level-bar-fill` |
| `level-bar-text` | Texto XP (ex: "50/100") | SIM | Criar novo | `level-bar-text` |

### 22. POOLS — Mining Pools (Fase 5)

| ID Faltante | Mecânica | Ativa? | Ação | ID no novo design |
|-------------|----------|--------|------|-------------------|
| `pools-list` | Lista de pools | SIM | Substituir | `pool-list` (já existe no novo design) |

---

## Análise por Prioridade de Implementação

### PRIORIDADE 1 — Core (sem estes o jogo não funciona)
Estes IDs são usados na lógica principal e precisam de mapeamento imediato:

- `word-bank-list` → `tx-list-container`
- `ui-network-progress` → `race-fill`
- `ui-miner-name` → `ui-operator-tag`
- `ui-hardware` → `ui-hw`
- `btn-buy-lightning` → `btn-buy-ln`
- `next-btn` → Botão inline no `result-box`
- `tutorial-modal` → `auth-modal`
- `tutorial-form` → Formulário no `auth-modal`
- `pools-list` → `pool-list`

### PRIORIDADE 2 — Funcionalidades Ativas (Fases 1-4)
Mecânicas que já estão no backend e precisam de UI:

- **Achievements** (10 IDs) — Backend ativo, precisa de modal + toast
- **Boss Battles** (7 IDs) — Backend ativo, precisa de HUD + modal
- **Missões** (3 IDs) — Backend ativo, precisa de painel
- **Decoder** (12 IDs) — Backend ativo, precisa de modal completo
- **Skills Tree** (7 IDs) — Backend ativo, precisa de painel
- **Level System** (6 IDs) — Backend ativo, precisa de barra no header

### PRIORIDADE 3 — Funcionalidades Sociais (Fases 5-10)
Mecânicas sociais e de progressão:

- **Chat** (7 IDs) — Backend ativo
- **Staking** (11 IDs) — Backend ativo
- **Friends** (7 IDs) — Backend ativo
- **Market** (10 IDs) — Backend ativo
- **Season Pass** (14 IDs) — Backend ativo
- **Cards** (10 IDs) — Backend ativo

### PRIORIDADE 4 — Funcionalidades Extras
Mecânicas opcionais e de engajamento:

- **Global Events** (6 IDs) — Backend ativo
- **Sprint Mode** (4 IDs) — Backend ativo
- **Crates** (5 IDs) — Backend ativo
- **Powerups** (2 IDs) — Backend ativo
- **Energy System** (4 IDs) — Backend ativo

### PRIORIDADE 5 — Infraestrutura
IDs de infraestrutura e compatibilidade:

- **PWA** (4 IDs) — Funcionalidade do navegador
- **Network Selection** (6 IDs) — Remover (nova design não usa)
- **Lightning Modal** (2 IDs) — Remover (ativação inline)

---

## Notas de Migração

1. **IDs que já existem no novo design e precisam de mapeamento:**
   - `word-bank-list` → `tx-list-container`
   - `ui-network-progress` → `race-fill`
   - `ui-miner-name` → `ui-operator-tag`
   - `ui-hardware` → `ui-hw`
   - `btn-buy-lightning` → `btn-buy-ln`
   - `tutorial-modal` → `auth-modal`
   - `pools-list` → `pool-list`

2. **IDs que devem ser REMOVIDOS (mecânica descontinuada):**
   - `network-select`, `network-status`, `btn-start-session`, `ui-active-network`, `btn-change-network` — Nova design não tem seleção de rede
   - `lightning-modal`, `lightning-text` — Nova design ativa Lightning inline
   - `pool-tag-input` — Nova design usa `[TAG] NOME` no input único
   - `next-btn` — Nova design usa botão inline no `result-box`

3. **IDs que precisam ser CRIADOS no novo design:**
   - Todos os IDs de Achievements, Boss Battles, Missões, Chat, Staking, Decoder, Skills, Energy, Season Pass, Cards, Market, Global Events, Sprint, Friends, Crates, Powerups, Level System
   - `game-status` e `connectivity-status` no footer
   - IDs de PWA no header

4. **Estratégia de integração:**
   - As abas do novo design (`tab-tx`, `tab-shop`, `tab-rank`, `tab-info`) devem ser estendidas para acomodar os painéis das mecânicas avançadas
   - `tab-rank` (NETWORK) → Leaderboard + Pools + Missões + Chat + Friends + Market
   - `tab-info` (PROTOCOL) → Info + Staking + Skills + Season Pass + Cards + Decoder
   - Modais (Achievements, Boss, Decoder, Crates) → Overlays independentes
   - Header → Level bar + Energy + PWA buttons
   - Footer → Game status + Connectivity
