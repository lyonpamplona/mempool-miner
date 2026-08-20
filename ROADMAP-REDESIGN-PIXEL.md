# ROADMAP: Redesign Pixel Art — Migração para o Código Principal

**Data:** 19/08/2026
**Objetivo:** Aplicar o redesign pixel art (protótipo v3) no código principal do Mempool Miner, mantendo TODAS as mecânicas ativas funcionais.

---

## 1. MECÂNICAS ATIVAS IDENTIFICADAS

### Core (Jogo Principal)
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Grid de caça-palavras | `game.js` | 12x12, 15x15, 8x8 (Lightning) |
| Word Bank | `game.js` | Transações pendentes (6 por bloco) |
| Race Track | `game.js` | Barra de progresso vs rede |
| Slashing | `game.js` | 3 erros = -5% saldo |
| Combo | `game.js` | Multiplicador até 4.0x |
| MEV Secreto | `game.js` | Palavras ocultas = +50k sats |
| RBF | `game.js` | Resgate de bloco órfão (100k sats) |
| Halving | `game.js` | Recompensa decresce 2% a cada 10 blocos |
| Lightning Mode | `game.js` | Grid 8x8, 10x rewards, 5 blocos |
| Frenzy Mode | `game.js` | Ativa no combo 4.0x |

### Fase 2: Níveis & Power-ups
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Sistema de Níveis & Rank | `game.js` | Barra de XP, ranks |
| Power-ups Temporários | `game.js` | Hint, Time Freeze |

### Fase 3: Estado do Jogador
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Estado do Jogador | `game.js` | Persistência via Redis |
| Lightning Channel | `game.js` | Canal dura N blocos |
| PvP | `game.js` | Desafios head-to-head |

### Fase 4: Leaderboard
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Leaderboard Epochs | `game.js` | Reset a cada 2016 blocos |

### Fase 5: Social
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Mining Pools | `game.js` | Guildas por prefixo [PoolName] |
| Modo Sprint | `game.js` | Leaderboard temporário |
| Sistema de Amigos | `game.js` | Co-op, status online |

### Fase 6: MEV
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| MEV Secreto | `game.js` | Palavras ocultas no grid |

### Fase 7: Achievements
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Achievements | `game.js` | Sistema de conquistas |
| Toast Notifications | `game.js` | Notificações de desbloqueio |

### Fase 8: Eventos & Missões
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Eventos Globais | `game.js` | Banner de eventos |
| Missões Diárias/Semanais | `game.js` | Tracking de progresso |

### Fase 9: Social Avançado
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Chat em Tempo Real | `game.js` | WebSocket, emojis |
| Block Cards | `game.js` | Tokens colecionáveis |
| PvP Arena | `game.js` | Desafios head-to-head |

### Fase 10: Progressão
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Skill Tree | `game.js` | Árvore de habilidades |
| Staking | `game.js` | Travar sats para bônus |
| Mempool Crates | `game.js` | Loot boxes |
| Season Pass | `game.js` | Temporada com tiers |

### Fase 11: Energia & Online
| Mecânica | Arquivo | Descrição |
|----------|---------|-----------|
| Energy System | `game.js` | Energia limitada, recarga |
| Online Status | `game.js` | Heartbeat, status online |

---

## 2. ARQUITETURA ATUAL vs NOVA

### Atual (index.html: 710 linhas, style.css: 4754 linhas, game.js: 6067 linhas)
```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (dashboard)                                          │
│  ├─ Operador, Saldo, Rodada, Hardware, Combo, Rede, Sprint │
│  ├─ Barra XP (Fase 2)                                      │
│  ├─ Energia (Fase 11)                                       │
│  └─ Power-ups (Fase 2)                                      │
├─────────────────────────────────────────────────────────────┤
│ RACE TRACK                                                  │
├─────────────────────────────────────────────────────────────┤
│ MAIN LAYOUT (3 colunas empilhadas em mobile)                │
│  ├─ Leaderboard (Top 10, Pools)                             │
│  ├─ Game Area (Word Bank, Grid, Boss HUD)                   │
│  ├─ Store (Hint, Hardware, Lightning, Energia, Crate)       │
│  ├─ Market (Comprar, Vender, Histórico)                     │
│  ├─ Missões (Diárias, Semanais)                             │
│  ├─ Skills (Skill Tree)                                     │
│  ├─ Staking (Stake ativo, Formulário, Histórico)            │
│  ├─ Chat (Mensagens, Input, Emojis)                         │
│  └─ PvP (Desafios)                                          │
├─────────────────────────────────────────────────────────────┤
│ MOBILE NAV (Grade, Ranking, Loja, Conquistas, Chat, Skills, │
│                Cards, Season, Mercado, Amigos, Sprint)      │
└─────────────────────────────────────────────────────────────┘
```

### Nova (5 Tabs)
```
┌─────────────────────────────────────────────────────────────┐
│ TOP HUD (42px)                                              │
│  ├─ Vault (Saldo)                                           │
│  ├─ Multi (Combo)                                           │
│  ├─ Block (Número)                                          │
│  └─ Slashing Meter (3 dots)                                 │
├─────────────────────────────────────────────────────────────┤
│ MAIN AREA (flex: 1)                                         │
│  ├─ SIDEBAR NAV (56-96px, tablet+)                          │
│  │   ├─ JOGO (Grid icon)                                   │
│  │   ├─ UPGRADES (Shop icon)                               │
│  │   ├─ COMPETIR (Trophy icon)                             │
│  │   ├─ PERFIL (Card icon)                                 │
│  │   └─ SOCIAL (People icon)                               │
│  ├─ CONTENT (flex: 1)                                       │
│  │   ├─ Header (PROOF-OF-SEARCH // OP: [TAG]NICK)          │
│  │   └─ Tab Content (5 views)                              │
│  │      ├─ JOGO: Grid + Word Bank + Race                   │
│  │      ├─ UPGRADES: Hint, Freeze, Hardware, LN, Energia,  │
│  │      │              Crate                               │
│  │      ├─ COMPETIR: Leaderboard, Boss, PvP, Sprint,       │
│  │      │            Missões, Eventos Globais              │
│  │      ├─ PERFIL: Cards, Season, Skills, Staking,         │
│  │      │          Achievements, Nível/Rank                │
│  │      └─ SOCIAL: Friends, Chat, Mercado, Pools           │
├─────────────────────────────────────────────────────────────┤
│ MOBILE NAV (56px, mobile)                                   │
│  └─ JOGO | UPGRADES | COMPETIR | PERFIL | SOCIAL           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. PLANO DE MIGRAÇÃO EM 6 FASES

### FASE 1: Design System (CSS) — 2 dias
**Objetivo:** Substituir o CSS atual pelo design system pixel art.

| Tarefa | Arquivo | Esforço |
|--------|---------|---------|
| Criar `frontend/pixel.css` com variáveis CSS | Novo | 2h |
| Substituir cores, fontes, bordas | `pixel.css` | 2h |
| Criar componentes: `.btn-retro`, `.badge`, `.progress` | `pixel.css` | 2h |
| Criar layout: `.top-hud`, `.sidebar-nav`, `.content` | `pixel.css` | 2h |
| Criar responsivo: 6 breakpoints (320px-2560px) | `pixel.css` | 2h |
| Criar animações: blink, frenzy, float-up | `pixel.css` | 1h |
| Remover `style.css` e referenciar `pixel.css` | `index.html` | 30min |
| **Total** | | **~11h** |

**Entregável:** CSS pixel art completo, responsivo, com todos os componentes.

**Risco:** Baixo. CSS é isolado, não afeta lógica.

---

### FASE 2: Estrutura HTML (Layout) — 3 dias
**Objetivo:** Reestruturar o HTML para 5 tabs, mantendo todos os IDs.

| Tarefa | Arquivo | Esforço |
|--------|---------|---------|
| Criar estrutura base: `.top-hud`, `.main-area`, `.content` | `index.html` | 2h |
| Criar sidebar nav (tablet+) e mobile nav (mobile) | `index.html` | 2h |
| Criar 5 tabs: JOGO, UPGRADES, COMPETIR, PERFIL, SOCIAL | `index.html` | 3h |
| Mover elementos existentes para as tabs corretas | `index.html` | 4h |
| Manter TODOS os IDs existentes (`ui-balance`, `word-grid`, etc.) | `index.html` | 1h |
| Adicionar modais: Auth, Result, Achievements, PvP, Crate | `index.html` | 2h |
| **Total** | | **~14h** |

**Mapeamento de elementos para tabs:**

| Tab | Elementos Atuais | IDs a Manter |
|-----|-----------------|--------------|
| **JOGO** | Grid, Word Bank, Race Track, Boss HUD, Grid Overlay | `word-grid`, `word-bank-list`, `ui-network-progress`, `boss-hud`, `grid-overlay` |
| **UPGRADES** | Store (Hint, Hardware, Lightning, Energia, Crate) | `btn-buy-hint`, `btn-buy-hw`, `btn-buy-lightning`, `btn-buy-energy`, `btn-open-crate-free`, `btn-open-crate-buy` |
| **COMPETIR** | Leaderboard, Pools, Missões, Eventos Globais, PvP, Sprint | `leaderboard-list`, `pools-list`, `missions-list`, `global-event-banner`, `pvp-panel` |
| **PERFIL** | Cards, Season, Skills, Staking, Achievements, Nível/Rank | `cards-panel`, `season-panel`, `skills-panel`, `staking-panel`, `achievements-modal`, `level-bar-container` |
| **SOCIAL** | Friends, Chat, Mercado, Pools | `chat-panel`, `market-panel`, `friends-panel` |

**Risco:** Médio. Precisa manter todos os IDs para não quebrar o JS.

---

### FASE 3: JavaScript (Navegação) — 1 dia
**Objetivo:** Adicionar sistema de tabs sem quebrar a lógica existente.

| Tarefa | Arquivo | Esforço |
|--------|---------|---------|
| Criar função `showTab(name)` para alternar tabs | `game.js` | 1h |
| Adicionar event listeners nos botões de nav | `game.js` | 1h |
| Manter lógica existente de game loop | `game.js` | 0h |
| Manter lógica existente de WebSocket | `game.js` | 0h |
| Manter lógica existente de API calls | `game.js` | 0h |
| Testar navegação entre tabs | Manual | 2h |
| **Total** | | **~4h** |

**Código necessário:**
```javascript
function showTab(name) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.mobile-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    // Ativar botão correspondente
}
```

**Risco:** Baixo. Adição simples, não modifica lógica existente.

---

### FASE 4: Integração de Mecânicas — 3 dias
**Objetivo:** Garantir que todas as mecânicas funcionam no novo layout.

| Tarefa | Mecânica | Esforço |
|--------|----------|---------|
| Grid interativo | Caça-palavras | 1h |
| Word Bank | Transações pendentes | 1h |
| Race Track | Barra de progresso | 1h |
| Store | Hint, Hardware, Lightning, Energia, Crate | 2h |
| Leaderboard | Ranking global | 1h |
| Boss Block | HP bar, eventos | 1h |
| PvP | Desafios, countdown | 2h |
| Sprint | Timer, leaderboard | 1h |
| Missões | Diárias, semanais | 1h |
| Cards | Galeria, raridades | 1h |
| Season Pass | Tiers, progresso | 1h |
| Skill Tree | Nodes, upgrades | 2h |
| Staking | Formulário, stake ativo | 2h |
| Chat | WebSocket, mensagens | 1h |
| Mercado | Comprar, vender, histórico | 2h |
| Achievements | Modal, toast | 1h |
| Friends | Lista, status online | 1h |
| Eventos Globais | Banner, countdown | 1h |
| **Total** | | **~22h** |

**Risco:** Médio. Algumas mecânicas podem precisar de ajustes de layout.

---

### FASE 5: Backend (API) — 1 dia
**Objetivo:** Verificar se a API precisa de ajustes.

| Tarefa | Arquivo | Esforço |
|--------|---------|---------|
| Verificar endpoints existentes | `main.py` | 1h |
| Verificar WebSocket handlers | `main.py` | 1h |
| Verificar Redis keys | `storage.py` | 1h |
| Verificar ingestor | `ingestor.py` | 1h |
| Ajustar se necessário | Vários | 2h |
| **Total** | | **~6h** |

**Observação:** O backend NÃO precisa de mudanças. A API já suporta todas as mecânicas. O redesign é puramente frontend.

**Risco:** Baixo. Backend permanece inalterado.

---

### FASE 6: Testes & QA — 2 dias
**Objetivo:** Garantir que tudo funciona.

| Tarefa | Esforço |
|--------|---------|
| Testar em mobile (320px) | 2h |
| Testar em tablet (768px) | 1h |
| Testar em notebook (1024px) | 1h |
| Testar em desktop (1440px) | 1h |
| Testar em 42" (2560px) | 1h |
| Testar todas as mecânicas | 4h |
| Testar WebSocket | 1h |
| Testar API calls | 1h |
| Testar acessibilidade | 1h |
| **Total** | **~12h** |

**Risco:** Baixo. Testes padronizados.

---

## 4. ESTIMATIVA TOTAL

| Fase | Esforço | Dias |
|------|---------|------|
| 1. Design System (CSS) | 11h | 2 |
| 2. Estrutura HTML (Layout) | 14h | 3 |
| 3. JavaScript (Navegação) | 4h | 1 |
| 4. Integração de Mecânicas | 22h | 3 |
| 5. Backend (API) | 6h | 1 |
| 6. Testes & QA | 12h | 2 |
| **TOTAL** | **69h** | **~12 dias úteis** |

---

## 5. RISCOS E MITIGAÇÃO

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Quebra de IDs no HTML | Alto | Manter TODOS os IDs existentes |
| CSS conflitante | Médio | CSS modular, variáveis isoladas |
| JS quebrado | Médio | Não modificar lógica existente |
| Responsivo quebrado | Médio | Testar em todos os breakpoints |
| WebSocket não funciona | Alto | Manter lógica existente |
| API calls falham | Alto | Manter endpoints existentes |

---

## 6. CHECKLIST DE IMPLEMENTAÇÃO

### Pré-requisitos
- [ ] Backup do código atual
- [ ] Branch `redesign-pixel-art` no git
- [ ] Protótipo v3 como referência

### Fase 1: CSS
- [ ] Criar `frontend/pixel.css`
- [ ] Variáveis CSS (cores, fontes, espaçamentos)
- [ ] Componentes (botões, badges, progress)
- [ ] Layout (top-hud, sidebar, content)
- [ ] Responsivo (6 breakpoints)
- [ ] Animações (blink, frenzy, float-up)
- [ ] Substituir `style.css` por `pixel.css`

### Fase 2: HTML
- [ ] Estrutura base (top-hud, main-area, content)
- [ ] Sidebar nav (tablet+)
- [ ] Mobile nav (mobile)
- [ ] 5 tabs (JOGO, UPGRADES, COMPETIR, PERFIL, SOCIAL)
- [ ] Mover elementos para tabs
- [ ] Manter TODOS os IDs
- [ ] Modais (Auth, Result, Achievements, PvP, Crate)

### Fase 3: JS
- [ ] Função `showTab(name)`
- [ ] Event listeners nos botões
- [ ] Testar navegação

### Fase 4: Integração
- [ ] Grid interativo
- [ ] Word Bank
- [ ] Race Track
- [ ] Store
- [ ] Leaderboard
- [ ] Boss Block
- [ ] PvP
- [ ] Sprint
- [ ] Missões
- [ ] Cards
- [ ] Season Pass
- [ ] Skill Tree
- [ ] Staking
- [ ] Chat
- [ ] Mercado
- [ ] Achievements
- [ ] Friends
- [ ] Eventos Globais

### Fase 5: Backend
- [ ] Verificar endpoints
- [ ] Verificar WebSocket
- [ ] Verificar Redis
- [ ] Verificar ingestor

### Fase 6: Testes
- [ ] Mobile (320px)
- [ ] Tablet (768px)
- [ ] Notebook (1024px)
- [ ] Desktop (1440px)
- [ ] 42" (2560px)
- [ ] Todas as mecânicas
- [ ] WebSocket
- [ ] API calls
- [ ] Acessibilidade

---

## 7. DECISÕES PENDENTES

| Decisão | Opções | Recomendação |
|---------|--------|--------------|
| Substituir `style.css` ou manter ambos? | Substituir / Manter ambos | Substituir (evita conflitos) |
| Manter `game.js` ou refatorar? | Manter / Refatorar | Manter (não toque no que funciona) |
| Criar novo `index.html` ou modificar? | Novo / Modificar | Modificar (manter IDs) |
| Deploy gradual ou completo? | Gradual / Completo | Completo (redesign é visual) |

---

## 8. PRÓXIMOS PASSOS

1. **Aprovar roadmap** — Usuário analisa e aprova
2. **Criar branch** — `git checkout -b redesign-pixel-art`
3. **Fase 1** — CSS pixel art
4. **Fase 2** — HTML reestruturado
5. **Fase 3** — JS navegação
6. **Fase 4** — Integração de mecânicas
7. **Fase 5** — Verificação backend
8. **Fase 6** — Testes e QA
9. **Deploy** — `git push` e deploy

---

**Gerado por:** Logger (Hermes Agent)
**Data:** 19/08/2026
**Versão:** 1.0
