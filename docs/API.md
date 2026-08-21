# API pública

Este documento descreve somente o contrato necessário ao jogo. Credenciais,
endereços RPC/ZMQ, chaves Redis, tokens de lease, identificadores físicos de
nós e endpoints operacionais não fazem parte da superfície pública.

## Convenções

- `realm_id`: arena lógica escolhida a partir do catálogo;
- `network`: `regtest`, `signet` ou `mainnet`;
- `schema_version`: versão do envelope de eventos, atualmente `2`;
- conteúdo JSON usa UTF-8;
- novas propriedades podem ser adicionadas de forma compatível.

O cliente nunca envia um hostname de nó nem constrói uma chave de
infraestrutura. Um realm desconhecido resulta em HTTP `404` ou fechamento do
WebSocket com código de política.

## REST

### GET `/api/v1/health/live`

Confirma que a API responde:

```json
{"status":"ok"}
```

Este endpoint não revela versão de dependência, topologia ou estado detalhado
dos nós.

### GET `/api/v1/networks`

Retorna o catálogo sanitizado usado pelo seletor do jogo:

```json
{
  "schema_version": 2,
  "default_realm_id": "regtest",
  "networks": [
    {
      "realm_id": "regtest",
      "network": "regtest",
      "display_name": "Regtest local",
      "status": "ready",
      "playable": true,
      "initial_block_download": false,
      "verification_progress": 1.0,
      "pruned": false
    }
  ]
}
```

Estados conhecidos:

| status | significado público |
|---|---|
| `starting` | serviço iniciando |
| `syncing` | nó sincronizando |
| `ready` | realm disponível |
| `disabled` | profile opcional não iniciado |
| `unavailable` | heartbeat indisponível |
| `stopped` | ingestor encerrado ordenadamente |

O cliente deve confiar em `playable`. Um nó podado pode continuar jogável.

### GET `/api/v1/networks/{realm_id}/leaderboard`

Retorna até dez recordes isolados por realm:

```json
{
  "realm_id": "regtest",
  "leaderboard": [
    {"username":"Miner_42","score":12500}
  ]
}
```

### POST `/api/v1/networks/{realm_id}/leaderboard`

Corpo:

```json
{"username":"Miner_42","score":12500}
```

Regras atuais:

- nickname de 1 a 12 caracteres;
- letras, números, hífen e sublinhado;
- score inteiro entre `0` e `2147483647`;
- o recorde só aumenta.

Resposta:

```json
{"status":"ok","updated":true}
```

> O score ainda é calculado pelo navegador. O leaderboard é demonstrativo e
> não prova que uma partida legítima ocorreu.

### GET `/api/v1/networks/{realm_id}/pools`

Top 10 de pools (guildas) do realm:

```json
{
  "realm_id": "regtest",
  "pools": [{"pool_name": "Satoshi_Squad", "score": 48200}]
}
```

## Endpoints de mecânicas

Todos os endpoints abaixo usam o mesmo padrão de validação de `realm_id` e
`username` (1–12 caracteres, letras/números/hífen/sublinhado). O estado é
persistido no Redis por realm.

### Jogador e progresso

| Método | Rota | Uso |
|---|---|---|
| GET | `/player/{username}` | saldo, hardware, Lightning e estado do jogador |
| POST | `/player/{username}` | atualiza estado do jogador |
| GET | `/level/{username}` | nível, XP, rank e bônus passivos |
| POST | `/level/{username}/add-xp` | adiciona XP e verifica level-up |
| GET | `/achievements/{username}` | conquistas com status, progresso e bônus |
| POST | `/stats/{username}` | atualiza estatísticas (dispara desbloqueio) |
| GET | `/achievements/definitions` | catálogo das 28 conquistas |

### Missões

| Método | Rota | Uso |
|---|---|---|
| GET | `/missions/{username}` | 3 diárias rotativas + 1 semanal, com progresso |
| POST | `/missions/{username}/claim/{mission_id}` | resgata recompensa |
| POST | `/missions/{username}/update` | atualiza progresso |

### Skill tree

| Método | Rota | Uso |
|---|---|---|
| GET | `/skills/{username}` | ramos `mining`/`search`/`lightning` com níveis |
| POST | `/skills/{username}/upgrade` | compra nível em um ramo |

### Power-ups

| Método | Rota | Uso |
|---|---|---|
| GET | `/powerups/{username}` | inventário de power-ups |
| POST | `/powerups/activate` | ativa power-up na partida |

### Chat

| Método | Rota | Uso |
|---|---|---|
| POST | `/chat/send` | envia mensagem (rate limiting) |
| GET | `/chat/history?limit=20` | últimas mensagens |

### Mercado

| Método | Rota | Uso |
|---|---|---|
| GET | `/market/list` | anúncios ativos |
| POST | `/market/sell` | anuncia power-up para venda |
| POST | `/market/buy` | compra anúncio |
| GET | `/market/history` | histórico de transações |

### PvP

| Método | Rota | Uso |
|---|---|---|
| GET | `/pvp/match/{challenger}/{challenged}` | estado do duelo (60 s) |
| POST | `/pvp/challenge` | inicia desafio |
| POST | `/pvp/accept` | aceita desafio |
| POST | `/pvp/score` | envia pontuação do duelo |

### Cards e crates

| Método | Rota | Uso |
|---|---|---|
| GET | `/cards/{username}` | coleção de block cards |
| POST | `/crates/open` | abre crate (grátis ou 5.000 sats) |
| GET | `/crates/inventory` | inventário de drops |
| POST | `/crates/claim` | resgata drop pendente |

### Staking

| Método | Rota | Uso |
|---|---|---|
| POST | `/staking/stake` | trava sats (1.000+; 1/6/24 h) |
| POST | `/staking/unstake` | cancela (penalidade 10%) |
| GET | `/staking/status/{username}` | stake ativo |
| GET | `/staking/history/{username}` | histórico |

### Amigos

| Método | Rota | Uso |
|---|---|---|
| POST | `/friends/add` | adiciona amigo |
| POST | `/friends/remove` | remove amigo |
| GET | `/friends/{username}` | lista de amigos |

### Energia

| Método | Rota | Uso |
|---|---|---|
| GET | `/energy/status` | energia atual (máx 10, recarga 30 min) |
| POST | `/energy/spend` | consome 1 ponto |
| POST | `/energy/buy` | compra 3 pontos por 2.000 sats |

### Decoder

| Método | Rota | Uso |
|---|---|---|
| POST | `/decoder/start` | inicia mini-game (30 s) |
| POST | `/decoder/submit` | envia resposta |

### Season pass

| Método | Rota | Uso |
|---|---|---|
| GET | `/season/{username}` | temporada, nível, XP e recompensas |
| POST | `/season/{username}/add-xp` | adiciona XP (100/nível) |
| POST | `/season/{username}/claim/{reward_level}` | resgata recompensa |
| POST | `/season/{username}/buy-premium` | desbloqueia premium |

### Sprint

| Método | Rota | Uso |
|---|---|---|
| POST | `/sprint/start` | inicia corrida (4 palavras, 30 s) |
| POST | `/sprint/submit` | envia resultado |
| GET | `/sprint/leaderboard` | ranking de sprint |

### Eventos globais

| Método | Rota | Uso |
|---|---|---|
| GET | `/global-events` | evento global ativo/próximo do realm |

## WebSocket

Rota canônica:

```text
/ws/v1/game/{realm_id}
```

O cliente obtém o `realm_id` no catálogo e aguarda `game_start` antes de aceitar
eventos de jogo.

### `game_start`

```json
{
  "schema_version": 2,
  "action": "game_start",
  "realm_id": "regtest",
  "network": "regtest",
  "status": "ready",
  "playable": true,
  "initial_block_download": false,
  "verification_progress": 1.0,
  "pruned": false
}
```

### `transaction_received`

```json
{
  "schema_version": 2,
  "action": "transaction_received",
  "realm_id": "regtest",
  "epoch": "opaque-stream-id",
  "word": "ABANDON",
  "txid": "4a5e1e4baab89f3a32514a8a421d1845c2f6b7e9d0c3a5f8b2e6d1c4a7f0e3",
  "tx_stub": "4a5e1e4b",
  "is_golden": false,
  "is_high_fee": true,
  "is_mev": false,
  "vsize": 250,
  "fee_rate_sat_vb": 24.5,
  "multiplier": 3
}
```

`epoch` é uma identidade opaca de continuidade. O navegador a usa somente para
descartar callbacks ou eventos de uma geração anterior.

`txid` é o identificador completo da transação (64 hex). `tx_stub` mantém os
8 primeiros caracteres para exibição compacta. `is_mev` indica se a transação
foi classificada como MEV (critério: `int(txid[:8], 16) % 100 < 15`).
`multiplier` é o multiplicador de pontuação efetivo, já com eventos globais
aplicados (`fee_spike` 3×, `golden_rush` 5×, `mempool_flood` 2×,
`lightning_storm` 10×).

### `block_mined`

```json
{
  "schema_version": 2,
  "action": "block_mined",
  "realm_id": "regtest",
  "epoch": "new-opaque-stream-id"
}
```

### `boss_block`

Publicado a cada 50 blocos pelo script Lua de reconciliação. Inicia uma
rodada de boss (grade 15×15, 10 palavras, 45 s, ×5, loot de 50.000 sats):

```json
{
  "action": "boss_block",
  "realm_id": "regtest",
  "block_count": 150,
  "boss_hp": 10,
  "boss_grid_size": 15,
  "boss_words": 10,
  "boss_timer": 45,
  "boss_reward_multiplier": 5,
  "boss_loot": 50000
}
```

### Eventos globais (`event_preannounce`, `event_started`, `event_ended`)

O `GlobalEventScheduler` publica três ações por evento global
(`fee_spike`, `golden_rush`, `mempool_flood`, `lightning_storm`):

```json
{
  "schema_version": 2,
  "event_id": "global_event:regtest:fee_spike:event_started",
  "action": "event_started",
  "realm_id": "regtest",
  "event_type": "fee_spike",
  "event_label": "Fee Spike",
  "event_icon": "⚡",
  "event_description": "Todas as palavras são High Fee! 3× recompensa por 10 min.",
  "event_color": "#a855f7",
  "event_preannounced": false,
  "event_started_at": "2026-08-20T12:00:00+00:00",
  "event_ends_at": "2026-08-20T12:10:00+00:00"
}
```

`event_preannounce` é enviado 120 s antes do início (banner de aviso);
`event_ended` encerra o efeito. O estado atual também é consultável via
`GET /api/v1/networks/{realm_id}/global-events`.

### `network_status`

```json
{
  "schema_version": 2,
  "action": "network_status",
  "realm_id": "signet",
  "status": "syncing",
  "playable": false,
  "initial_block_download": true,
  "verification_progress": 0.82
}
```

Se `playable` mudar para `false`, o cliente encerra a rodada e retorna ao seletor.

## Compatibilidade

Aliases da primeira versão podem continuar ativos durante a migração, mas não
são parte do contrato recomendado para novos clientes. O frontend e o backend
devem ser publicados juntos enquanto não houver negociação explícita de versão.

## Documentação interativa

Swagger e o documento OpenAPI bruto ficam desabilitados por padrão. Quando
necessários em desenvolvimento, devem ser habilitados explicitamente e mantidos
fora do proxy público do jogo.
