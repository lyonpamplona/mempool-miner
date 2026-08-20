# Mempool Miner — Análise de Game Design & Sugestões de Novas Mecânicas

## 1. LOOP DE GAMEPLAY ATUAL

### Ciclo Principal
```
Escolher rede → Aguardar 6 TXs reais da mempool → Grade gerada → 
Corrida contra timer → Encontrar palavras → Ganhar sats → 
Comprar upgrades → Próxima rodada
```

### Avaliação do Loop

| Critério | Nota | Análise |
|----------|------|---------|
| **Feedback imediato** | ✅ Forte | Sons (tick/success/orphan/buy), floating text com pontos, animação SVG de linha, combo visual, barra de progresso do timer |
| **Progressão clara** | ⚠️ Parcial | Hardware levels (CPU→GPU→ASIC→Quantum) dão senso de evolução, mas não há níveis/rank do jogador — apenas saldo acumulado |
| **Variedade** | ⚠️ Média | Golden Hash, High Fee, MEV Secret, Lightning Mode adicionam variedade, mas o core loop (encontrar palavras na grade) é sempre o mesmo |
| **Tensão** | ✅ Forte | Timer regressivo, slashing por erros, RBF como "segunda chance", halving que reduz tempo/recompensa |
| **Conexão com tema** | ✅ Excelente | TXs reais da mempool Bitcoin, BIP39 words, halving protocol, Lightning Network, pools de mineração — tudo educacional e temático |

### Pontos Fortes do Loop
- **Dados reais**: Cada rodada é única porque usa transações reais da mempool
- **Múltiplas camadas de recompensa**: base + comprimento + combo + raridade + lightning
- **Risco/Recompensa**: Slashing pune erros, RBF oferece resgate caro
- **Escalonamento orgânico**: Halving protocol naturalmente aumenta dificuldade

### Pontos Fracos do Loop
- **Sem meta-progression entre sessões**: O jogador volta ao mesmo estado visual (apenas saldo persiste)
- **Loop monolítico**: Apenas "encontrar palavras" — sem variação de mecânica
- **Sem objetivos de curto prazo**: Não há missões, metas diárias ou milestones
- **Falta de "endgame"**: Após max hardware + lightning, não há mais para buscar

---

## 2. CURVA DE DIFICULDADE

### Mecânicas Atuais de Dificuldade

| Mecânica | Efeito | Progressão |
|----------|--------|------------|
| **Halving Protocol** | -1s de tempo por bloco (máx -30s) | Linear, cumulativa |
| **Halving de Recompensa** | -2% a cada 10 blocos (mín 50%) | Gradual |
| **Grid Dinâmico** | 12×12 padrão, 15×15 para vsize>1000 | Baseado em dados reais |
| **Lightning Mode** | 8×8 grid, 20s timer | Mais rápido, menos espaço |
| **Slashing** | 5% do saldo por 3 erros consecutivos | Penalidade de precisão |

### Avaliação
- **Início**: Fácil — 60s para 6 palavras em 12×12 é generoso
- **Meio**: Halving começa a apertar (~30 blocos = -30s = 30s restantes)
- **Pico de dificuldade**: ~50 blocos com halving máximo + grid 15×15 = 30s para 15×15
- **Problema**: A dificuldade é **apenas temporal** — não há complexidade mecânica crescente
- **Problema**: Após reset de epoch (2016 blocos), a dificuldade volta ao zero — sem acumulação de longo prazo

---

## 3. SISTEMA DE RECOMPENSAS

### Recompensas Atuais

| Tipo | Valor | Gatilho | Frequência |
|------|-------|---------|------------|
| Base | 500 + (comprimento × 50) | Cada palavra | Sempre |
| Combo | 1.0× até 4.0× | <8s entre palavras | Variável |
| Golden Hash | 5× multiplicador | TXID começa com "00" | Rara |
| High Fee | 3× multiplicador | Fee ≥ 20 sat/vB | Moderada |
| MEV Secret | +50.000 sats bonus | ~15% das TXs | Oculta |
| Lightning | 10× tudo | Modo ativo (5 blocos) | Compra |
| RBF | 15s extras | Bloco minerado mid-round | Evento |

### Avaliação
- **Variedade**: ✅ Boa — 6 tipos de recompensa com mecânicas diferentes
- **Antecipação**: ⚠️ Média — Golden Hash e MEV criam momentos de surpresa, mas sem sistema de "próxima recompensa"
- **Satisfação visual**: ✅ Boa — Floating text colorido, sons distintos, animações
- **Progressão financeira**: ⚠️ Fraca — Saldo é o único recurso, sem sinks além dos 3 upgrades existentes
- **Falta**: Sem recompensas não-monetárias (títulos, badges, desbloqueáveis visuais)

---

## 4. MECÂNICAS EXISTENTES — INVENTÁRIO COMPLETO

### Core Gameplay
1. **Word Search Grid** — Caça-palavras em grade dinâmica (8×8 a 15×15)
2. **Timer Race** — Corrida contra cronômetro visual (barra de progresso)
3. **Combo System** — Multiplicador por velocidade (até 4×)
4. **Slashing** — Penalidade por erros consecutivos (5% do saldo)
5. **Dynamic Grid Size** — Grade expande baseado em vsize das TXs

### Economia
6. **Satoshi Balance** — Moeda única do jogo
7. **Hardware Shop** — 4 tiers de upgrade (CPU→GPU→ASIC→Quantum), cada +10s
8. **Hint System** — 5.000 sats para revelar primeira letra
9. **Lightning Mode** — 1M sats, 10× recompensas, 5 blocos de duração
10. **RBF Salvage** — 100K sats para 15s extras quando bloco real minera

### Raridade/Eventos
11. **Golden Hash** — TXID começa com "00", 5× multiplicador
12. **High Fee** — Fee alta, 3× multiplicador
13. **MEV Secret** — Palavras ocultas do word bank, +50K sats bonus
14. **Halving Protocol** — Dificuldade crescente + recompensa decrescente
15. **Leaderboard Epochs** — Reset a cada 2016 blocos

### Social
16. **Leaderboard** — Top 10 por realm
17. **Mining Pools** — Guildas com tag [TAG] no nome

### Técnico
18. **Session Persistence** — sessionStorage para restaurar sessão
19. **Player State Sync** — Backend armazena balance, hardware, lightning, combo
20. **Auto-reconnect** — Backoff exponencial para reconexão WebSocket
21. **Multi-realm** — Suporte a múltiplas redes Bitcoin (signet, testnet, mainnet)

---

## 5. GAP ANALYSIS — O QUE FALTA

| Área | O que falta | Impacto |
|------|-------------|---------|
| Progressão de longo prazo | Níveis, XP, rank do jogador | Alto |
| Objetivos | Missões diárias/semanais, achievements | Alto |
| Variedade de gameplay | Mini-games, modos alternativos | Médio |
| Social | Chat, PvP, cooperação | Alto |
| Economia | Mercado, itens colecionáveis, sinks adicionais | Médio |
| Retenção | Daily login, streaks, season pass | Alto |
| Visual | Skins, temas, efeitos desbloqueáveis | Médio |
| Endgame | Conteúdo pós-max hardware | Alto |

---

## 6. SUGESTÕES DE NOVAS MECÂNICAS

### 📊 CATEGORIA: PROGRESSÃO

#### 6.1 — Sistema de Níveis & Rank do Jogador
- **Descrição**: XP ganho por palavra encontrada converte em níveis (1-100). Cada 10 níveis = novo rank com nome temático (Script Kiddie → Node Operator → Mining Tycoon → Satoshi). Ranks dão bônus passivos (ex: +2s base, hints 10% mais baratos).
- **Impacto no engajamento**: 🔴 ALTO — Dá meta de longo prazo, senso de identidade, e progresso visível independente do saldo
- **Esforço**: 🔴 ALTO — Backend: tabela de XP/ranks no Redis, cálculo de level-up. Frontend: barra de XP, UI de rank, animações de level-up
- **Dependências**: Player state no backend (já existe), sistema de persistência (já existe)

#### 6.2 — Achievements / Conquistas
- **Descrição**: 30-50 conquistas desbloqueáveis com categorias: Volume (encontrar 100 palavras), Raridade (encontrar 10 Golden Hashes), Velocidade (combo 4×), Exploração (jogar em 3 realms), Social (entrar no top 3). Cada conquista dá badge visual + bônus permanente pequeno.
- **Impacto no engajamento**: 🔴 ALTO — Dá objetivos concretos, recompensa comportamentos específicos, cria "coleccionabilidade"
- **Esforço**: 🟡 MÉDIO — Backend: tracking de stats no player state, API de achievements. Frontend: painel de achievements, badges, notificações de desbloqueio
- **Dependências**: Player state tracking (expandir campos existentes), leaderboard (já existe)

#### 6.3 — Missões Diárias & Semanais
- **Descrição**: 3 missões diárias rotativas (ex: "Encontre 5 palavras High Fee", "Ganhe 50K sats em uma rodada", "Use RBF com sucesso") + 1 missão semanal desafiadora. Recompensas: sats bonus + XP + itens especiais. Missões expiram à meia-noite UTC.
- **Impacto no engajamento**: 🔴 ALTO — Driver de retorno diário comprovado, dá foco à sessão, cria urgência
- **Esforço**: 🟡 MÉDIO — Backend: geração de missões, tracking de progresso, reset diário via cron. Frontend: painel de missões, progresso visual, notificações
- **Dependências**: Sistema de XP (sugestão 6.1), player state tracking, cron job para reset

#### 6.4 — Árvore de Habilidades (Skill Tree)
- **Descrição**: 3 ramos temáticos: ⛏️ Mining (bônus de tempo, hardware mais barato), 🔍 Search (hints mais baratos, palavras MEV mais frequentes), ⚡ Lightning (canal dura mais, multiplicador maior). Cada ramo tem 5 níveis, desbloqueados com "Skill Points" ganhos ao subir de nível.
- **Impacto no engajamento**: 🟡 MÉDIO — Personalização profunda, escolhas estratégicas, replayability
- **Esforço**: 🔴 ALTO — Backend: persistência de skill points e escolhas, aplicação de bônus. Frontend: UI interativa de árvore, tooltips, preview de efeitos
- **Dependências**: Sistema de níveis (sugestão 6.1), player state expandido

---

### 👥 CATEGORIA: SOCIAL

#### 6.5 — Chat em Tempo Real por Realm
- **Descrição**: Canal de chat WebSocket por realm, com mensagens curtas (máx 100 chars). Mensagens aparecem como "tx broadcasts" no feed lateral. Sistema de moderação básico (ban de palavras, rate limit). Emojis temáticos de Bitcoin.
- **Impacto no engajamento**: 🟡 MÉDIO — Comunidade, interação social, senso de presença
- **Esforço**: 🟡 MÉDIO — Backend: novo channel Redis para mensagens, rate limiting, moderação. Frontend: painel de chat, scroll, input
- **Dependências**: Infraestrutura WebSocket (já existe), Redis pub/sub (já existe)

#### 6.6 — Desafios PvP (Head-to-Head)
- **Descrição**: Jogador desafia outro do leaderboard para uma rodada sincronizada. Ambos recebem as mesmas 6 palavras na mesma grade. Quem encontrar mais palavras (ou mais rápido) ganha o prêmio do perdedor (ex: 10% do saldo). Matchmaking por nível próximo.
- **Impacto no engajamento**: 🔴 ALTO — Competição direta, alto engajamento, viralidade
- **Esforço**: 🔴 ALTO — Backend: sistema de matchmaking, sincronização de rounds, arbitragem de resultado. Frontend: UI de desafio, countdown, resultado PvP
- **Dependências**: Leaderboard (já existe), sistema de níveis (sugestão 6.1), WebSocket sync

#### 6.7 — Eventos em Tempo Real (Global Events)
- **Descrição**: Eventos temporários que afetam todos os jogadores de um realm simultaneamente. Exemplos: "Fee Spike" (todas as palavras são High Fee por 10 minutos), "Golden Rush" (Golden Hash aparece 3× mais), "Mempool Flood" (grade 15×15 obrigatória, recompensas 2×). Anunciados com 2 minutos de antecedência.
- **Impacto no engajamento**: 🟡 MÉDIO — Urgência, FOMO, momentos memoráveis compartilhados
- **Esforço**: 🟡 MÉDIO — Backend: scheduler de eventos, broadcast via WebSocket, modificação temporária de parâmetros. Frontend: banner de evento, timer, efeitos visuais
- **Dependências**: WebSocket broadcast (já existe), sistema de eventos (já existe parcialmente)

#### 6.8 — Sistema de Amigos & Co-op
- **Descrição**: Lista de amigos com status online/offline. Bônus de "mining co-op": quando amigos estão online no mesmo realm, todos ganham +5% de recompensa por amigo ativo (máx +20%). Visitas ao perfil mostram stats básicos.
- **Impacto no engajamento**: 🟡 MÉDIO — Retenção social, pull factor para trazer amigos
- **Esforço**: 🟡 MÉDIO — Backend: relações de amizade no Redis, tracking de status online. Frontend: lista de amigos, perfil, indicador de bônus co-op
- **Dependências**: Player state (já existe), sistema de níveis (sugestão 6.1)

---

### 💰 CATEGORIA: ECONOMIA

#### 6.9 — Mercado de Power-ups (Player-to-Player)
- **Descrição**: Power-ups encontrados durante o jogo (ex: "Time Freeze", "Word Reveal", "Double Combo") podem ser usados ou vendidos no mercado. Preços flutuam baseado em oferta/demand. Mercado é por realm com taxa de 5%.
- **Impacto no engajamento**: 🟡 MÉDIO — Economia player-driven, trading, estratégia de uso vs venda
- **Esforço**: 🔴 ALTO — Backend: database de itens, sistema de ofertas, matching de preços, prevenção de fraudes. Frontend: UI de mercado, histórico de preços, inventário
- **Dependências**: Sistema de itens (sugestão 6.10), player state expandido

#### 6.10 — Tokens Colecionáveis (Block Cards)
- **Descrição**: Cada bloco minerado gera um "Block Card" colecionável com o hash do bloco, dificuldade, e stats da rodada. Cards têm raridade (Common, Rare, Epic, Legendary) baseada em eventos especiais. Coleções completas dão bônus permanentes.
- **Impacto no engajamento**: 🟡 MÉDIO — Coleccionabilidade, FOMO por cards raros, objetivos de coleção
- **Esforço**: 🟡 MÉDIO — Backend: geração de cards, raridade, tracking de coleção. Frontend: galeria de cards, filtros, animação de "pull"
- **Dependências**: Player state expandido, sistema de achievements (sugestão 6.2)

#### 6.11 — Loot Boxes / Mempool Crates
- **Descrição**: A cada 10 blocos completados, o jogador ganha uma "Mempool Crate". Abertura revela: sats bonus, power-ups temporários, Block Cards raros, ou (raramente) skins desbloqueáveis. Probabilidade transparente (ex: 60% sats, 25% power-up, 10% card, 5% skin).
- **Impacto no engajamento**: 🟡 MÉDIO — Antecipação, surpresa, variação de recompensa
- **Esforço**: 🟡 MÉDIO — Backend: sistema de loot tables, RNG, tracking de aberturas. Frontend: animação de abertura, inventário, efeitos visuais
- **Dependências**: Sistema de itens, player state

#### 6.12 — Staking de Sats
- **Descrição**: Jogador pode "travar" sats em um staking pool por períodos (1h, 6h, 24h). Durante o staking, ganha bônus passivo (+1% XP, +5% recompensas) mas não pode gastar os sats. Cancelar antes do prazo perde 10% dos sats staked.
- **Impacto no engajamento**: 🟡 MÉDIO — Sink de moeda, decisão estratégica, retorno passivo
- **Esforço**: 🟡 MÉDIO — Backend: tracking de stakes, timers, cálculo de bônus. Frontend: UI de staking, timer visual, preview de bônus
- **Dependências**: Player state, sistema de XP (sugestão 6.1)

---

### 🎮 CATEGORIA: GAMEPLAY

#### 6.13 — Power-ups Temporários
- **Descrição**: Itens ativáveis durante a rodada com duração limitada:
  - ⏸️ **Time Freeze** (5s): Pausa o timer por 5 segundos
  - 🔍 **Scanner** (1 rodada): Revela a direção de uma palavra
  - 💎 **Double Combo** (1 rodada): Combo sobe até 6× ao invés de 4×
  - 🧲 **Magnet** (1 rodada): Palavras encontradas dão +50% sats
  - 🎯 **Precision** (1 rodada): Sem slashing por 1 rodada
- **Impacto no engajamento**: 🟡 MÉDIO — Variedade tática, momentos de poder, estratégia de quando usar
- **Esforço**: 🟡 MÉDIO — Backend: tracking de power-ups ativos, modificação de regras temporária. Frontend: UI de inventário, botão de ativar, timer visual, efeitos
- **Dependências**: Sistema de itens (sugestão 6.10), player state

#### 6.14 — Boss Battles (Blocos Especiais)
- **Descrição**: A cada 50 blocos, aparece um "Boss Block" — uma rodada especial com: grade 15×15, 10 palavras (ao invés de 6), timer reduzido (45s), mas recompensa 5×. Boss tem "HP" visual (barra de vida) que diminui a cada palavra encontrada. Derrotar o boss dá achievement + loot especial.
- **Impacto no engajamento**: 🔴 ALTO — Picos de tensão, momentos épicos, recompensa desproporcional
- **Esforço**: 🟡 MÉDIO — Backend: trigger a cada 50 blocos, parâmetros especiais, loot drop. Frontend: UI de boss, barra de HP, efeitos visuais dramáticos, animação de derrota
- **Dependências**: Counter de blocos no backend, sistema de loot (sugestão 6.11)

#### 6.15 — Mini-game: Transaction Decoder
- **Descrição**: Entre rodadas, com 10% de chance, aparece um mini-game opcional: o jogador recebe um TXID truncado e deve adivinhar a palavra BIP39 correspondente em 3 tentativas. Acerto = sats bonus + XP. Errar 3x = perde a chance.
- **Impacto no engajamento**: 🟢 BAIXO-MÉDIO — Variedade, quebra de monotonia, educação sobre BIP39
- **Esforço**: 🟢 BAIXO — Backend: geração de desafio, validação. Frontend: modal de mini-game, input, feedback
- **Dependências**: GameEngine.tx_to_word (já existe)

#### 6.16 — Modo "Sprint" (Quick Play)
- **Descrição**: Modo alternativo ativável: grade 10×10, 4 palavras, 30s timer, sem upgrades. Focado em sessões rápidas de 2-3 minutos. Leaderboard separado por tempo total. Ideal para mobile e pausas curtas.
- **Impacto no engajamento**: 🟡 MÉDIO — Acessibilidade, sessões curtas, público mobile
- **Esforço**: 🟢 BAIXO — Backend: flag de modo, leaderboard separado. Frontend: toggle de modo, UI simplificada
- **Dependências**: Leaderboard (já existe)

---

### 🔄 CATEGORIA: RETENÇÃO

#### 6.17 — Sistema de Streaks (Login Diário)
- **Descrição**: Login consecutivo dá recompensas escalonadas: Dia 1: 1.000 sats, Dia 3: 5.000 sats + hint grátis, Dia 7: 20.000 sats + power-up, Dia 14: 50.000 sats + Block Card raro, Dia 30: 100.000 sats + skin exclusiva. Perder um dia reseta para zero. "Streak Freeze" (item raro) salva o streak uma vez.
- **Impacto no engajamento**: 🔴 ALTO — Driver de retenção #1 em jogos mobile, hábito diário, FOMO de perder streak
- **Esforço**: 🟡 MÉDIO — Backend: tracking de último login, cálculo de streak, distribuição de recompensas. Frontend: calendário visual, contador de streak, animação de recompensa
- **Dependências**: Player state expandido (último login, streak count)

#### 6.18 — Energy System (Mempool Energy)
- **Descrição**: Cada rodada consome 1 "Energy" (máx 10). Energy regenera 1 a cada 30 minutos (máx 10). Jogador pode comprar Energy com sats (preço escala: 10K, 20K, 50K...). Sem energy, jogador espera ou compra. Previne burnout e cria escassez natural.
- **Impacto no engajamento**: 🟡 MÉDIO — Controla ritmo de jogo, cria retorno natural, sink de moeda
- **Esforço**: 🟡 MÉDIO — Backend: tracking de energy, timer de regeneração, loja de energy. Frontend: display de energy, timer de regeneração, botão de compra
- **Dependências**: Player state, timer server-side

#### 6.19 — Season Pass (Battle Pass)
- **Descrição**: Temporadas de 4 semanas com trilha de recompensas gratuita e premium. Trilha gratuita: sats, hints, power-ups. Trilha premium (500K sats): skins exclusivas, Block Cards raros, bônus permanentes. XP de gameplay avança na trilha. Cada temporada tem tema (ex: "Halving Season", "Lightning Season").
- **Impacto no engajamento**: 🔴 ALTO — Engajamento de longo prazo, meta clara, conteúdo rotativo, monetização
- **Esforço**: 🔴 ALTO — Backend: sistema de temporadas, tracking de progresso, distribuição de recompensas, cron de reset. Frontend: UI de season pass, progresso visual, loja de premium, countdown
- **Dependências**: Sistema de XP (sugestão 6.1), sistema de itens, cron jobs

#### 6.20 — Daily Rewards Escalonadas
- **Descrição**: Recompensa diária que escala por 7 dias: Dia 1: 500 sats, Dia 2: 1.000 sats, ..., Dia 7: 10.000 sats + item especial. Reset semanal. Diferente de streaks — não pune ausência, apenas reseta o contador. Coletar recompensa do dia 7 dá badge "Weekly Champion".
- **Impacto no engajamento**: 🟡 MÉDIO — Retorno semanal, recompensa consistente, menor pressão que streaks
- **Esforço**: 🟢 BAIXO — Backend: tracking de dia atual, distribuição. Frontend: grid de 7 dias, botão de coletar, animação
- **Dependências**: Player state (dia atual da semana)

---

## 7. MATRIZ DE PRIORIDADE

### Fase 1 — MVP de Engajamento (Alto impacto, esforço contido)
| # | Feature | Impacto | Esforço | Por quê |
|---|---------|---------|---------|---------|
| 1 | **Streaks (6.17)** | 🔴 ALTO | 🟡 MÉDIO | Retenção #1, implementação direta |
| 2 | **Daily Rewards (6.20)** | 🟡 MÉDIO | 🟢 BAIXO | Complementa streaks, baixo esforço |
| 3 | **Achievements (6.2)** | 🔴 ALTO | 🟡 MÉDIO | Objetivos concretos, reutiliza stats existentes |
| 4 | **Boss Battles (6.14)** | 🔴 ALTO | 🟡 MÉDIO | Picos de emoção, reutiliza mecânica existente |

### Fase 2 — Progressão & Variedade
| # | Feature | Impacto | Esforço | Por quê |
|---|---------|---------|---------|---------|
| 5 | **Níveis & Rank (6.1)** | 🔴 ALTO | 🔴 ALTO | Base para todas as features de progressão |
| 6 | **Missões Diárias (6.3)** | 🔴 ALTO | 🟡 MÉDIO | Driver de retorno, depende de níveis |
| 7 | **Power-ups (6.13)** | 🟡 MÉDIO | 🟡 MÉDIO | Variedade tática, prepara para economia |
| 8 | **Eventos Globais (6.7)** | 🟡 MÉDIO | 🟡 MÉDIO | FOMO, momentos compartilhados |

### Fase 3 — Social & Economia
| # | Feature | Impacto | Esforço | Por quê |
|---|---------|---------|---------|---------|
| 9 | **Chat (6.5)** | 🟡 MÉDIO | 🟡 MÉDIO | Comunidade, reutiliza WebSocket |
| 10 | **Tokens Colecionáveis (6.10)** | 🟡 MÉDIO | 🟡 MÉDIO | Coleccionabilidade, prepara para mercado |
| 11 | **PvP (6.6)** | 🔴 ALTO | 🔴 ALTO | Competição direta, alto engajamento |
| 12 | **Mercado (6.9)** | 🟡 MÉDIO | 🔴 ALTO | Economia player-driven, complexo |

### Fase 4 — Endgame & Monetização
| # | Feature | Impacto | Esforço | Por quê |
|---|---------|---------|---------|---------|
| 13 | **Season Pass (6.19)** | 🔴 ALTO | 🔴 ALTO | Engajamento de longo prazo, monetização |
| 14 | **Skill Tree (6.4)** | 🟡 MÉDIO | 🔴 ALTO | Personalização profunda, endgame |
| 15 | **Staking (6.12)** | 🟡 MÉDIO | 🟡 MÉDIO | Sink de moeda, decisão estratégica |
| 16 | **Loot Boxes (6.11)** | 🟡 MÉDIO | 🟡 MÉDIO | Variação de recompensa |

### Fase 5 — Polimento
| # | Feature | Impacto | Esforço | Por quê |
|---|---------|---------|---------|---------|
| 17 | **Mini-game Decoder (6.15)** | 🟢 BAIXO | 🟢 BAIXO | Variedade, educação |
| 18 | **Modo Sprint (6.16)** | 🟡 MÉDIO | 🟢 BAIXO | Acessibilidade mobile |
| 19 | **Amigos & Co-op (6.8)** | 🟡 MÉDIO | 🟡 MÉDIO | Retenção social |
| 20 | **Energy System (6.18)** | 🟡 MÉDIO | 🟡 MÉDIO | Controle de ritmo, opcional |

---

## 8. RECOMENDAÇÕES DE GAME DESIGN

### Críticas Construtivas ao Design Atual

1. **O loop é bom mas monolítico**: O jogo tem excelente core loop (encontrar palavras), mas precisa de "sazonalidade" — momentos diferentes dentro da mesma sessão. Boss Battles e Eventos Globais resolvem isso.

2. **Falta de identidade do jogador**: O jogador é apenas um saldo e um hardware. Níveis, ranks, badges e skins dão personalidade e orgulho de exibição.

3. **Economia sem sinks suficientes**: Após comprar max hardware + lightning, o saldo acumulado não tem para onde ir. Staking, mercado, season pass e itens criam sinks saudáveis.

4. **Retenção depende de TXs reais**: Se a mempool estiver vazia, o jogo para. Energy system + modo Sprint + mini-games dão alternativas quando não há TXs suficientes.

5. **Leaderboard é flat**: Top 10 é bom para os melhores, mas os 11-100 não veem progresso. Níveis, ranks e achievements dão progresso para todos.

### Princípios para Implementação

- **Manter a conexão com Bitcoin real**: Toda nova mecânica deve ter justificativa temática (ex: "staking" = travar BTC, "pools" = mineração coletiva)
- **Progressão em camadas**: Curto prazo (missões diárias) → Médio prazo (níveis/achievements) → Longo prazo (season pass/ranks)
- **Recompensas variadas**: Não apenas sats — XP, badges, skins, power-ups, cards
- **Dados reais como diferencial**: Nenhuma sugestão substitui o core de TXs reais — todas complementam
