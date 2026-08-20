# 🔍 Relatório de Varredura de Logs — Mempool Miner

**Data:** 19 de Agosto de 2026  
**Horário da varredura:** ~15:30 UTC  
**Escopo:** 7 containers (500 linhas cada, com busca ampliada quando necessário)

---

## Resumo Executivo

| Container | Status | Erros Críticos | Erros Moderados | Avisos |
|-----------|--------|----------------|-----------------|--------|
| `mempool-miner-frontend-1` | ⚠️ 1 erro transitório | 1 (502) | 0 | 0 |
| `mempool-miner-backend-1` | ✅ Limpo | 0 | 0 | 0 |
| `mempool-miner-redis-1` | ⚠️ 4 avisos de configuração | 0 | 0 | 4 |
| `mempool-miner-ingestor-regtest-1` | ⚠️ 1 aviso operacional | 0 | 0 | 1 |
| `mempool-miner-ingestor-signet-1` | 🔴 141 erros contínuos | 141 | 0 | 0 |
| `mempool-miner-bitcoin-regtest-1` | ⚠️ 33 avisos | 0 | 0 | 33 |
| `mempool-miner-bitcoin-signet-1` | ⚠️ 4 avisos + falhas de importação | 0 | 89 tx falhadas | 4 |

**Total de erros encontrados:** 143 erros + 47 avisos + 89 transações falhadas

---

## ERRO #1 — 502 Bad Gateway (Frontend → Backend)

- **Container:** `mempool-miner-frontend-1` (nginx)
- **Timestamp:** `2026/08/19 15:20:11`
- **Frequência:** 1 ocorrência (transitório)
- **Mensagem completa:**
  ```
  172.21.0.1 - - [19/Aug/2026:15:20:11 +0000] "GET /api/v1/networks HTTP/1.1" 502 552
  2026/08/19 15:20:11 [error] 23#23: *186 connect() failed (111: Connection refused) while connecting to upstream, client: 172.21.0.1, server: _, request: "GET /api/v1/networks HTTP/1.1", upstream: "http://172.21.0.2:8000/api/v1/networks", host: "localhost:8010"
  ```
- **Impacto:** **Médio** — O frontend não conseguiu conectar ao backend momentaneamente. A requisição do navegador recebeu 502.
- **Causa:** O backend estava reiniciando naquele momento (os logs do backend mostram startup às 15:28:45, indicando que houve um restart entre 15:20 e 15:28).
- **Correção recomendada:**
  - Adicionar `max_fails=3` e `fail_timeout=30s` no upstream do nginx para tolerância a falhas
  - Configurar health check no docker-compose para evitar que o nginx envie tráfego para um backend reiniciando
  - Adicionar retry no nginx: `proxy_next_upstream error timeout http_502;`

---

## ERRO #2 — Bitcoin RPC 500 no Ingestor Signet (CRÍTICO)

- **Container:** `mempool-miner-ingestor-signet-1`
- **Timestamp:** Contínuo, de `15:26:37` até `15:30:51` (e provavelmente além)
- **Frequência:** **141 ocorrências** nos últimos 500 logs (~a cada 0.5 segundos)
- **Mensagem completa:**
  ```
  2026-08-19 15:26:37,959 WARNING app.engine: Falha na chamada Bitcoin RPC getmempoolentry: Server error '500 Internal Server Error' for url 'http://bitcoin-signet:38332'
  For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/HTTP/Status/500
  ```
- **Impacto:** **Alto** — O ingestor signet não consegue consultar `getmempoolentry` para NENHUMA transação do mempool. Isso significa que:
  - Transações do mempool signet não estão sendo rastreadas
  - Dados de mineração signet estão incompletos/obsoletos
  - O jogo não pode processar transações signet corretamente
- **Causa provável:** O nó Bitcoin signet está retornando 500 para `getmempoolentry`. Possíveis causas:
  1. O nó signet ainda está sincronizando (IBD — Initial Block Download)
  2. O mempool do nó signet está sobrecarregado
  3. A versão do Bitcoin Core não suporta `getmempoolentry` para certas transações
  4. O nó signet está com problemas de recursos (CPU/memória)
- **Correção recomendada:**
  1. Verificar se o nó signet está sincronizado: `docker exec mempool-miner-bitcoin-signet-1 bitcoin-cli -signet getblockchaininfo`
  2. Verificar o tamanho do mempool: `docker exec mempool-miner-bitcoin-signet-1 bitcoin-cli -signet getmempoolinfo`
  3. Testar manualmente: `docker exec mempool-miner-bitcoin-signet-1 bitcoin-cli -signet getmempoolentry <txid>`
  4. Se o nó estiver em IBD, aguardar a sincronização completar
  5. Adicionar retry com backoff exponencial no ingestor para não spammear o RPC

---

## AVISO #1 — Redis: Memory Overcommit Desabilitado

- **Container:** `mempool-miner-redis-1`
- **Timestamp:** Aparece em cada restart (4 ocorrências nos logs)
- **Frequência:** 4 (uma por cada reinicialização do container)
- **Mensagem completa:**
  ```
  # WARNING Memory overcommit must be enabled! Without it, a background save or replication may fail under low memory condition.
  ```
- **Impacto:** **Baixo** — Em ambiente Docker com memória suficiente, não é um problema prático. Pode causar falhas em cenários de baixa memória.
- **Correção recomendada:**
  - Adicionar `sysctl vm.overcommit_memory=1` no host ou no docker-compose
  - Ou ignorar se a memória do host for suficiente

---

## AVISO #2 — Ingestor Regtest: Nó em IBD

- **Container:** `mempool-miner-ingestor-regtest-1`
- **Timestamp:** `2026-08-19 15:20:16,391`
- **Frequência:** 1 (apenas no startup)
- **Mensagem completa:**
  ```
  WARNING app.engine: Nó regtest-local em IBD (progresso=0.0%) — aguardando sync
  ```
- **Impacto:** **Baixo** — Comportamento esperado. Regtest começa sem blocos e precisa de sincronização.
- **Correção recomendada:**
  - Gerar blocos no regtest para progresso: `docker exec mempool-miner-bitcoin-regtest-1 bitcoin-cli -regtest generatetoaddress 101 <address>`
  - Ou ignorar — é comportamento normal de regtest

---

## AVISO #3 — Bitcoin Regtest: Stale Tip (31 ocorrências)

- **Container:** `mempool-miner-bitcoin-regtest-1`
- **Timestamp:** De `03:11:27` até `15:22:33` (a cada ~10 minutos)
- **Frequência:** 31 ocorrências
- **Mensagem completa:**
  ```
  Potential stale tip detected, will try using extra outbound peer (last tip update: 1890 seconds ago)
  ```
- **Impacto:** **Baixo** — Regtest não tem peers externos (é uma rede local isolada). Sem mineração ativa, o tip fica estagnado.
- **Correção recomendada:**
  - Gerar blocos periodicamente no regtest para manter a cadeia ativa
  - Ou ignorar — é comportamento esperado em regtest sem mineração

---

## AVISO #4 — Bitcoin Regtest: RPC Security Warnings

- **Container:** `mempool-miner-bitcoin-regtest-1`
- **Timestamp:** Em cada startup (6 ocorrências)
- **Frequência:** 6
- **Mensagem completa:**
  ```
  [warning] The RPC server is not safe to expose to untrusted networks such as the public internet
  [warning] The use of rpcuser/rpcpassword is less secure, because credentials are configured in plain text.
  ```
- **Impacto:** **Baixo** — Avisos de segurança padrão do Bitcoin Core. Em ambiente Docker isolado, não é crítico.
- **Correção recomendada:**
  - Migrar para `rpcauth` (hashed credentials) ou cookie-based auth
  - Ou ignorar em ambiente de desenvolvimento

---

## AVISO #5 — Bitcoin Signet: RPC Security Warnings

- **Container:** `mempool-miner-bitcoin-signet-1`
- **Timestamp:** `2026-08-19T13:47:18Z`
- **Frequência:** 2
- **Mensagem completa:**
  ```
  [warning] The RPC server is not safe to expose to untrusted networks such as the public internet
  [warning] The use of rpcuser/rpcpassword is less secure...
  ```
- **Impacto:** **Baixo** — Mesmo que acima.
- **Correção recomendada:** Idem ao AVISO #4.

---

## AVISO #6 — Bitcoin Signet: Transações Falhadas na Importação

- **Container:** `mempool-miner-bitcoin-signet-1`
- **Timestamp:** `2026-08-19T02:39:55Z` e `2026-08-19T13:47:53Z`
- **Frequência:** 2 eventos de importação
- **Mensagem completa:**
  ```
  Imported mempool transactions from file: 1580 succeeded, 3 failed, 0 expired, 0 already there, 0 waiting for initial broadcast
  Imported mempool transactions from file: 1285 succeeded, 86 failed, 0 expired, 0 already there, 0 waiting for initial broadcast
  ```
- **Impacto:** **Médio** — 89 transações falharam na importação do mempool persistente. Isso pode indicar:
  - Transações orfãs (dependem de outras transações não no mempool)
  - Transações expiradas ou duplicadas
  - Problemas de consistência do mempool
- **Correção recomendada:**
  - Verificar se as transações falhadas são orfãs
  - Limpar o mempool persistente e deixar o nó reconstruir: `docker exec mempool-miner-bitcoin-signet-1 bitcoin-cli -signet clearmempool`

---

## Análise de Conectividade entre Containers

| Conexão | Status | Detalhes |
|---------|--------|----------|
| Frontend → Backend | ✅ Funcionando (com 1 falha transitória) | Nginx proxy para `172.21.0.2:8000` |
| Backend → Redis | ✅ Funcionando | Sem erros de conexão nos logs |
| Ingestor-regtest → Bitcoin-regtest | ✅ Funcionando | RPC 200 OK em todas as chamadas |
| Ingestor-signet → Bitcoin-signet | 🔴 Falhando | RPC retorna 500 para `getmempoolentry` |
| Backend → WebSocket | ✅ Sem erros | Nenhum erro de WebSocket detectado |

---

## Análise de WebSocket

- **Status:** ✅ Nenhum erro de WebSocket encontrado em nenhum container
- O frontend não reporta erros de conexão WebSocket nos logs do nginx

---

## Análise de Redis

- **Status:** ✅ Funcionando normalmente
- Sem erros de conexão, chave não encontrada, ou timeout
- Apenas o aviso de `memory overcommit` (baixo impacto)
- Saves em background funcionando corretamente

---

## Análise de Bitcoin RPC

| Nó | Status | Detalhes |
|----|--------|----------|
| Regtest | ✅ Funcionando | Todas as chamadas RPC retornam 200 OK |
| Signet | 🔴 Problema | `getmempoolentry` retorna 500 Internal Server Error |

---

## Conclusão

**O erro mais crítico é o ERRO #2** — o ingestor signet não consegue consultar `getmempoolentry` no nó Bitcoin signet. Isso afeta diretamente a funcionalidade do sistema para a rede signet.

**O erro do 502 no frontend (ERRO #1)** foi transitório e ocorreu durante um restart do backend. Não é a causa do travamento na tela de login.

**O backend está saudável** — sem erros nos logs, respondendo corretamente para `/api/v1/networks` e `/api/v1/health/live`.

**A causa do travamento na tela de login provavelmente NÃO está nos logs dos containers** — o backend está funcionando e o frontend consegue se comunicar com ele. O problema pode estar:
1. No código JavaScript do frontend (erros no console do navegador)
2. Em endpoints de autenticação que não estão sendo chamados
3. Em problemas de CORS ou cookies
4. Em erros do console do navegador (não visíveis nos logs do nginx)
