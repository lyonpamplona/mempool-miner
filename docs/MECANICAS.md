# Mecânicas do jogo

Referência completa de todas as mecânicas do Mempool Miner, organizada pelas
cinco abas da interface (JOGO, UPGRADES, COMPETIR, PERFIL, SOCIAL) mais as
mecânicas transversais. Os valores numéricos citados aqui são os constantes
atuais no código (`frontend/game.js` e `backend/app/main.py`); se divergirem,
o código é a fonte de verdade.

> Sats, hashrate, carteira, Lightning e recompensas são **simulados**. O que é
> real: evento ZMQ, TXID, vsize, taxa, hash de bloco e a derivação BIP39.

## Mapa das abas

| Aba | Subseções | Mecânicas |
|---|---|---|
| **JOGO** | — | Coleta BIP39, grade, pontuação, raridades, RBF, boss block, eventos globais, loja, pools, leaderboard |
| **UPGRADES** | LOJA · INVENTÁRIO · UTILITÁRIOS | Hint, hardware, Lightning; power-ups; mini-game Decoder |
| **COMPETIR** | RANKING · MISSÕES · SPRINT | Leaderboard/pools; missões diárias/semanais; sprint |
| **PERFIL** | VISÃO · PROGRESSÃO · COLEÇÃO · ECONOMIA | Nível/XP/rank; cards; staking |
| **SOCIAL** | CHAT · EQUIPE · MERCADO | Chat; amigos; mercado de power-ups |
| **Transversais** | — | Conquistas, season pass, energia, crates, skill tree, PWA, sessão |

---

## Aba JOGO

### Coleta de palavras BIP39

Cada transação que entra no mempool é convertida em uma palavra BIP39
determinística (primeira palavra de 128 bits do double SHA-256 do TXID). O
jogo coleta **6 palavras únicas** antes de montar a grade. Palavras repetidas
são descartadas. O buffer é limpo a cada novo bloco.

### Grade de caça-palavras

| Condição | Grade |
|---|---|
| Padrão | 12×12 |
| Modo Lightning (L2) ativo | 8×8 |
| Alguma palavra com vsize > 1000 | 15×15 |
| Evento `mempool_flood` ativo | 15×15 (obrigatória) |
| Evento `lightning_storm` ativo | 8×8 |

Palavras são posicionadas sem sobreposição (tentativas + fallback); espaços
restantes são preenchidos com letras aleatórias. O tamanho da célula é
calculado por viewport (`configureGridSize`).

### Seleção

- **Mouse/toque/caneta:** Pointer Events unificados; clique na primeira letra
  e arraste até a última.
- **Teclado:** setas navegam, Enter confirma, Escape cancela.
- **Direção:** horizontal, vertical ou diagonal, nos dois sentidos. A segunda
  célula fixa o vetor; as próximas devem continuar na mesma linha.

### Pontuação

```
pontos = (500 + comprimento × 50) × combo × multiplier
```

| Fator | Valor |
|---|---|
| Base por palavra | 500 |
| Bônus por letra | 50 × comprimento |
| Combo | +0,5 por acerto em < 8 s, limitado a 4× |

### Raridades e multiplicadores

| Tipo | Condição | Multiplicador |
|---|---|---|
| Golden Hash | TXID começa com `00` | ×5 |
| High Fee | taxa ≥ 20 sats/vB (`HIGH_FEE_RATE_SAT_VB`) | ×3 |
| Golden + High Fee | ambos | ×15 |
| MEV | `int(txid[:8], 16) % 100 < 15` (~15%) | ×1 (flag separada, sem bônus direto) |
| Padrão | — | ×1 |

O `multiplier` final publicado já inclui o efeito do evento global ativo
(abaixo).

### RBF / bloco órfão

Quando um bloco real encerra a rodada com palavras não encontradas, o jogador
pode ativar **RBF** (Replace-By-Fee) para "resgatar" o bloco:

- **Custo:** 100.000 sats (`RBF_PRICE`)
- **Efeito:** +15 s (`RBF_TIME_BONUS`) para continuar a rodada
- **Janela:** 3 s para decidir (`scheduleForSession`, 3000 ms)
- Se o saldo for insuficiente ou a janela expirar, a rodada é marcada como
  derrota.

### Boss block

A cada **50 blocos**, o ingestor publica um evento `boss_block`:

| Campo | Valor |
|---|---|
| `boss_hp` | 10 |
| `boss_grid_size` | 15 (grade 15×15) |
| `boss_words` | 10 |
| `boss_timer` | 45 s |
| `boss_reward_multiplier` | ×5 |
| `boss_loot` | 50.000 sats |

O HUD do boss (`boss-hud`) mostra a barra de HP sobre a grade. Cada palavra
encontrada reduz o HP; zerar o HP vence e concede o loot. O modal
`boss-defeat-modal` exibe o resultado.

### Eventos globais

O `GlobalEventScheduler` dispara eventos aleatórios com aviso antecipado de
120 s (`EVENT_PREANNOUNCE_SECONDS`). O banner (`global-event-banner`) mostra o
contagem regressiva.

| Evento | Duração | Efeito |
|---|---|---|
| `fee_spike` | 10 min | Todas as palavras viram High Fee (3×); Golden+HighFee = 15× |
| `golden_rush` | 5 min | Golden Hash 3× mais frequente (~30%); 5× |
| `mempool_flood` | 10 min | Recompensas 2×; grade 15×15 obrigatória; +15 s no tempo |
| `lightning_storm` | 3 min | 10× recompensa; grade 8×8; tempo base 20 s |

Os efeitos são aplicados no ingestor (`apply_event_effects`) antes da
publicação, então o `multiplier` do evento já reflete o bônus.

### Loja (compras rápidas na aba JOGO)

| Item | Custo | Efeito |
|---|---|---|
| Dica (hint) | 5.000 sats (`HINT_PRICE`) | Destaca a primeira célula de uma palavra pendente |
| Hardware | progressivo | Adiciona tempo fora do modo L2; níveis CPU → GPU → ASIC |
| Lightning (L2) | 1.000.000 sats | Ativa modo Lightning: grade 8×8, tema azul, ×10; só entre rodadas |

### Pools (guildas)

Top 10 de pools por realm (`GET /pools`). Entrar em uma pool soma o score do
jogador ao da pool; o ranking de pools é independente do leaderboard
individual.

### Leaderboard

Top 10 por realm. O navegador envia nickname + saldo fictício; `ZADD GT`
mantém apenas o maior valor. **Não é autoritativo** (score calculado no
browser).

---

## Aba UPGRADES

### LOJA

Mesmos itens da loja da aba JOGO (hint, hardware, Lightning), com estado de
compra e níveis.

### INVENTÁRIO — Power-ups

Power-ups obtidos por crates/season e ativáveis na partida:

| ID | Nome | Efeito |
|---|---|---|
| `speed_boost` | Speed Boost | Reduz tempo de cooldown em 20% |
| `golden_eye` | Golden Eye | Próxima palavra golden garantida |
| `combo_lock` | Combo Lock | Trava combo 2× por 3 blocos |
| `extra_time` | Extra Time | +15 s no próximo bloco |
| `double_sats` | Double Sats | Recompensa 2× no próximo bloco |

### UTILITÁRIOS — Mini-game Decoder

Mini-game de decodificação: o jogador recebe um `txid` e tem **30 s**
(`DECODER_TIME_LIMIT`) para adivinhar a palavra BIP39 correspondente. Acertos
alimentam uma **streak** e contam **wins**. Erro ou timeout encerra a partida
do decoder.

---

## Aba COMPETIR

### RANKING

Leaderboard individual + pools do realm ativo.

### MISSÕES

- **Diárias:** 6 definições, **3 rotativas** por dia (seleção por
  `day_of_year % 3`). Reset em 00:00 UTC.
- **Semanal:** 1 missão, reset no domingo 00:00 UTC.

Definições diárias disponíveis:

| ID | Meta | Recompensa |
|---|---|---|
| `find_5_high_fee` | 5 High Fee | 2.000 sats |
| `earn_50k_round` | 50.000 sats em 1 rodada | 3.000 sats |
| `use_rbf` | 1 RBF bem-sucedido | 5.000 sats |
| `find_3_mev` | 3 MEV | 10.000 sats |
| `complete_3_blocks` | 3 blocos seguidos | 4.000 sats |
| `10_words_no_error` | 10 palavras sem erro | 2.500 sats |

O progresso é rastreado pelos mesmos `stats` das conquistas; `claim` resgata a
recompensa.

### SPRINT

Corrida relâmpago: **4 palavras** (`SPRINT_WORD_COUNT`) em **30 s**
(`SPRINT_TIME_LIMIT`). Recompensa com multiplicador **0,5**
(`SPRINT_REWARD_MULTIPLIER`). Leaderboard próprio de sprint por realm.

---

## Aba PERFIL

### VISÃO

Resumo do jogador: nickname, realm, saldo, nível, rank e estatísticas.

### PROGRESSÃO — Nível, XP e Rank

- **XP por palavra:** `comprimento × 10 + combo × 5`
  (`calculateWordXP`).
- **XP para o próximo nível:** `nível × 100` (`xp_to_next_level`).
- **Bônus passivos por nível:**
  - `time_bonus_seconds` = `min(nível, 10)` (máx +10 s);
  - `hint_discount_percent` = `min((nível // 3) × 10, 30)` (máx 30%).
- **Ranks temáticos** (10 tiers):

| Níveis | Rank |
|---|---|
| 1–9 | Script Kiddie |
| 10–19 | Node Operator |
| 20–29 | Hash Crafter |
| 30–39 | Block Miner |
| 40–49 | Mempool Hunter |
| 50–59 | Satoshi Disciple |
| 60–69 | Chain Validator |
| 70–79 | Hash Rate Lord |
| 80–89 | Block King |
| 90–99 | Bitcoin Legend |

### COLEÇÃO — Cards

Cards de bloco (`block_card`) são gerados a cada bloco e adicionados à
coleção. Raridade por peso:

| Raridade | Peso |
|---|---|
| Common | 60% |
| Rare | 25% |
| Epic | 10% |
| Legendary | 5% |

Blocos de **halving** (número de bloco múltiplo de 210.000,
`is_halving_block`) geram card especial. A coleção concede bônus passivo.

### ECONOMIA — Staking

Travar sats em stake para ganhar bônus de recompensa:

| Parâmetro | Valor |
|---|---|
| Mínimo | 1.000 sats |
| Durações | 1 h (+5%), 6 h (+15%), 24 h (+30%) |
| Penalidade por cancelamento antecipado | 10% |

`STAKE_BONUS_TABLE = {1: 0.05, 6: 0.15, 24: 0.30}`;
`STAKE_PENALTY_PERCENT = 0.10`.

---

## Aba SOCIAL

### CHAT

Chat por realm com histórico (últimas 20 mensagens), rate limiting (informado
na UI) e tokens/emojis. Mensagens são validadas pelo backend.

### EQUIPE — Amigos

Adicionar/remover amigos por username. Bônus de cooperação (`friends-coop-bonus`)
para jogadas em conjunto.

### MERCADO

Mercado P2P de power-ups: listar, comprar (`market/buy`), vender
(`market/sell`) e histórico. Preços definidos pelos vendedores; o backend
valida saldo e propriedade.

---

## Mecânicas transversais

### Conquistas (Achievements)

**28 conquistas** em 5 categorias, desbloqueadas por estatísticas acumuladas
e que concedem bônus permanentes:

| Categoria | Exemplos | Bônus típico |
|---|---|---|
| Volume | Primeira Palavra, Miner Mestre (5.000), Lenda da Mempool (10.000) | +1% a +8% de recompensa |
| Raridade | Primeiro Golden, MEV Master | +2% a +5% de recompensa |
| Velocidade | Combo Master, Speed Demon | 5% a 10% de desconto em dica |
| Exploração | Block Veteran, Realm Explorer, Epoch Survivor | +1% a +4% de recompensa |
| Social | Top 3, Pool Leader | +2% a +5% de recompensa |

Os bônus são somados (`applyAchievementBonus`) e aplicados à pontuação.

### Season Pass

- **Duração:** 28 dias (4 semanas).
- **Níveis:** 20 free + 20 premium (21–40).
- **XP por nível:** 100.
- **Recompensas free (1–20):** sats, hints, power-ups (`scanner`,
  `time_freeze`, `magnet`) e badge de temporada no nível 20.
- **Recompensas premium (21–40):** sats maiores, cards (rare/epic/legendary),
  power-ups (`precision`, `double_combo`, `scanner`) e bônus de recompensa
  (+5% por 7 dias, +10% por 14 dias).
- **Premium:** desbloqueável por compra; 7 dias grátis após completar a free.

### Energia

| Parâmetro | Valor |
|---|---|
| Máximo | 10 (`ENERGY_MAX`) |
| Recarga | 1 ponto a cada 30 min (`ENERGY_REFILL_INTERVAL = 1800`) |
| Compra | 2.000 sats → 3 pontos (`ENERGY_BUY_COST`/`ENERGY_BUY_AMOUNT`) |

### Crates

| Parâmetro | Valor |
|---|---|
| Preço | 5.000 sats (`CRATE_PRICES`) |
| Grátis | 1 a cada 10 blocos (`CRATE_FREE_INTERVAL`) |

Drops: power-ups (`CRATE_POWERUPS`), skins (`CRATE_SKINS`: Neon Grid, Retro
Terminal, Golden Hash) e block cards.

### Skill Tree

Três ramos com níveis progressivos:

| Ramo | Efeito |
|---|---|
| `mining` | +1 s / +2 s / +3 s de tempo base por rodada |
| `search` | bônus de busca/desconto |
| `lightning` | bônus do modo Lightning |

Cada nível custa pontos de skill; `applySkillBonuses` soma os bônus ativos.

### PWA

Service worker cacheia **apenas o shell** (HTML, CSS, JS, manifest, ícones,
fontes). Rotas `/api`, `/ws`, health, ranking, Swagger e OpenAPI **nunca**
entram no cache. Offline, o shell informa que conexão é necessária.
Atualizações aguardam ação explícita no banner.

### Sessão

O estado da partida é salvo em `sessionStorage` em 9 pontos críticos
(saldo, hardware, Lightning, RBF, resultado, etc.). `loadSessionState()`
restaura ao recarregar (F5); `startSession(realmIdOverride)` reconecta ao
mesmo realm; `clearSessionState()` limpa ao encerrar.

### Multi-rede

Regtest e Signet sobem por padrão; Mainnet é opt-in (`--profile mainnet`).
Cada realm tem nó, ingestor, volume e namespace Redis próprios. Saldo e
upgrades **não** atravessam realms.

---

## O que é real e o que é simulado

| Recurso | Natureza |
|---|---|
| Evento ZMQ, TXID, vsize, taxa, hash de bloco | integração real com o nó |
| Palavra BIP39 | derivação determinística para o jogo |
| Saldos em sats, carteira, hashrate, reward | simulação local |
| Hardware, dica, Lightning | mecânica local |
| Boss block, eventos globais, RBF | mecânica local (gatilho real de bloco) |
| Conquistas, missões, season, staking, mercado | estado Redis, score não autoritativo |
| Leaderboard | Redis real, score não autoritativo |

## Referências

- [API](API.md) — contratos REST e WebSocket
- [Fluxos](FLUXOS.md) — sequências de inicialização, transação, bloco
- [Módulos](MODULOS.md) — funções e responsabilidades por arquivo
- [Arquitetura](ARQUITETURA.md) — camadas e decisões
