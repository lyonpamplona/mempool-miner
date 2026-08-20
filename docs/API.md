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
  "tx_stub": "4a5e1e4b",
  "is_golden": false,
  "is_high_fee": true,
  "vsize": 250,
  "fee_rate_sat_vb": 24.5
}
```

`epoch` é uma identidade opaca de continuidade. O navegador a usa somente para
descartar callbacks ou eventos de uma geração anterior.

### `block_mined`

```json
{
  "schema_version": 2,
  "action": "block_mined",
  "realm_id": "regtest",
  "epoch": "new-opaque-stream-id"
}
```

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
