# Relatório de Análise Técnica — Mempool Miner Backend

**Data:** 2026-08-16
**Escopo:** backend/app/ (main.py, engine.py, ingestor.py, storage.py, blockchain.py, config.py, events.py)
**Total linhas analisadas:** ~3.000

---

## Resumo Executivo

O backend do Mempool Miner apresenta uma arquitetura **bem estruturada** com separação clara de responsabilidades, uso correto de Lua scripts para atomicidade Redis, e padrões de segurança sólidos (CORS, TrustedHost, sanitização de eventos). No entanto, foram identificados **28 problemas** distribuídos em 6 categorias, incluindo 5 críticos, 12 médios e 11 baixos.

| Categoria | Crítico | Médio | Baixo | Total |
|-----------|---------|-------|-------|-------|
| Arquitetura | 1 | 3 | 2 | 6 |
| Redis | 1 | 3 | 2 | 6 |
| WebSocket | 1 | 2 | 1 | 4 |
| Bitcoin Core | 1 | 2 | 1 | 4 |
| Segurança | 1 | 1 | 3 | 5 |
| Observabilidade | 0 | 1 | 2 | 3 |

---

## 1. ARQUITETURA

### 1.1 [CRÍTICO] Memory leak em `EventRelay.queue` — eventos acumulam indefinidamente
- **Localização:** `main.py:784`, `main.py:802-812`
- **Descrição:** O `EventRelay` armazena eventos em um `asyncio.Queue(maxsize=1000)` que é alimentado pelo `_listen()` loop (linha 802-812). O `ws_sender` consome eventos com `relay.queue.get()` (linha 886), mas quando não há conexões WebSocket ativas, os eventos continuam chegando do PubSub e acumulam na fila. Quando a fila enche, eventos são descartados silenciosamente (linha 808-812). Pior: quando há conexões WebSocket, cada evento é consumido por **apenas um** `ws_sender` (porque `queue.get()` remove o item), então **apenas um cliente recebe cada evento** — os outros clientes perdem eventos.
- **Impacto:** Crítico. Com múltiplos clientes conectados, cada evento é entregue a apenas um cliente. Os demais ficam com stream incompleto.
- **Sugestão:** Substituir o Queue por um padrão fan-out: manter uma lista de subscribers e broadcastar cada evento para todos. Exemplo:
  ```python
  class EventRelay:
      def __init__(self):
          self.subscribers: list[asyncio.Queue[str]] = []
      async def subscribe(self) -> asyncio.Queue[str]:
          q = asyncio.Queue(maxsize=1000)
          self.subscribers.append(q)
          return q
      async def broadcast(self, event: str):
          for q in self.subscribers:
              try: q.put_nowait(event)
              except asyncio.QueueFull: pass
  ```

### 1.2 [MÉDIO] `recent_events()` com lógica de drain/reinsert racy e O(n²)
- **Localização:** `main.py:828-845`
- **Descrição:** O método `recent_events()` drena toda a fila, depois reinsere. Entre o drain e a reinsert, outro coroutine pode consumir da fila vazia. Além disso, a condição `while tmp or (not tmp and self.queue.qsize() > 0)` é redundante — o `while True` com try/except `QueueEmpty` já cobre. Se a fila encher durante a reinsert (linha 843), itens são perdidos silenciosamente.
- **Impacto:** Médio. Eventos podem ser perdidos durante a reinsert se a fila estiver cheia.
- **Sugestão:** Remover `recent_events()` — não é usado em nenhum endpoint. Se necessário, usar um snapshot separado (ex: lista circular com TTL).

### 1.3 [MÉDIO] `redis_client` global compartilhado entre main.py e ingestor.py sem pool isolation
- **Localização:** `main.py:189-194`, `ingestor.py:748-753`
- **Descrição:** O `redis_client` em `main.py` é um módulo-level singleton criado no import time. O `ingestor.py` cria seu próprio cliente (linha 748). Ambos usam `decode_responses=True` e timeouts de 5s. Se o processo API e o ingestor rodarem no mesmo container (o que não é o caso pelo design), haveria conflito. O problema real é que o `redis_client` global em `main.py` é usado por **todos os endpoints e WebSockets simultaneamente** sem connection pooling explícito — o `redis.asyncio` cria conexões sob demanda, mas não há limite configurado de conexões máximas.
- **Impacto:** Médio. Sob carga alta, o número de conexões Redis pode crescer sem limite, esgotando file descriptors.
- **Sugestão:** Usar `redis.ConnectionPool` com `max_connections` explícito:
  ```python
  pool = redis.ConnectionPool.from_url(redis_url, max_connections=20, decode_responses=True)
  redis_client = redis.Redis(connection_pool=pool)
  ```

### 1.4 [MÉDIO] `EventRelay` criado no lifespan mas `get_relay()` pode criar duplicatas
- **Localização:** `main.py:264-269`, `main.py:848-854`
- **Description:** No `lifespan` (linha 264-269), relays são criados para todos os realms do `NETWORK_CATALOG`. Mas `get_relay()` (linha 848-854) pode criar um relay adicional se o `realm_id` não estiver em `_event_relays`. Se um WebSocket conectar para um realm não-catalogado antes do lifespan terminar, ou se `release_relay()` remover um relay, `get_relay()` cria um novo que **não é rastreado pelo lifespan** e nunca será encerrado no shutdown.
- **Impacto:** Médio. Memory leak de tarefas asyncio e conexões PubSub órfãs.
- **Sugestão:** No `lifespan.finally`, iterar sobre todos os relays existentes (não apenas os do catálogo) e encerrá-los. Ou proibir `get_relay()` para realms fora do catálogo.

### 1.5 [BAIXO] `logging.basicConfig` chamado em múltiplos módulos
- **Localização:** `main.py:43-46`, `ingestor.py:40-43`
- **Descrição:** Ambos `main.py` e `ingestor.py` chamam `logging.basicConfig()`. Como são processos separados (API vs ingestor), isso funciona, mas se alguém importar ambos no mesmo processo (ex: testes), a configuração é sobrescrita.
- **Impacto:** Baixo. Afeta apenas cenários de teste ou desenvolvimento.
- **Sugestão:** Mover `basicConfig` para um módulo `logging_config.py` compartilhado, ou usar `logging.config.dictConfig`.

### 1.6 [BAIXO] `import asyncio as _asyncio` inline em `validate_declared_network`
- **Localização:** `engine.py:272`
- **Descrição:** O import `import asyncio as _asyncio` dentro do método `validate_declared_network` é desnecessário — `asyncio` já está importado no topo do módulo (linha 5). O alias `_asyncio` não é usado; o código usa `asyncio.sleep` diretamente (linha 311).
- **Impacto:** Baixo. Código morto.
- **Sugestão:** Remover a linha 272.

---

## 2. REDIS

### 2.1 [CRÍTICO] `COMMIT_TRANSACTION_SCRIPT`: race condition no `cjson.decode` + `publish`
- **Localização:** `ingestor.py:58-77`
- **Descrição:** O script Lua decodifica o evento JSON (linha 73: `cjson.decode(ARGV[5])`), modifica o campo `mempool_count` (linha 74), e re-encode + publish (linha 75). Se o JSON em `ARGV[5]` for inválido ou malformado, `cjson.decode` levanta um erro Lua que **aborta todo o script atomicamente** — incluindo o `sadd` de deduplicação (linha 62) e o `incr` do contador (linha 68). A transação é perdida, mas o txid NÃO é adicionado ao dedupe set, então a próxima tentativa reprocessa a mesma TX.
- **Impacto:** Crítico. Em cenários de JSON malformado, transações são reprocessadas indefinidamente, causando duplicação de eventos.
- **Sugestão:** Adicionar proteção `pcall` no decode:
  ```lua
  local ok, event = pcall(cjson.decode, ARGV[5])
  if not ok then return {1, 0} end  -- commit sem publish
  event['mempool_count'] = count
  redis.call('publish', KEYS[4], cjson.encode(event))
  ```

### 2.2 [MÉDIO] Dedupe sets sem TTL consistente — `seen:{epoch}` pode acumular
- **Localização:** `ingestor.py:65`, `storage.py:60-62`
- **Descrição:** O dedupe set (`seen:{epoch}`) recebe `expire` de 3600s (1 hora) no Lua script (ingestor.py:65). Se uma epoch durar mais que 1 hora (possível em redes com baixa atividade de blocos), o dedupe expira e transações duplicadas são publicadas. Em mainnet, os blocos vêm a cada ~10 minutos, então 1 hora cobre ~6 blocos — aceitável. Mas em signet/regtest com blocos lentos, pode ser insuficiente.
- **Impacto:** Médio. Duplicação de eventos em epochs longas.
- **Sugestão:** Aumentar o TTL para 3600*2 ou usar um TTL baseado no tempo médio de bloco da rede. Alternativamente, não usar TTL e limpar explicitamente no `handle_block`.

### 2.3 [MÉDIO] `RESET_SCRIPT`: `leaderboard_reset` publica `realm_id` errado
- **Localização:** `ingestor.py:618-622`
- **Descrição:** O evento `leaderboard_reset` publicado pelo script Lua usa `realm_id = epoch_id` (linha 620), onde `epoch_id` é o `ARGV[2]` que passa `self.config.realm_id` (linha 636). Isso funciona por coincidência — o `realm_id` do config é passado como `epoch_id` no ARGV. Mas o campo no evento JSON é `realm_id`, e o valor é o realm_id correto. O problema é que o campo `epoch` no evento usa `new_epoch` (o contador incrementado), mas o contrato público em `main.py:98` espera `epoch` como o hash do bloco, não um número sequencial. Isso pode confundir clientes que esperam o formato padrão.
- **Impacto:** Médio. Inconsistência semântica no campo `epoch` do evento `leaderboard_reset`.
- **Sugestão:** Documentar explicitamente que `leaderboard_reset.epoch` é um número sequencial, não um block hash. Ou adicionar um campo separado `leaderboard_epoch`.

### 2.4 [MÉDIO] `COMMIT_STATUS_SCRIPT`: `node_status_key` com TTL 30s mas `realm_state_key` sem TTL
- **Localização:** `ingestor.py:89-101`
- **Descrição:** O script seta `node_status_key` com `EX 30` (linha 96) mas `realm_state_key` sem TTL (linha 97). Se o ingestor crashar, o `node_status_key` expira em 30s (bom para health check), mas o `realm_state_key` persiste indefinidamente com dados stale. A API em `main.py:468` lê ambos e prefere `status` (node_status_key) se existir, mas se o node_status expirar, a API usa o realm_state stale.
- **Impacto:** Médio. Dados stale podem ser exibidos após crash do ingestor.
- **Sugestão:** Adicionar TTL ao `realm_state_key` também, ou usar o mesmo TTL de 30s.

### 2.5 [BAIXO] Lua scripts não são cached com `sha` — re-parse a cada chamada
- **Localização:** `ingestor.py:200`, `ingestor.py:388`, `ingestor.py:477`, etc.
- **Descrição:** Todos os Lua scripts são passados como string para `redis.eval()` a cada chamada. O Redis server cacheia scripts internamente, mas o Python client re-envia o source toda vez. Para alta frequência (transações), isso adiciona overhead de rede.
- **Impacto:** Baixo. Overhead de rede em ~100-200 bytes por chamada.
- **Sugestão:** Usar `redis.evalsha()` com script pre-loaded via `script_load()`, ou usar `redis.register_script()` do redis-py que gerencia o SHA automaticamente.

### 2.6 [BAIXO] `MIGRATE_LEADERBOARD_SCRIPT`: sem proteção contra leaderboard gigante
- **Localização:** `storage.py:12-21`
- **Descrição:** O script de migração faz `zrange KEYS[2] 0 -1 WITHSCORES` que carrega **todo** o leaderboard legacy em memória Lua. Se o leaderboard legacy tiver milhares de entradas, isso consome memória no servidor Redis e bloqueia o event loop durante a execução.
- **Impacto:** Baixo. Afeta apenas a primeira execução pós-deploy.
- **Sugestão:** Usar `ZRANGEBYSCORE` com paginação ou limitar a migração aos top 100.

---

## 3. WEBSOCKET

### 3.1 [CRÍTICO] `ws_sender` consome eventos do Queue — apenas UM cliente recebe cada evento
- **Localização:** `main.py:886`
- **Descrição:** O `ws_sender` usa `relay.queue.get()` (linha 886) que **remove** o evento da fila. Se houver N clientes conectados ao mesmo realm, cada evento é entregue a apenas UM cliente (o primeiro `ws_sender` a chamar `get()`). Os outros N-1 clientes nunca recebem esse evento. Este é o bug mais severo do sistema — a funcionalidade core de broadcast WebSocket está quebrada.
- **Impacto:** Crítico. A funcionalidade principal do WebSocket (stream de eventos em tempo real) não funciona corretamente com múltiplos clientes.
- **Sugestão:** Ver item 1.1. Substituir o Queue por um padrão fan-out com lista de subscribers.

### 3.2 [MÉDIO] WebSocket sem backpressure — `send_text` pode bloquear ou falhar silenciosamente
- **Localização:** `main.py:905`
- **Descrição:** O `ws_sender` chama `await websocket.send_text(serialized)` (linha 905) sem verificar o buffer de saída do WebSocket. Se o cliente for mais lento que o stream de eventos (ex: rede lenta), o buffer interno do Starlette cresce indefinidamente, consumindo memória do servidor. A única proteção é o `RuntimeError` catch (linha 906-908), que só dispara quando o WebSocket é fechado.
- **Impacto:** Médio. Memory leak do servidor sob clientes lentos.
- **Sugestão:** Adicionar limite de backpressure: se o buffer ultrapassar um threshold, descartar eventos ou desconectar o cliente lento.

### 3.3 [MÉDIO] `ws_receiver` timeout de 5 minutos pode ser muito longo para produção
- **Localização:** `main.py:919-925`
- **Descrição:** O `ws_receiver` usa `timeout=300` (5 minutos) para detectar clientes órfãos. Em produção, conexões órfãs mantêm recursos (task, relay subscription) por até 5 minutos antes de serem encerradas. Para um serviço com centenas de conexões, isso significa recursos significativos retidos.
- **Impacto:** Médio. Recursos retidos por conexões órfãs.
- **Sugestão:** Reduzir para 60-120 segundos, ou usar WebSocket ping/pong nativo (`websocket.send_text` com opcode ping).

### 3.4 [BAIXO] `serve_websocket` não limpa tasks no `finally` se `sender_task`/`receiver_task` forem None
- **Localização:** `main.py:998-1001`
- **Descrição:** O `finally` block (linha 998-1001) tenta cancelar `sender_task` e `receiver_task`, mas verifica `if task and not task.done()`. Se a exceção ocorrer antes da criação das tasks (ex: falha em `sanitize_public_event` na linha 979-981), as tasks são `None` e o `finally` funciona corretamente. Porém, se a exceção ocorrer **durante** a criação (entre `create_task` e a atribuição), a task pode ser criada mas não atribuída, vazando.
- **Impacto:** Baixo. Raro, requer timing específico.
- **Sugestão:** Criar as tasks antes do try block, ou usar variáveis temporárias.

---

## 4. BITCOIN CORE

### 4.1 [CRÍTICO] `is_halving_block` usa `mempool_count % 210000` em vez do número do bloco
- **Localização:** `ingestor.py:554`
- **Descrição:** O campo `is_halving_block` é calculado como `current_count % 210000 == 0` onde `current_count` é o tamanho do mempool (número de transações pendentes), NÃO o número do bloco. O halving do Bitcoin ocorre a cada 210.000 **blocos**, não baseado no tamanho do mempool. Este campo é semanticamente incorreto e sempre será `False` na prática (o mempool raramente tem exatamente 210.000 transações).
- **Impacto:** Crítico. Funcionalidade de jogo (Halving Protocol) não funciona como documentado.
- **Sugestão:** Usar o número do bloco do `getblockchaininfo` ou do `block_height` do ZMQ:
  ```python
  "is_halving_block": block_height % 210000 == 0
  ```

### 4.2 [MÉDIO] `get_tx_metadata` com retry fixo de 3 tentativas pode ser insuficiente durante reorg
- **Localização:** `engine.py:154-159`
- **Descrição:** O retry loop (3 tentativas, 500ms cada) para `getmempoolentry` pode ser insuficiente durante chain reorganizations ou picos de carga do Bitcoin Core. Se a TX foi removida do mempool por um reorg, o RPC retorna erro e o retry não ajuda — mas o código trata isso como "RPC indisponível" e continua retrying. Após 3 falhas, `get_tx_metadata` retorna valores default (vsize=250, fee_rate=0.0) sem indicar que o RPC falhou.
- **Impacto:** Médio. Dados de fee/vsize incorretos durante reorgs, sem sinalização de erro.
- **Sugestão:** Retornar um flag `rpc_failed` no metadata, ou propagar o erro para o ingestor decidir se descarta a TX.

### 4.3 [MÉDIO] ZMQ `hashblock` não valida o formato do block_hash
- **Localização:** `blockchain.py:104-116`
- **Descrição:** O `hashblock` do ZMQ envia 32 bytes raw. O código faz `binascii.hexlify(body).decode("ascii")` (linha 113) sem verificar se `len(body) == 32`. Se o Bitcoin Core enviar um payload inesperado (bug, versão diferente), o hash terá tamanho errado e será usado como `self.epoch` — quebrando a lógica de deduplicação e epoch validation.
- **Impacto:** Médio. Epoch inválida pode causar perda ou duplicação de todas as transações subsequentes.
- **Sugestão:** Validar `len(body) == 32` antes de hexlify:
  ```python
  if len(body) != 32:
      logger.error("hashblock ZMQ com tamanho inválido: %d bytes", len(body))
      raise ValueError("block_hash inválido")
  ```

### 4.4 [BAIXO] `httpx.AsyncClient` com `max_connections=10` pode ser insuficiente para múltiplos realms
- **Localização:** `engine.py:48-51`
- **Descrição:** O `httpx.AsyncClient` é criado com `max_connections=10`. Cada `GameEngine` instance tem seu próprio client, então isso é por-ingestor. Com 3 RPC calls concorrentes possíveis (`getmempoolentry`, `getmempoolinfo`, `getblockchaininfo`), 10 conexões é suficiente para um único ingestor. Mas se o `process_interval_seconds` for muito baixo (default 1.0s no config, mas pode ser 0.01), múltiplas calls podem se sobrepor.
- **Impacto:** Baixo. Apenas relevante com `process_interval_seconds` muito baixo.
- **Sugestão:** Aumentar para 20 ou tornar configurável via `NodeConfig`.

---

## 5. SEGURANÇA

### 5.1 [CRÍTICO] `PlayerStateUpdate` permite write-arbitrary-user — nenhum ownership check
- **Localização:** `main.py:745-763`
- **Descrição:** O endpoint `POST /api/v1/networks/{realm_id}/player/{username}` aceita um `PlayerStateUpdate` com `username` no path E no body. Qualquer cliente pode atualizar o estado de **qualquer** jogador, incluindo `balance`, `hardware_level`, `combo_multiplier`, etc. Não há autenticação, nem verificação de que o cliente é o dono do username. Um atacante pode:
  - Setar `balance` de qualquer jogador para qualquer valor
  - Ativar `lightning_active` para si mesmo
  - Manipular `combo_multiplier` para inflar pontuações
- **Impacto:** Crítico. Manipulação completa do estado do jogo.
- **Sugestão:** Adicionar autenticação (JWT, API key) e verificar que o `username` no path corresponde ao usuário autenticado. Ou remover o endpoint de update e fazer todas as atualizações via ingestor/server-side.

### 5.2 [MÉDIO] `ScoreSubmit` sem rate limiting — leaderboard pode ser spamado
- **Localização:** `main.py:654-665`
- **Descrição:** O endpoint `POST /api/v1/networks/{realm_id}/leaderboard` não tem rate limiting. Um cliente pode enviar milhares de requisições por segundo, cada uma fazendo `ZADD GT CH` no Redis. Embora `GT` previna scores menores, o volume de requisições pode sobrecarregar o Redis e o servidor.
- **Impacto:** Médio. DoS do endpoint de leaderboard.
- **Sugestão:** Adicionar rate limiting (ex: `slowapi` ou middleware custom) — ex: 10 requests/minute por IP.

### 5.3 [BAIXO] `normalize_username` permite usernames vazios após strip
- **Localização:** `main.py:197-205`
- **Descrição:** O `BeforeValidator` `normalize_username` faz `value.strip()` e valida caracteres, mas o `Field(min_length=1)` no `Username` type (linha 210) valida o comprimento **antes** do `BeforeValidator` em alguns casos do Pydantic v2. Se o validator strip resultar em string vazia, o `safe_characters.isalnum()` check (linha 203) levanta `ValueError` — então na prática está protegido. Mas a ordem de validação Pydantic v2 pode variar.
- **Impacto:** Baixo. Protegido na prática, mas a defesa em profundidade poderia ser melhor.
- **Sugestão:** Adicionar `if not normalized: raise ValueError("nickname vazio")` após o strip.

### 5.4 [BAIXO] RPC credentials expostas em logs de debug
- **Localização:** `engine.py:53-80`
- **Descrição:** O método `_load_auth_header` lê o cookie do Bitcoin Core e cria um header `Authorization: Basic <base64>`. Se os logs de debug capturarem headers HTTP (httpx pode logar request details), as credenciais RPC seriam expostas. O `logger.debug` na linha 75 loga o caminho do cookie e a exceção, mas não as credenciais — então está parcialmente protegido.
- **Impacto:** Baixo. Risco teórico, não confirmado na prática.
- **Sugestão:** Configurar httpx com `event_hooks` para redactar headers de autenticação nos logs.

### 5.5 [BAIXO] `TrustedHostMiddleware` não aplicado — código existe mas não é usado
- **Localização:** `main.py:23`, `main.py:166-182`, `main.py:186`
- **Description:** O módulo importa `TrustedHostMiddleware` (linha 23) e calcula `trusted_hosts` (linha 186), mas **nunca adiciona o middleware ao app**. O `FastAPI` instance (linha 281-290) não tem `TrustedHostMiddleware`. O comentário na linha 292-293 diz que CORS é tratado no WebSocket handler e nginx, mas `TrustedHostMiddleware` para HTTP REST endpoints não é configurado.
- **Impacto:** Baixo. O header `Host` pode ser spoofed em requisições HTTP, permitindo cache poisoning em proxies.
- **Sugestão:** Adicionar `app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)` após a criação do app.

---

## 6. OBSERVABILIDADE

### 6.1 [MÉDIO] Métricas operacionais não expostas — sem Prometheus/statsd
- **Localização:** Todo o código base
- **Descrição:** Não há métricas expostas para monitoramento. O sistema coleta dados operacionais valiosos (`dropped_transactions`, `queue_depth`, `epoch`, `status`) mas não os expõe como métricas time-series. Sem métricas, é impossível:
  - Alertar sobre taxa de transações descartadas
  - Monitorar latência de processamento
  - Detectar degradação gradual do Redis
  - Medir throughput de eventos WebSocket
- **Impacto:** Médio. Operações em produção sem visibilidade métrica.
- **Sugestão:** Adicionar endpoint `/metrics` com Prometheus client library, ou integrar com statsd/datadog. Métricas essenciais:
  - `mempool_miner_tx_processed_total` (counter)
  - `mempool_miner_tx_dropped_total` (counter)
  - `mempool_miner_queue_depth` (gauge)
  - `mempool_miner_ws_connections` (gauge)
  - `mempool_miner_rpc_latency_seconds` (histogram)

### 6.2 [BAIXO] Logs não estruturados — difícil de agregar em produção
- **Localização:** Todo o código base
- **Descrição:** Os logs usam `logging` padrão com formato `%asctime %levelname %name: %message`. Em produção com múltiplos containers, esses logs são difíceis de agregar, filtrar e correlacionar. Não há `request_id`, `trace_id`, ou campos estruturados como `realm_id`, `node_id` nos logs.
- **Impacto:** Baixo. Dificulta debugging em produção, mas não quebra funcionalidade.
- **Sugestão:** Usar `structlog` ou `python-json-logger` para logs JSON estruturados com campos consistentes.

### 6.3 [BAIXO] Health check não verifica estado dos ingestores
- **Localização:** `main.py:501-510`
- **Descrição:** O health check (`/api/v1/health/live`) faz apenas `redis_client.ping()` e retorna `{"status": "ok"}`. Não verifica se os ingestores estão rodando, se o ZMQ está conectado, ou se o Bitcoin Core RPC está responsivo. Um health check "ok" não garante que o sistema está processando transações.
- **Impacto:** Baixo. O readiness check (linha 514-522) tem o mesmo problema.
- **Sugestão:** O health check já está correto para liveness (apenas verifica Redis). Para readiness, verificar o heartbeat dos ingestores via `node_status_key` — se nenhum heartbeat foi recebido nos últimos 60s, retornar 503.

---

## 7. ANÁLISE ADICIONAL

### 7.1 Race Conditions Identificadas

| # | Localização | Descrição | Status |
|---|-------------|-----------|--------|
| R1 | `ingestor.py:437-455` | TX processada entre RPC e lock pode ter epoch stale | **Mitigado** — segunda validação no lock |
| R2 | `ingestor.py:300-315` | `drain_stale_transactions` com reinsert pode perder itens | **Parcial** — QueueFull na reinsert descarta |
| R3 | `main.py:828-845` | `recent_events` drain/reinsert race | **Não mitigado** |
| R4 | `ingestor.py:535-574` | `handle_block` e `process_transaction` compartilham `epoch_lock` | **Mitigado** — lock serializa |

### 7.2 Memory Leaks Identificados

| # | Localização | Descrição | Severidade |
|---|-------------|-----------|------------|
| M1 | `main.py:784` | `EventRelay.queue` acumula eventos sem consumidores | **Alta** |
| M2 | `main.py:848-854` | `get_relay()` cria relays não rastreados pelo lifespan | **Média** |
| M3 | `ingestor.py:609-610` | `block_counter` sem TTL cresce indefinidamente | **Baixa** |

### 7.3 Pontos Fortes Identificados

1. **Lua scripts atômicos** — todos os commits Redis usam fencing por token (`lease_token`) para garantir que apenas o ingestor com lease ativa pode publicar
2. **Sanitização de eventos** — `sanitize_public_event` filtra campos permitidos por tipo de ação e hash SHA-256 no `event_id`
3. **CORS rigoroso** — `normalize_http_origin` valida esquema, hostname, porta, e rejeita curingas/credenciais
4. **Epoch lock** — serializa `process_transaction`, `handle_block` e `update_status` para evitar TXs de epoch stale
5. **Graceful shutdown** — SIGTERM handler com cancelamento ordenado de tasks
6. **Lease com retry** — `lease_loop` com backoff exponencial evita falhas por instabilidade temporária de rede
7. **Configuração frozen** — `NodeConfig` com `frozen=True, slots=True` previne mutação acidental

---

## 8. PRIORIDADE DE CORREÇÃO

### Immediato (Sprint atual)
1. **Item 1.1 / 3.1** — Corrigir EventRelay para broadcast fan-out (afeta funcionalidade core)
2. **Item 5.1** — Adicionar autenticação ao endpoint de PlayerStateUpdate
3. **Item 4.1** — Corrigir `is_halving_block` para usar block height

### Curto prazo (Próxima sprint)
4. **Item 2.1** — Adicionar pcall no cjson.decode do COMMIT_TRANSACTION_SCRIPT
5. **Item 2.4** — Adicionar TTL ao realm_state_key
6. **Item 3.2** — Adicionar backpressure ao ws_sender
7. **Item 5.2** — Adicionar rate limiting ao leaderboard

### Médio prazo (Backlog)
8. **Item 1.3** — Connection pool com max_connections
9. **Item 6.1** — Métricas Prometheus
10. **Item 6.2** — Logs estruturados
11. **Item 5.5** — Aplicar TrustedHostMiddleware
