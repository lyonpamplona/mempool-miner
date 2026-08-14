# API técnica

Base same-origin: /api para REST e /ws para WebSocket.

Não há autenticação nesta versão. Exponha a API apenas atrás do Nginx local até
implementar identidade, rate limiting e score autoritativo.

## GET /api/health

Confirma que o processo atende e que Redis responde.

Resposta 200:

~~~json
{
  "status": "ok"
}
~~~

Falha de Redis resulta em erro 5xx e torna o healthcheck do contêiner inválido.

## GET /api/leaderboard

Retorna até dez recordes em ordem decrescente.

~~~json
{
  "leaderboard": [
    {
      "username": "Miner_42",
      "score": 12500
    }
  ]
}
~~~

score é serializado como inteiro.

## POST /api/leaderboard

Registra somente um valor maior que o recorde atual do nickname.

Corpo:

~~~json
{
  "username": "Miner_42",
  "score": 12500
}
~~~

Regras:

| Campo | Regra |
|---|---|
| username | 1–12 caracteres após validação |
| username | letras/números Unicode, hífen e sublinhado |
| score | inteiro entre 0 e 2.147.483.647 |

Resposta 200:

~~~json
{
  "status": "success",
  "updated": true
}
~~~

updated false significa que o valor não superou o recorde. Entrada inválida
retorna 422 no formato padrão do FastAPI.

### Exemplo

    curl -X POST http://localhost:8010/api/leaderboard \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"Miner_42\",\"score\":12500}"

## WebSocket /ws/game

Conecte em ws://localhost:8010/ws/game. Em HTTPS use wss.

O cliente não precisa enviar comandos. O backend mantém uma tarefa receptora
apenas para detectar a desconexão.

### game_start

Primeira mensagem de cada conexão:

~~~json
{
  "action": "game_start",
  "network": "regtest",
  "game_mode": "mempool",
  "mempool_count": 0
}
~~~

### transaction_received

~~~json
{
  "action": "transaction_received",
  "mempool_count": 1,
  "word": "ABANDON",
  "tx_stub": "4a5e1e4b",
  "is_golden": false,
  "is_high_fee": true,
  "vsize": 250,
  "fee_rate_sat_vb": 24.5
}
~~~

| Campo | Origem |
|---|---|
| word | primeiro termo BIP39 derivado do TXID |
| tx_stub | oito primeiros caracteres do TXID |
| is_golden | TXID começa com 00 |
| is_high_fee | taxa efetiva supera HIGH_FEE_RATE_SAT_VB |
| vsize | getmempoolentry ou fallback 250 |
| fee_rate_sat_vb | fees.base convertido para sats/vB |

### block_mined

~~~json
{
  "action": "block_mined",
  "block_hash": "000000000000000000...",
  "mempool_count": 3
}
~~~

mempool_count vem de getmempoolinfo após o evento ou usa zero se RPC falhar.

## Redis interno

Não é API pública, mas integra os processos:

- canal: game_events;
- chave: mempool_count;
- Sorted Set: global_leaderboard.

## Documentação gerada

Com a stack ativa:

- Swagger: /backend-docs
- OpenAPI JSON: /openapi.json

A página visual complementar está em [api.html](api.html).

## Compatibilidade

Campos novos devem ser aditivos. Remover/renomear campos WebSocket exige
versionar o contrato, atualizar game.js, API.md, api.html e testes de integração.
