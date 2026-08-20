# RELATÓRIO DE AUDITORIA COMPLETA — Mempool Miner

**Data:** 15/08/2026
**Escopo:** Backend Python (9 arquivos, ~2.291 linhas), Frontend JS (1.465 linhas), Docker/CI/CD, Testes
**Método:** 4 agents especializados em paralelo (3 entregaram, 1 parou por timeout)

---

## RESUMO EXECUTIVO

O sistema é **bem arquitetado** com separação clara de responsabilidades, bons padrões de segurança e código limpo. Foram encontrados **3 problemas críticos**, **8 de alta severidade**, **12 de média** e **15 de baixa**. Nenhum problema impede a operação atual, mas alguns representam riscos de confiabilidade e segurança que devem ser tratados.

---

## 1. PROBLEMAS CRÍTICOS

### C1. `fees.base` depreciado no Bitcoin Core v31.1 — taxas sempre zeradas
**Arquivo:** `engine.py:106-109`
**Descrição:** O campo `fees` (com subcampos `base`/`modified`) foi **depreciado no Bitcoin Core v0.21**. A imagem do projeto usa `bitcoin/bitcoin:31.1`. O campo correto é `result.get("fee", 0)` (fee direta em BTC). O código atual lê `fees.get("base", 0)`, que pode retornar 0 em versões futuras, zerando todas as taxas e desabilitando `is_high_fee`.
**Impacto:** **ALTO** — Em versões futuras do Bitcoin Core, `fees` pode ser removido completamente, fazendo o jogo perder toda a mecânica de taxa alta. Mesmo na v31.1 atual, o campo pode estar ausente.
**Correção:** Substituir por `result.get("fee", 0)` diretamente.

### C2. ZMQ: Leitura do terceiro frame é dead code
**Arquivo:** `blockchain.py:46-57`
**Descrição:** O código tenta ler o terceiro frame da mensagem ZMQ como sequência, mas o Bitcoin Core `rawtx` envia apenas 2 frames (topic + body). O terceiro frame só existe em `zmqpubsequence`, que é um publisher diferente. O contador local monotônico é **sempre** usado — a lógica do terceiro frame é dead code que confunde.
**Impacto:** `source.sequence` é sempre um contador local, não a sequência real do Bitcoin Core. Se o sistema depender de sequenciamento real para detecção de gaps ou replay, isso falha silenciosamente.
**Correção:** Remover a lógica de leitura do terceiro frame e documentar que `local_sequence` é o único mecanismo de ordenação.

### C3. Double-await de `run_task` em `ingestor.py:502` — comportamento frágil no shutdown
**Arquivo:** `ingestor.py:502`
**Descrição:** Quando `run_task` completa primeiro (erro interno), o código faz `await run_task` para re-levantar a exceção. Funciona, mas é confuso e frágil: se a lógica de shutdown mudar, o double-await pode levantar `CancelledError` em vez da exceção original. O `finally` já faz `gather` com `return_exceptions=True`, então a limpeza ocorre de qualquer forma.
**Impacto:** Comportamento correto por coincidência; risco de bug silencioso em refatorações futuras.
**Correção:** Remover a linha 502; deixar o `finally` lidar com a limpeza e propagar a exceção explicitamente.

### C4. Race condition entre `process_transaction` e `handle_block`
**Arquivo:** `ingestor.py:271-327`
**Descrição:** O código reconhece o problema (comentário nas linhas 287-289) e mitiga com `epoch_lock`. A verificação `observed_epoch != self.epoch` dentro do lock funciona, mas o padrão é frágil — se alguém mover `event.update()` para antes do lock no futuro, o bug se manifesta.
**Impacto:** Baixo na prática (mitigação funciona), mas risco latente de regressão.
**Correção:** Documentar explicitamente a dependência de ordem. Considerar mover toda a construção do evento para dentro do lock.

### C5. `mempool_count` diverge do valor real do nó durante indisponibilidade RPC
**Arquivo:** `ingestor.py:50-69` (COMMIT_TRANSACTION_SCRIPT)
**Descrição:** Quando o RPC está indisponível, o Lua script faz `INCR` no contador Redis, que nunca decresce quando transações são mineradas. O `handle_block` reseta via `COMMIT_BLOCK_SCRIPT`, mas entre o reset e a próxima reconciliação RPC, o contador pode estar errado.
**Impacto:** `mempool_count` exibido ao cliente pode ser inflado durante períodos de indisponibilidade RPC.
**Correção:** Aceitável para uso recreativo. Documentar como comportamento esperado.

---

## 2. PROBLEMAS DE ALTA SEVERIDADE

### A1. Lease fencing não previne "split-brain" durante rede particionada
**Arquivo:** `ingestor.py:42-103`
**Descrição:** Se o Redis ficar temporariamente indisponível, o `lease_loop` lança `RuntimeError`, o ingestor encerra, mas o lease no Redis ainda existe (TTL continua). Quando o Redis volta, outro ingestor não pode adquirir porque o lease antigo ainda está ativo. Gap de ~30s na publicação de eventos.
**Correção:** Documentar como comportamento esperado. Considerar adicionar lógica de "force acquire" após período de grace.

### A2. `ingestor_healthcheck.py` valida `NODE_ID` com função de `realm_id`
**Arquivo:** `ingestor_healthcheck.py:22`
**Descrição:** `validate_realm_id(os.environ["NODE_ID"])` — semântica errada. Funciona hoje porque os node_ids do catálogo passam no pattern, mas se um node_id futuro usar caracteres fora do pattern, o healthcheck falha falsamente.
**Correção:** Renomear função para `validate_id_format()` ou criar `validate_node_id()`.

### A3. `GameEngine` chama `load_dotenv()` — acoplamento implícito ao filesystem
**Arquivo:** `engine.py:16`
**Descrição:** `load_dotenv()` executado em nível de módulo — efeito colateral na importação. Em produção (Docker), as variáveis já estão injetadas. Em teste, pode carregar credenciais de desenvolvimento acidentalmente.
**Correção:** Remover `load_dotenv()` de `engine.py`. As variáveis vêm do Docker.

### A4. WebSocket sem heartbeat — cliente não detecta ingestor caído
**Arquivo:** `main.py:487-499`
**Descrição:** `ws_sender` apenas repassa eventos do Redis Pub/Sub. Se o ingestor cair e parar de publicar, o WebSocket permanece aberto silenciosamente. O cliente não sabe que o stream parou.
**Correção:** Adicionar heartbeat/ping no WebSocket ou documentar que o frontend deve implementar timeout local.

### A5. `process_interval_seconds` como gargalo de throughput
**Arquivo:** `ingestor.py:340-341`
**Descrição:** O sleep é **por transação**, não por batch. Com o default de 1.0s, o ingestor processa no máximo 1 TX/segundo. Para mainnet (0.25s), são 4 TX/s. O Bitcoin mainnet processa ~2000-7000 TX/s em picos. A fila de 5000 (20000 para mainnet) enche rapidamente, e transações são descartadas.
**Correção:** Processar em batches com sleep entre batches, não entre transações. Ou usar `process_interval_seconds=0` para mainnet e confiar na fila como buffer.

### A6. Estado do jogo controlado pelo cliente
**Arquivo:** `frontend/game.js`
**Descrição:** O frontend calcula pontuação, gerencia saldo fictício, controla rodadas e envia scores auto-declarados ao leaderboard. A API valida apenas o intervalo do score (`0..MAX_SCORE`), não a legitimidade. Qualquer cliente pode enviar `POST /api/v1/networks/{realm}/leaderboard` com score máximo.
**Correção:** (Documentado no ROADMAP.md) Serviço autoritativo de partidas com eventos assinados.

### A7. Sem HA entre ingestores do mesmo realm
**Arquivo:** Arquitetura geral
**Descrição:** A arquitetura suporta apenas um ingestor por realm. Se o ingestor cai, eventos ZMQ são perdidos até o restart. O lease mechanism faz fencing (impede duplicação), mas não failover automático.
**Correção:** (Documentado no ARQUITETURA.md) Múltiplos nós por realm com eleição e deduplicação por TXID.

### A8. `load_dotenv()` no nível de módulo em `engine.py` — acoplamento ao filesystem
**Arquivo:** `engine.py:16`
**Descrição:** `load_dotenv()` executado no escopo do módulo modifica `os.environ` no momento do `import`, antes que `NodeConfig.from_environment()` leia as variáveis do Docker. Se um arquivo `.env` existir acidentalmente na imagem Docker, ele sobrescreve credenciais RPC/ZMQ injetadas pelo docker-compose.
**Correção:** Remover `load_dotenv()` de `engine.py`. O Docker já injeta todas as variáveis necessárias.

### A9. `config.py:169` — KeyError silencioso quando REALM_ID não está no catálogo
**Arquivo:** `config.py:169`
**Descrição:** `NETWORKS_BY_REALM[realm_id]` — se REALM_ID passar na regex mas não estiver no catálogo, levanta `KeyError` em vez de `ValueError` descritivo.
**Correção:** Usar `.get()` com mensagem clara.

### A10. Redis sem autenticação no Docker Compose
**Arquivo:** `docker-compose.yaml:29-48`
**Descrição:** Redis roda sem senha. URL `redis://redis:6379` não inclui credenciais. Em ambiente compartilhado, qualquer contêiner na rede pode ler/escrever no Redis.
**Correção:** Adicionar `--requirepass` e usar `REDIS_PASSWORD` via Docker secrets.

### A11. Senhas RPC em variáveis de ambiente visíveis
**Arquivo:** `docker-compose.yaml`
**Descrição:** Variáveis de ambiente são visíveis via `docker inspect` e em logs. Para um sistema que lida com acesso a nós Bitcoin, isso é sensível.
**Correção:** Usar Docker secrets ou montar arquivos de senha via volume.

### A12. RPC dentro de `epoch_lock` — bloqueia processamento de transações durante heartbeats
**Arquivo:** `ingestor.py:206, 293, 348`
**Descrição:** Chamadas RPC (`get_mempool_size`) são feitas **dentro** de `async with self.epoch_lock`. Enquanto o heartbeat espera pelo RPC, `process_transaction` e `handle_block` ficam bloqueados esperando o lock. Se o RPC estiver lento, transações do ZMQ acumulam na fila e podem ser descartadas (`QueueFull`). O problema ocorre em 3 pontos: `update_status` (L206), `process_transaction` (L293) e `handle_block` (L348).
**Impacto:** **ALTO** — Perda de transações sob carga alta + RPC lento. Serialização total do processamento.
**Correção:** Mover `get_mempool_size()` para fora do lock e passar o valor como parâmetro.

### A13. `LEADERBOARD_KEY` dead code
**Arquivo:** `main.py:49`
**Descrição:** `LEADERBOARD_KEY = leaderboard_key(DEFAULT_REALM_ID)` é definido e nunca referenciado. O código usa `leaderboard_key(definition.realm_id)` dinamicamente em todas as rotas.
**Correção:** Remover a linha 49.

### A14. Log bomb em `ws_sender` — warning para cada evento de outro realm
**Arquivo:** `main.py:497`
**Descrição:** `logger.warning("Evento Redis fora do contrato público foi ignorado")` — em ambiente multi-realm, TODO evento de outro realm gera um warning. Com 3+ realms ativos, ~66% dos eventos geram warnings desnecessários.
**Correção:** Mudar para `logger.debug(...)` com contexto.

---

## 3. PROBLEMAS DE MÉDIA SEVERIDADE

### M1. `BitcoinZMQListener.stop()` só seta flag — não fecha socket
**Arquivo:** `blockchain.py:113-115`
**Descrição:** O socket ZMQ só é fechado no `finally` de `start()`. Se `stop()` for chamado sem que `start()` esteja rodando, o socket e contexto vazam.
**Correção:** Adicionar fechamento condicional em `stop()`.

### M2. `COMMIT_STATUS_SCRIPT` pode ter `mempool_count` stale
**Arquivo:** `ingestor.py:81-94`
**Descrição:** Quando RPC falha, `realm_state_key` recebe snapshot com `mempool_count` desatualizado, enquanto `mempool_count` key separado está correto. A API lê ambos e usa o que existir.
**Correção:** Garantir consistência entre as duas fontes.

### M3. `drain_stale_transactions` não cobre TXs já sendo processadas
**Arquivo:** `ingestor.py:177-186`
**Descrição:** Quando um bloco chega, TXs na fila são descartadas, mas TXs já fora da fila (dentro de `process_transaction`) podem ainda ser publicadas após o drain.
**Correção:** Raro, mas documentar. Uma TX da epoch anterior pode aparecer brevemente.

### M4. `__init__.py` diz "Mempool Search" em vez de "Mempool Miner"
**Arquivo:** `backend/app/__init__.py:1`
**Correção:** Cosmético — atualizar docstring.

### M5. Sem `conftest.py` — nenhuma fixture compartilhada
**Arquivo:** `backend/tests/`
**Descrição:** Sem fixtures de cleanup global, sem configuração centralizada de pytest-asyncio, sem fixtures reutilizáveis. Cada teste cria dependências manualmente.
**Correção:** Criar `conftest.py` com fixtures compartilhadas.

### M6. Estado global em `os.environ.setdefault` nos testes
**Arquivo:** `test_engine.py:8-9`, `test_models.py:13-14`
**Descrição:** Variáveis de ambiente definidas no nível do módulo. Se RPC_USER já estiver definido no CI, o `setdefault` não sobrescreve — o valor do CI vaza.
**Correção:** Usar `monkeypatch.setenv()` em cada teste ou fixture `autouse`.

### M7. `GameEngine` sem cleanup em caso de exceção nos testes
**Arquivo:** `test_engine.py`
**Descrição:** Se `tx_to_word` lançar exceção inesperada, `engine.close()` nunca é chamado e o `httpx.AsyncClient` interno vaza.
**Correção:** Usar `async with` ou `try/finally`.

### M8. `test_full_queue_drops_without_blocking` cria NodeIngestor real
**Arquivo:** `test_multi_network.py:469-485`
**Descrição:** Instancia `BitcoinZMQListener` real e `GameEngine` real. Se o teste falhar, recursos ZMQ e HTTP vazam.
**Correção:** Usar `object.__new__(NodeIngestor)` como outros testes fazem.

### M9. Sem medição de cobertura de código
**Arquivo:** CI workflow
**Descrição:** CI roda `pytest -q` sem `--cov`. Impossível saber quais caminhos estão sem testes.
**Correção:** Adicionar `pytest-cov` com threshold mínimo.

### M10. `BitcoinZMQListener` — zero testes
**Arquivo:** `backend/app/blockchain.py`
**Descrição:** O módulo que conecta ZMQ ao Bitcoin Core não tem nenhum teste. É o componente mais crítico do sistema.
**Correção:** Criar testes unitários com mock de ZMQ.

### M11. `migrate_legacy_default()` — migração sem testes
**Arquivo:** `backend/app/storage.py`
**Descrição:** Scripts Lua executados no Redis para migrar dados legados. Zero testes cobrem idempotência, dados ausentes, etc.
**Correção:** Criar testes de migração.

### M13. `test_old_transaction_cannot_publish_after_new_block` — teste quebrado
**Arquivo:** `test_multi_network.py:223-284`
**Descrição:** O teste faz `redis_client.eval.assert_awaited_once()` após `await ingestor.handle_block(block)`. Porém, `handle_block` chama `eval` **duas vezes**: uma para `COMMIT_BLOCK_SCRIPT` (L368) e outra em `update_status()` (L382). `assert_awaited_once()` deve falhar. Se o teste está passando, há algo que está sendo perdido — possivelmente o teste não está rodando ou foi ignorado.
**Correção:** Verificar se o teste realmente passa. Se sim, investigar por que. Se não, corrigir para `assert_awaited()` com `call_count == 2`.

### M14. 5 testes usam `object.__new__(NodeIngestor)` — frágeis a mudanças
**Arquivo:** `test_multi_network.py:229, 292, 328, 367, 396`
**Descrição:** Bypass de `__init__` cria objetos parcialmente inicializados. Se `NodeIngestor.__init__` adicionar um novo atributo obrigatório, esses testes continuam passando com objetos incompletos — falso positivo.
**Correção:** Criar factory function ou fixture que inicializa o objeto corretamente.

### M15. `NodeConfig` frozen com `object.__setattr__` em `__post_init__` — hack
**Arquivo:** `config.py:126-129`
**Descrição:** `NodeConfig` é `frozen=True`, mas `__post_init__` faz `object.__setattr__(self, "realm_id", normalized_realm)`. Funciona em CPython, mas viola o contrato `frozen`. Se `realm_id` vier já normalizado, o `setattr` é desnecessário; se vier com maiúsculas, o objeto é criado com valor diferente do construtor.
**Correção:** Normalizar `realm_id` antes de passar para o construtor, ou remover `frozen=True`.

### M16. `from_environment` não valida `rpc_host`/`zmq_host`
**Arquivo:** `config.py:163`
**Descrição:** Hosts vazios ou com caracteres inválidos passam silenciosamente. `RPC_HOST=""` gera `rpc_url = "http://:18443"`.
**Correção:** Adicionar validação mínima de host.

### M17. `ingestor_healthcheck.py` — `FileNotFoundError` não tratado
**Arquivo:** `ingestor_healthcheck.py:25`
**Descrição:** Se `/tmp/mempool-miner-ingestor-token` não existe, `read_text()` levanta `FileNotFoundError` que vira um traceback cru. O healthcheck do Docker falha com stack trace em vez de mensagem limpa.
**Correção:** Envolver em `try/except` com mensagem clara.

### M18. `handle_block` não valida se o bloco é realmente novo
**Arquivo:** `ingestor.py:343-346`
**Descrição:** Se o mesmo `hashblock` for recebido duas vezes (edge case do ZMQ), a epoch é redefinida para o mesmo valor, o backlog é drenado novamente (vazio), e um evento `block_mined` redundante é publicado.
**Correção:** Verificar `if notice.block_hash == self.epoch: return` antes de avançar.

### M19. Redis Pub/Sub sem replay — eventos perdidos durante desconexões
**Arquivo:** `main.py:493-499`
**Descrição:** Pub/Sub é fire-and-forget. Se o WebSocket do cliente cai, eventos são perdidos irreversivelmente. O cliente precisa reconectar e esperar novos eventos.
**Correção:** Redis Streams para replay, ou buffer temporário de eventos recentes.

### M20. Backend com `--workers 1` — throughput HTTP limitado
**Arquivo:** `docker-compose.yaml:271`
**Descrição:** O uvicorn roda com um único worker. Correto para WebSocket (que não funciona com múltiplos workers no FastAPI), mas limita o throughput HTTP a uma thread. Em picos de tráfego, healthchecks e leaderboard podem atrasar.
**Correção:** Separar WebSocket em serviço dedicado ou usar WebSockets com múltiplos workers via Redis Pub/Sub.

---

## 4. PROBLEMAS DE BAIXA SEVERIDADE

### B1. `engine.py:107` — Dead code inatingível
`fees.get("base", 0) if isinstance(fees, dict) else 0` — `fees` é sempre dict. Simplificar.

### B2. `engine.py:33-37` — Atributos redundantes
`self.rpc_user`, `self.rpc_password`, etc. duplicam dados de `self.config`. Remover.

### B3. `game.js:1248` — `event.key === 'Spacebar'` nunca é válido
Tecla espaço retorna `' '`. Ramo inatingível.

### B4. `game.js:1076` — Truncamento de palavras BIP39
Se palavra for truncada, o word bank mostra a palavra completa mas a grade tem a versão truncada.

### B5. `game.js:393` — `teardownSession()` não limpa `catalogRetryTimeout`
Ponta solta cosmética.

### B6. `config.py:146` — `process_interval_seconds < 0` permite zero — busy-loop
**Arquivo:** `config.py:146`
**Descrição:** A validação é `< 0`, então `0` passa. Em `ingestor.py:340-341`, `process_interval_seconds > 0` controla o sleep. Se for `0`, o loop de processamento vira um busy-loop sem sleep. **Impacto:** CPU 100% em produção.
**Correção:** Mudar para `<= 0` ou validar `> 0` explicitamente.

### B7. `storage.py:67` — `validate_realm_id(node_id)` — nome enganoso
Renomear para `validate_id_format()`.

### B8. `healthcheck.py:22` — `os.environ["NODE_ID"]` levanta KeyError
Usar `os.environ.get()` com verificação explícita.

### B9. `main.py:83` — `block_mined` expõe frozenset vazio
Decidir se `block_hash` deve ser exposto no evento público.

### B10. Legacy endpoints sem data de remoção
Adicionar `Sunset` header.

### B11. `MAX_SCORE = INT32_MAX` — limite arbitrário
Documentar a razão.

### B12. `redis_client` global em `main.py` — não testável sem mock
Considerar injeção de dependência.

### B13. `game.js:112` — `hardwarePrices[0] = 0` nunca acessado
Índice 0 é dead code.

### B14. `game.js:1397` — `setTimeout` direto em vez de `scheduleForSession()`
Usar `scheduleForSession()` para consistência.

### B15. `storage.py:75-88` — Dados legados nunca removidos após migração
Documentar explicitamente ou adicionar flag de cleanup.

---

## 5. PONTOS FORTES IDENTIFICADOS

1. **Lease-based fencing com Lua scripts atômicos** — implementação robusta com token verification
2. **Namespace isolation por realm** — todas as chaves Redis incluem `realm_id`
3. **Event sanitization** — campos privados filtrados antes do WebSocket
4. **Graceful shutdown** — SIGTERM → cancelamento ordenado → release de lease → cleanup
5. **Multi-rede consistente** — catálogo estático, validação cruzada realm↔network↔node_id
6. **Segurança** — CORS restrito, TrustedHost, CSP headers, sem credenciais em defaults
7. **Dedupe por epoch** — `SEEN:{epoch}` com TTL de 3600s previne duplicatas
8. **Migração legada** — scripts Lua idempotentes para v1→v2
9. **Docker** — `no-new-privileges`, redes internas, resource limits, healthchecks
10. **Frontend** — Acessibilidade (ARIA, trap de foco, skip-link), PWA completa, gerenciamento de memória

---

## 6. ROADMAP DE CORREÇÃO

### Fase 1 — Crítico (prioridade imediata)
| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 1 | Remover dead code do terceiro frame ZMQ em `blockchain.py` | 15min | Alto |
| 2 | Remover `load_dotenv()` de `engine.py` | 5min | Médio |
| 3 | Corrigir `config.py:169` — usar `.get()` com mensagem clara | 10min | Médio |
| 4 | Adicionar heartbeat/ping no WebSocket OU documentar timeout no frontend | 30min | Alto |
| 5 | Adicionar autenticação ao Redis no Docker Compose | 30min | Alto |

### Fase 2 — Alto (próxima sprint)
| # | Ação | Esforço | Impacto |
|---|---|---|---------|
| 6 | Documentar race condition em `process_transaction`/`handle_block` | 15min | Médio |
| 7 | Renomear `validate_realm_id()` para `validate_id_format()` | 15min | Baixo |
| 8 | Reduzir `TX_PROCESS_INTERVAL_SECONDS` para signet | 5min | Médio |
| 9 | Adicionar Docker secrets para senhas RPC | 1h | Alto |
| 10 | Criar `conftest.py` com fixtures compartilhadas | 30min | Alto |

### Fase 3 — Médio (melhoria contínua)
| # | Ação | Esforço | Impacto |
|---|---|---|---------|
| 11 | Adicionar `pytest-cov` ao CI com threshold mínimo | 30min | Alto |
| 12 | Criar testes para `BitcoinZMQListener` | 1h | Alto |
| 13 | Criar testes para `migrate_legacy_default()` | 30min | Médio |
| 14 | Completar testes de `ingestor_healthcheck.py` | 30min | Médio |
| 15 | Corrigir `test_full_queue_drops_without_blocking` (usar `object.__new__`) | 15min | Médio |
| 16 | Adicionar `.dockerignore` ao backend | 10min | Baixo |
| 17 | Corrigir docstring em `__init__.py` | 2min | Baixo |
| 18 | Corrigir `event.key === 'Spacebar'` no frontend | 5min | Baixo |

### Fase 4 — Baixo (cosmético / técnico)
| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 19 | Limpar atributos redundantes em `GameEngine` | 15min | Baixo |
| 20 | Simplificar `engine.py:107` (dead code) | 5min | Baixo |
| 21 | Adicionar `Sunset` header nos endpoints legados | 10min | Baixo |
| 22 | Documentar `MAX_SCORE = INT32_MAX` | 5min | Baixo |
| 23 | Limpar `hardwarePrices[0]` no frontend | 5min | Baixo |
| 24 | Usar `scheduleForSession()` em `game.js:1397` | 5min | Baixo |
| 25 | Adicionar `clearTimeout(catalogRetryTimeout)` em `teardownSession()` | 5min | Baixo |

---

## 7. METRICAS

| Métrica | Valor |
|---------|-------|
| Linhas de código auditadas | ~3.756 (backend + frontend + Docker) |
| Problemas encontrados | 50 |
| Críticos | 5 |
| Alta severidade | 14 |
| Média severidade | 20 |
| Baixa severidade | 15 |
| Arquivos limpos (zero problemas) | 3 (events.py, index.html, service-worker.js) |
| Cobertura de testes estimada | ~40% (sem medição real) |
| Tempo estimado para Fase 1 | ~2h |
| Tempo estimado para todas as fases | ~8h |
