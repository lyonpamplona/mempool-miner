# Auditoria de Mecânicas — 02: Economia

> Auditoria 100% da economia do Mempool Miner (sats, energia, upgrades, mercado, crates, staking).
> Valores exatos extraídos do código, com `path:linha`. Estado: pós-Fases 1–8 + auditoria final.

## 1. Moeda: sats (`balanceSatoshis`)

### 1.1 Definição e persistência
- Variável frontend: `let balanceSatoshis = 0;` — `frontend/game.js:344` (saldo inicial **0**).
- Fonte de verdade: campo `balance` do hash Redis do player state (`player_state_key(realm, username)`) — leitura em `backend/app/main.py:906`, escrita em `main.py:946`.
- **Sem TTL após correção**: `update_player_state` chama `persist()` para limpar TTL residual do código antigo (que zerava o saldo em 24h) — `main.py:947-950`; idem no claim de missões — `main.py:1488-1491`.
- Novo jogador: `balance` padrão `0` — `main.py:895`.
- Sincronização: frontend espelha o backend; se o backend tiver mais, adota; se o local tiver mais, mantém o local — `game.js:2056-2058`.

### 1.2 Fontes de entrada
| Fonte | Valor | path:linha |
|---|---|---|
| Palavra encontrada (jogo) | `(500·(1+bônus skill) + len·50) · combo · mult` | `game.js:2813-2819` |
| `baseReward` | 500; halving −2% a cada 10 blocos, mín. 50% | `game.js:363, 2346-2348` |
| Modo Lightning | ×10 nas palavras | `game.js:2820` |
| Golden / High Fee | ×5 / ×3 (multiplicador do backend) | `game.js:2817-2819` |
| MEV secreto | +50.000 | `game.js:2858-2865` |
| Boss derrotado (loot) | +50.000 | `game.js:1241, 2846` |
| Missões diárias/semanal | 2.000–50.000 (tabela §1.4) | `main.py:1467-1475` |
| Crate (drop sats, 60%) | 1.000–10.000 | `main.py:3705-3715` |
| Decoder (acerto) | +5.000 | `main.py:4823` |
| Sprint | variável (a confirmar) | `main.py:5020` |
| Venda no mercado P2P | preço − 5% de taxa | `main.py:2771, 2816` |
| PvP (vencedor) | 10% do saldo do perdedor | `main.py:2953, 3214-3220` |
| Staking (expiração) | devolução do `amount` (bônus NÃO pago — §9) | `main.py:4194` |
| Season pass (recompensas) | variável | `season_pass.py:275` |

### 1.3 Saídas (gastos)
| Gasto | Valor | path:linha |
|---|---|---|
| Dica (hint) | 5.000 (com desconto de conquistas/skill) | `game.js:355, 2110-2125` |
| Hardware (3 níveis) | 100.000 / 500.000 / 2.000.000 | `game.js:347, 2130-2149` |
| L2 Lightning | 1.000.000 | `game.js:356, 2154-2160` |
| RBF (resgate de bloco órfão) | 100.000 | `game.js:3100, 3129-3130` |
| Slashing (erro) | 5% do saldo | `game.js:371, 2939-2942` |
| Energia (ENERGY_RECHARGE) | 2.000 por +3 | `main.py:4423-4424` |
| Crate | 5.000 | `main.py:3662` |
| Compra no mercado P2P | preço + 5% de taxa | `main.py:2450, 2769-2771` |
| Staking | `amount` travado | `main.py:4050-4052` |
| Season premium | 50.000 | `season_pass.py:324` |

### 1.4 Tabela de missões (recompensas)
| Missão | Recompensa | path:linha |
|---|---|---|
| `find_5_high_fee` | 2.000 | `main.py:1468` |
| `earn_50k_round` | 3.000 | `main.py:1469` |
| `use_rbf` | 5.000 | `main.py:1470` |
| `find_3_mev` | 10.000 | `main.py:1471` |
| `complete_3_blocks` | 4.000 | `main.py:1472` |
| `10_words_no_error` | 2.500 | `main.py:1473` |
| `find_100_words_week` (semanal) | 50.000 | `main.py:1474` |

## 2. Energia

| Parâmetro | Valor | path:linha |
|---|---|---|
| Máximo | 10 | `main.py:4421` |
| Custo por rodada | 1 | `main.py:4499-4500` |
| Recarga natural | +1 a cada 30 min (1800 s), calculada na leitura | `main.py:4422, 4477-4480` |
| Compra (ENERGY_RECHARGE) | **2.000 sats por +3 energia — confirmado** | `main.py:4423-4424` |
| Refund | 1 energia devolvida se a rodada falhar | `main.py:4538-4550` |
| Idempotência spend/refund | TTL 24 h por round_id | `main.py:4425` |
| TTL do estado de energia | 30 dias (reseta para 10/10) | `main.py:4426` |

- UI: barra `index.html:106-113`; botão "2,000 SATS" `index.html:260`; polling a cada 10 s `game.js:5555`; `buyEnergy()` `game.js:5608-5641`; `spendEnergy()` `game.js:5559-5605`.

## 3. Upgrades (tab UPGRADES)

| Upgrade | Custo | Efeito | Nível máx | Definição |
|---|---|---|---|---|
| Hardware (CPU Miner → GPU Rig → ASIC Antminer → Quantum Node) | 100.000 / 500.000 / 2.000.000 | +10 s permanentes no limite da rede por nível | 3 upgrades (4 tiers) | `game.js:346-347, 2130-2149`; `index.html:240-246` |
| L2 Lightning | 1.000.000 | Grid 8×8, recompensas ×10, canal de 5 blocos | 1 (recompra após expirar) | `game.js:356, 410, 2154-2188`; `index.html:248-254` |
| ENERGY_RECHARGE | 2.000 | +3 energia | ilimitado | `main.py:4423-4424`; `index.html:256-263` |
| CRATE | 5.000 | abre crate (drops §4) | ilimitado | `main.py:3662`; `index.html:266-280` |
| TX_DECODER | grátis (mini-game) | +5.000 sats + power-up aleatório por acerto | ilimitado | `main.py:4781-4841`; `index.html:282-291` |
| Dica (hint, in-game) | 5.000 (desconto por conquistas/skill) | revela direção de 1 palavra | ilimitado | `game.js:355, 2110-2125, 3441` |
| RBF (in-game) | 100.000 | +15 s na rodada (resgate de bloco órfão) | ilimitado | `game.js:3100-3101, 3124-3153` |
| Skill tree (tab PERFIL) | 1 ponto de habilidade por nível (pontos vêm do nível do jogador) | ramos mining/search/lightning | 5 por ramo | `main.py:1679-1756, 1759+` |
| Season premium (tab PERFIL) | 50.000 | recompensas premium | — | `season_pass.py:324-344`; `main.py:4938` |

## 4. Crates

- Preço: **5.000 sats** — `main.py:3662` (`CRATE_PRICES = {"crate": 5000}`).
- Crate grátis: **1 a cada 10 blocos minerados** — `main.py:3663` (`CRATE_FREE_INTERVAL = 10`); claim em `main.py:3908`; UI `game.js:7211`.
- Botões UI: FREE / 5K — `index.html:275-276`.

| Drop | Probabilidade | Conteúdo | path:linha |
|---|---|---|---|
| sats (comum) | 60% | 1.000–10.000 sats | `main.py:3705-3715` |
| Power-up (incomum) | 20% | time_freeze / scanner / double_combo / magnet / precision | `main.py:3716-3726, 3666-3672` |
| Block card (raro) | 12% | raridade rare ou epic | `main.py:3727-3737` |
| Skin (raro) | 6% | Neon Grid / Retro Terminal / Golden Hash / Dark Matter | `main.py:3738-3748, 3675-3680` |
| Legendário | 2% | Halving Boost / Mempool Lord — bônus permanente +5% | `main.py:3749-3759, 3683-3686` |

- Abertura: `main.py:3771-3822` (deduz 5.000 ou consome crate grátis; drop sats creditado em `balance` em `main.py:3819-3822`).

## 5. Mercado P2P (tab SOCIAL)

- **Taxa**: 5% (`MARKET_FEE_RATE = 0.05`, `main.py:2450`) — cobrada **na compra**: comprador paga `preço + 5%`, vendedor recebe `preço − 5%` (`main.py:2768-2771, 2815-2816`). Venda não cobra taxa (`main.py:2626-2627`).
- **Vender**: preço mínimo 100 sats (`main.py:2463`); power-up sai do inventário e o listing entra em Sorted Set ordenado por preço; TTL do listing 7 dias (`main.py:2452, 2621-2697`).
- **Comprar**: transação Lua atômica — valida listing, preço inalterado e saldo; transfere saldo e item (`main.py:2719-2839`).
- **Precificação sugerida**: mediana dos últimos 50 preços de venda; sem histórico, usa o preço base do power-up (`main.py:2495-2525`).
- **Preços base de referência** (`POWERUP_DEFINITIONS`, `main.py:2143-2189`): time_freeze 10.000 · scanner 5.000 · double_combo 15.000 · magnet 8.000 · precision 12.000.
- **UI** (tab SOCIAL → MARKETPLACE, `index.html:476-507`):
  - Toggle **COMPRAR/VENDER** (`index.html:481-482`): VENDER com 1º clique abre a seção de venda, 2º clique executa a venda (`game.js:6420-6435`, correção Fase 8 — antes a seção ficava `display:none` permanente).
  - **CTA nos estados vazios (Fase 8)**:
    - Browse vazio: "Nenhum item à venda no momento. Venda o seu na seção VENDER acima — ou jogue para ganhar power-ups." (`game.js:6215-6230`).
    - Vender vazio: "Você não tem power-ups para vender. Jogue para ganhar power-ups (crates, conquistas, season pass) e volte aqui." (`index.html:489-495`; `game.js:6329-6333`).
  - Filtro por power-up (`index.html:497-504`); histórico mostra últimas 20 vendas (`game.js:6288`).

## 6. Staking

| Parâmetro | Valor | path:linha |
|---|---|---|
| Quanto se stakeia | livre, mínimo 1.000 sats (frontend) | `game.js:4771-4773` |
| Durações | 1 h / 6 h / 24 h | `main.py:4035-4039` |
| "Rendimento" | 1 h: +5% · 6 h: +15% · 24 h: +30% | `main.py:3991-3995` |
| Cancelamento antecipado | penalty 10% — devolve 90% | `main.py:3996, 4085-4118` |
| Expiração natural | devolve o `amount` sem penalty | `main.py:4187-4208` |
| Stakes simultâneos | 1 por jogador (409) | `main.py:4024-4030` |
| TTL da chave de stake | duração + 1 h de margem | `main.py:4068` |

- **⚠️ O bônus (5/15/30%) é armazenado e exibido, mas NUNCA creditado** — a expiração devolve apenas o `amount` (`main.py:4194`). Ver §9 (ALTO).
- Frontend: duração padrão 6 h (`game.js:4537, 991`); countdown + polling a cada 30 s (`game.js:4625-4630`); histórico últimos 10 (`game.js:4725`).

## 7. Fluxo de sats (resumo)

| Entrada | Valor típico | | Saída | Valor típico |
|---|---|---|---|---|
| Palavra (jogo) | ~500–2.500 (com combos/mults) | | Dica | 5.000 |
| MEV | 50.000 | | Hardware | 100K–2M |
| Boss loot | 50.000 | | Lightning | 1.000.000 |
| Missões | 2.000–50.000 | | RBF | 100.000 |
| Crate (60%) | 1.000–10.000 | | Slashing | 5% do saldo |
| Decoder | 5.000 | | Energia | 2.000 (+3) |
| Venda no mercado | preço − 5% | | Crate | 5.000 |
| PvP (10% do perdedor) | variável | | Compra no mercado | preço + 5% |
| Staking (expiração) | `amount` (sem bônus) | | Staking | `amount` travado |

## 8. Faucet regtest

- Configuração: `FAUCET_INTERVAL=20 s`, `FAUCET_TXS=12`, `BLOCK_INTERVAL=90 s` — `bitcoin/entrypoint.sh:107-109`.
- A cada 20 s: 12 transações de 0,001 BTC (`entrypoint.sh:134-136`); a cada 90 s: 1 bloco minerado (`entrypoint.sh:142-148`).
- **Papel na economia**: regtest não tem tráfego orgânico — o faucet é a ÚNICA fonte de transações da mempool (`docs/baseline-ingestao.md:98`). Ele mantém a mempool populada e o tip fresco (evita IBD, emite `block_mined`), alimentando o feed de transações do qual as palavras do jogo são derivadas. **Não é fonte de sats do jogo** — os sats são 100% simulados (Redis); o faucet é infraestrutura de dados, não de moeda.

## 9. Pontas soltas

| Severidade | Item | path:linha |
|---|---|---|
| **ALTO** | Bônus de staking (5/15/30%) é armazenado e exibido na UI, mas nunca creditado: a expiração devolve apenas o `amount` — o "rendimento" prometido não existe | `main.py:4188-4195` |
| **MÉDIO** | Compras in-game (hint, hardware, lightning, RBF) e slashing são **apenas frontend** — não há endpoint backend que debite esses valores; se a `syncPlayerState` falhar, o saldo diverge | `game.js:2110-2188, 3129-3130, 2939-2942` |
| **MÉDIO** | Inventário de power-ups recebe TTL de 24 h em cada operação — power-ups obtidos (crates/decoder/mercado) podem sumir se o jogador não operar por 24 h | `main.py:2231, 2252, 2685` |
| **MÉDIO** | Sincronização de saldo "quem tiver mais, vence" — sessões concorrentes podem duplicar créditos | `game.js:2056-2058` |
| **BAIXO** | Logger de staking imprime literalmente "(+.1f% bonus)" em vez do valor do bônus (format specifier fora do `%`) | `main.py:4071` |
| **BAIXO** | `POWERUP_DEFINITIONS["price"]` só é usado como fallback de preço sugerido — não existe loja direta de power-ups com sats | `main.py:2518` |
| **BAIXO** | Venda no mercado: frontend valida só `price > 0`; o backend impõe mínimo de 100 sats (erro 400) | `game.js:6376`; `main.py:2463` |
| **BAIXO** | Bônus legendário +5% (crates) é armazenado em `legendary_bonus`, mas a aplicação nas recompensas não foi verificada | `main.py:3796`; `game.js:7112` |
| **BAIXO** | Estado de energia tem TTL de 30 dias (reseta para 10/10) — comportamento diferente do saldo (persistente, sem TTL) | `main.py:4426` |
