# RELATÓRIO DE AUDITORIA — BACKEND MEMPOOL MINER
# Gerado: 2026-08-16
# Arquivos auditados: main.py (4594 linhas), engine.py (421), ingestor.py (910), storage.py (302), events.py (100)
# Módulos auxiliares: config.py (214), global_events.py (386)

================================================================================
RESUMO EXECUTIVO
================================================================================

Total de problemas encontrados: 31
  - CRÍTICOS: 8
  - MÉDIOS: 14
  - BAIXOS: 9

Categorias mais afetadas:
  1. Assinatura de função incompatível (card_detail_key) — 3 ocorrências
  2. Dados de eventos globais nunca persistidos — 1 bug de lógica
  3. Serialização incorreta de eventos Pub/Sub — 1 bug
  4. Endpoints sem rate limiting — 10 endpoints
  5. Operações financeiras sem logging — 8 ocorrências

================================================================================
1. ERROS DE IMPORTAÇÃO
================================================================================

[1.1] CRÍTICO — card_detail_key chamada com 3 argumentos, definida com 2
  Arquivo: storage.py:160 / main.py:936,940 / ingestor.py:707
  Tipo: Assinatura de função incompatível
  Descrição: card_detail_key(realm_id, card_id) aceita 2 parâmetros, mas é
    chamada com 3 argumentos em 3 locais:
    - main.py:936  → card_detail_key(realm_id, username, bh)
    - main.py:940  → card_detail_key(realm_id, "global", bh)
    - ingestor.py:707 → card_detail_key(self.config.realm_id, "global", block_hash)
  Impacto: CRÍTICO — TypeError em tempo de execução ao gerar/consultar cards
  Sugestão: Adicionar parâmetro ao storage.py:
    def card_detail_key(realm_id: str, owner: str, card_id: str) -> str:
      return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:card:{owner}:{card_id}"

[1.2] BAIXO — Importação não utilizada: field (dataclasses)
  Arquivo: global_events.py:20
  Tipo: Importação não utilizada
  Descrição: `field` é importado de dataclasses mas nunca usado
  Impacto: BAIXO — apenas ruído no código
  Sugestão: Remover `field` da importação

[1.3] BAIXO — Importação não utilizada: event_envelope
  Arquivo: global_events.py:27
  Tipo: Importação não utilizada
  Descrição: `event_envelope` é importado de app.events mas nunca chamado
  Impacto: BAIXO — apenas ruído no código
  Sugestão: Remover da importação

[1.4] MÉDIO — Funções em storage.py não importadas por nenhum módulo
  Arquivo: storage.py:116,133,109
  Tipo: Funções definidas mas nunca usadas
  Descrição:
    - daily_reward_key() (linha 116) — não importada por main.py nem ingestor.py
    - sprint_leaderboard_key() (linha 133) — não importada por nenhum módulo
    - streak_key() (linha 109) — não importada por nenhum módulo
  Impacto: MÉDIO — código morto ou funcionalidade implementada mas não integrada
  Sugestão: Implementar os endpoints correspondentes ou remover as funções

================================================================================
2. ENDPOINTS DUPLICADOS
================================================================================

[2.1] MÉDIO — healthcheck com dois decorators @app.get
  Arquivo: main.py:597-598
  Tipo: Endpoint duplicado no mesmo handler
  Descrição: A função healthcheck() tem dois decorators:
    @app.get("/api/health", ...)
    @app.get("/api/v1/health/live", ...)
    Ambos apontam para a mesma função. Funciona, mas é anti-pattern.
  Impacto: MÉDIO — se a lógica divergir no futuro, um dos endpoints ficará desatualizado
  Sugestão: Separar em duas funções ou usar um redirect 301 de /api/health para /api/v1/health/live

[2.2] BAIXO — decoder_start usa @app.get com corpo de requisição
  Arquivo: main.py:4439-4440
  Tipo: Anti-pattern HTTP
  Descrição: Endpoint GET aceita DecoderStart (BaseModel) como corpo, o que
    viola a semântica HTTP. GET não deve ter body.
  Impacto: BAIXO — alguns proxies/clientes rejeitam GET com body
  Sugestão: Mudar para @app.post ou mover `username` para query parameter/path

================================================================================
3. FUNÇÕES NÃO USADAS
================================================================================

[3.1] MÉDIO — publish_event_status nunca chamada pelo scheduler
  Arquivo: global_events.py:378
  Tipo: Função declarada mas nunca chamada
  Descrição: publish_event_status() grava o status do evento no Redis para
    que get_active_event() possa consultá-lo. Porém, o scheduler (_trigger_event)
    nunca chama publish_event_status(), apenas _publish_event().
  Impacto: MÉDIO — get_active_event() sempre retorna None, então o endpoint
    /global-events nunca mostra eventos ativos
  Sugestão: Chamar publish_event_status() dentro de _trigger_event() após cada
    _publish_event(), ou remover get_active_event() e usar abordagem diferente

[3.2] BAIXO — Funções em storage.py sem consumidores (ver [1.4])
  Ver item [1.4] acima.

================================================================================
4. VARIÁVEIS NÃO INICIALIZADAS
================================================================================

[4.1] BAIXO — _event_relays acessado dentro do generator lifespan
  Arquivo: main.py:345,373,375
  Tipo: Variável de módulo usada dentro de generator
  Descrição: _event_relays é definido no módulo (linha 1771) mas só é
    populado dentro de lifespan(). Se lifespan() falhar antes de popular,
    o dicionário estará vazio. O finally block limpa corretamente.
  Impacto: BAIXO — comportamento correto, mas acoplamento implícito
  Sugestão: Documentar que _event_relays é gerenciado exclusivamente por lifespan()

================================================================================
5. REDIS KEYS INCONSISTENTES
================================================================================

[5.1] CRÍTICO — card_detail_key com assinatura errada gera keys inconsistentes
  Arquivo: storage.py:160 / main.py:936,940 / ingestor.py:707
  Tipo: Key Redis inconsistente
  Descrição: Como card_detail_key aceita 2 args mas recebe 3, a key gerada
    será diferente da esperada. Cards gerados pelo ingestor não serão
    encontrados pelo endpoint de consulta.
  Impacto: CRÍTICO — sistema de Block Cards completamente quebrado
  Sugestão: Corrigir assinatura da função (ver [1.1])

[5.2] MÉDIO — global_event_status key nunca populada
  Arquivo: global_events.py:351,384
  Tipo: Key Redis referenciada mas nunca escrita
  Descrição: get_active_event() lê de mempool_miner:v2:{realm}:global_event_status
    mas o scheduler nunca escreve nessa key. publish_event_status() existe
    mas nunca é chamada.
  Impacto: MÉDIO — endpoint /global-events retorna sempre active_event: null
  Sugestão: Chamar publish_event_status() no scheduler (ver [3.1])

[5.3] MÉDIO — BIP39_WORDLIST com duplicatas
  Arquivo: main.py:4416-4418
  Tipo: Dados inconsistentes
  Descrição: As palavras 'duende', 'dublador', 'dublar', 'duela' aparecem
    múltiplas vezes na lista (3-4 vezes cada), viésando a probabilidade
    do mini-game Decoder.
  Impacto: MÉDIO — palavras duplicadas alteram as chances de sorteio
  Sugestão: Remover duplicatas: set(BIP39_WORDLIST) ou limpar manualmente

================================================================================
6. ASYNC/AWAIT
================================================================================

[6.1] OK — Nenhuma chamada async sem await detectada
  Descrição: Todas as chamadas a redis_client, get_*, _* possuem await
    correto. O código é consistente nesse aspecto.

================================================================================
7. ERROR HANDLING
================================================================================

[7.1] MÉDIO — Endpoints que modificam saldo sem try/except
  Arquivo: main.py — múltiplos endpoints
  Tipo: Error handling ausente em operações financeiras
  Descrição: Os seguintes endpoints modificam saldo (balance) sem try/except:
    - submit_score() :816
    - update_player_state() :880
    - open_crate() :1111
    - claim_free_crates() :1244
    - stake_sats() :1335
    - unstake_sats() :1422
    - spend_energy() :1827
    - buy_energy() :1879
    - decoder_submit() :2126
  Impacto: MÉDIO — falha Redis durante operação financeira pode deixar
    saldo inconsistente (debitado mas não creditado, ou vice-versa)
  Sugestão: Envolver operações de saldo em try/except com rollback,
    ou usar scripts Lua atômicos para operações multi-key

[7.2] MÉDIO — _end_pvp_match transfere saldo sem atomicidade
  Arquivo: main.py:2998-2999
  Tipo: Race condition em transferência de saldo PvP
  Descrição: Duas chamadas hincrby separadas (debita perdedor, credita
    vencedor) não são atômicas. Se o servidor cair entre as duas, o saldo
    fica inconsistente.
  Impacto: MÉDIO — perda ou duplicação de saldo em PvP
  Sugestão: Usar pipeline transacional ou script Lua para transferência atômica

[7.3] MÉDIO — buy_from_market tem race condition pop-then-check
  Arquivo: main.py:2565-2596
  Tipo: Race condition em operação de mercado
  Descrição: zpopmin remove o listing, depois verifica saldo do comprador.
    Se o saldo for insuficiente, o listing é devolvido com zadd — mas entre
    pop e push, outro comprador pode ter pegado o próximo item.
  Impacto: MÉDIO — listings podem ser perdidos ou duplicados no mercado
  Sugestão: Usar script Lua atômico para pop+verificar+transferir

================================================================================
8. VALIDAÇÃO DE INPUT
================================================================================

[8.1] MÉDIO — Username em path não validado por Pydantic
  Arquivo: main.py — múltiplos endpoints
  Tipo: Validação de input ausente
  Descrição: Os seguintes endpoints recebem `username` como path parameter
    (str) sem validação Pydantic:
    - get_player_state() :841
    - update_player_state() :880
    - get_player_cards() :981
    - get_friends() :1740
    - get_staking_status() :1508
    - get_staking_history() :1559
    - get_energy_status() :1740
    - spend_energy() :1827
    - buy_energy() :1879
  Impacto: MÉDIO — usernames com caracteres especiais podem causar
    problemas nas keys Redis ou injeção
  Sugestão: Adicionar validação de username nos handlers ou usar
    BeforeValidator no path parameter

[8.2] MÉDIO — claim_mission_reward sem validação de mission_id
  Arquivo: main.py:1370
  Tipo: Validação de input ausente
  Descrição: mission_id vem do path como str sem validação. Se o cliente
    enviar um mission_id malicioso, o endpoint tenta buscar em rewards dict
    e retorna 404, mas não valida o formato.
  Impacto: MÉDIO — baixo risco prático, mas inconsistente com outros endpoints
  Sugestão: Validar mission_id contra lista conhecida de missões

[8.3] BAIXO — CrateClaimRequest.blocks_mined sem validação
  Arquivo: main.py:3618
  Tipo: Validação de input ausente
  Descrição: blocks_mined é int sem ge=0, permitindo valores negativos
    que poderiam gerar crates_earned > 0 com cálculo de overflow.
  Impacto: BAIXO — requer intencionalidade do atacante
  Sugestão: Adicionar Field(ge=0) a blocks_mined

================================================================================
9. RATE LIMITING
================================================================================

[9.1] MÉDIO — 10 endpoints POST sem rate limiting
  Arquivo: main.py — múltiplos endpoints
  Tipo: Proteção contra abuso ausente
  Descrição: Os seguintes endpoints POST não possuem rate limiting:
    - submit_score_v1() :789
    - submit_score() :816
    - update_player_state() :880
    - stake_sats() :1335
    - unstake_sats() :1422
    - add_friend() :1648
    - remove_friend() :1683
    - spend_energy() :1827
    - buy_energy() :1879
    - decoder_submit() :2126
  Impacto: MÉDIO — um cliente malicioso pode spammar esses endpoints,
    causando carga excessiva no Redis e manipulação de dados
  Sugestão: Implementar middleware de rate limiting (ex: slowapi) ou
    usar Redis para tracking de requisições por IP/username

[9.2] OK — Chat possui rate limiting
  Arquivo: main.py:2189-2204
  Descrição: _check_chat_rate limita a 5 mensagens/minuto por jogador.
    Implementação correta com Redis counter + TTL.

================================================================================
10. LOGGING
================================================================================

[10.1] MÉDIO — 8 operações de saldo sem logging
  Arquivo: main.py — múltiplas linhas
  Tipo: Logging ausente em operações críticas
  Descrição: As seguintes operações de saldo não possuem logging:
    - main.py:1145 — hincrby free_crates
    - main.py:1152 — hset balance (open_crate debit)
    - main.py:1162 — hset balance (open_crate sats credit)
    - main.py:1388 — hset balance (stake debit)
    - main.py:1461 — hset balance (unstake credit)
    - main.py:1533 — hset balance (staking auto-return)
    - main.py:1908 — hset balance (buy_energy debit)
    - main.py:1937 — hset balance (buy_energy revert)
  Impacto: MÉDIO — sem logs, é impossível auditar transações financeiras
    ou investigar discrepâncias de saldo
  Sugestão: Adicionar logger.info() com username, operação, valor antes/depois

[10.2] BAIXO — _roll_crate_item sem logging do resultado
  Arquivo: main.py:3406
  Tipo: Logging ausente
  Descrição: A função que determina o drop da crate não loga o item
    sorteado, dificultando debug de distribuição de probabilidades.
  Impacto: BAIXO — útil apenas para debug
  Sugestão: Adicionar logger.debug() com o item sorteado

================================================================================
11. PROBLEMAS ADICIONAIS
================================================================================

[11.1] CRÍTICO — _publish_event usa str() em vez de json.dumps()
  Arquivo: global_events.py:331
  Tipo: Serialização incorreta
  Descrição: await self.redis_client.publish(channel, str(payload)) converte
    um dict Python com str(), produzindo formato Python (aspas simples,
    True/False maiúsculos) em vez de JSON. O cliente WebSocket que faz
    json.loads() vai falhar.
  Impacto: CRÍTICO — eventos globais não são recebidos pelos clientes
  Sugestão: Usar json.dumps(payload, separators=(",", ":")) como feito
    em todo o resto do código

[11.2] MÉDIO — SCAN operations em PvP (race condition)
  Arquivo: main.py:2882,3168
  Tipo: Race condition
  Descrição: _update_pvp_score e accept_challenge usam SCAN para encontrar
    matches PvP. Entre o SCAN e a operação, outro request pode modificar
    o estado.
  Impacto: MÉDIO — em alta concorrência, updates podem ser perdidos
    ou aplicados ao match errado
  Sugestão: Passar challenger/challenged no payload para construir a key
    diretamente, evitando SCAN

[11.3] MÉDIO — datetime.datetime vs datetime
  Arquivo: main.py — 9 ocorrências (linhas 1179,1362,1392,1470,1510,1624,1782,1845,1913)
  Tipo: Inconsistência de estilo
  Descrição: O código importa `import datetime` mas usa `datetime.datetime.now()`
    em vez de `datetime.now()`. Funciona, mas é redundante.
  Impacto: MÉDIO — apenas estilo, mas consistente com o resto do códigobase
    que usa datetime.now(UTC)
  Sugestão: Padronizar para datetime.now(datetime.timezone.utc)

[11.4] BAIXO — random import dentro de funções
  Arquivo: main.py:3101, ingestor.py:731
  Tipo: Importação dentro de função
  Descrição: `import random` é feito dentro de challenge_player() e
    _determine_card_rarity() ao invés de no topo do módulo.
  Impacto: BAIXO — funciona, mas anti-pattern Python
  Sugestão: Mover para imports no topo do arquivo

[11.5] BAIXO — import time dentro de função
  Arquivo: main.py:4456
  Tipo: Importação dentro de função
  Descrição: `import time` é feito dentro de decoder_start()
  Impacto: BAIXO — funciona, mas anti-pattern
  Sugestão: Mover para imports no topo

[11.6] MÉDIO — Energy buy pode ter race condition
  Arquivo: main.py:1879-1937
  Tipo: Race condition em compra de energia
  Descrição: buy_energy() lê saldo, debita, depois lê energia e adiciona.
    Se duas requisições chegarem simultaneamente, ambas podem debitar o
    saldo mas apenas uma creditar a energia corretamente.
  Impacto: MÉDIO — saldo pode ser debitado sem energia creditada
  Sugestão: Usar script Lua atômico para verificar+debitar+adicionar

[11.7] CRÍTICO — Staking balance pode ficar negativo
  Arquivo: main.py:2998-2999
  Tipo: Underflow de saldo
  Descrição: hincrby com valor negativo não verifica se o saldo é suficiente.
    Se o perdedor do PvP tem saldo 0, o hincrby deixa o saldo negativo.
  Impacto: CRÍTICO — saldo negativo quebra toda a economia do jogo
  Sugestão: Verificar saldo antes de debitar, ou usar script Lua com
    verificação de saldo mínimo

[11.8] MÉDIO — PvP score update usa SCAN global
  Arquivo: main.py:2876-2915
  Tipo: Performance + race condition
  Descrição: _update_pvp_score faz SCAN em todas as keys do Redis com
    pattern `*:pvp:*` para encontrar o match do jogador. Em realms com
    muitos matches, isso é lento e pode encontrar matches de outros realms.
  Impacto: MÉDIO — performance degradada + risco de match cross-realm
  Sugestão: Incluir realm_id no payload e construir a key diretamente

[11.9] CRÍTICO — _activate_powerup e sell_on_market têm TOCTOU
  Arquivo: main.py:2101-2125, 2492-2523
  Tipo: Time-of-check to time-of-use (TOCTOU)
  Descrição: _activate_powerup verifica o inventário, depois decrementa
    em chamadas separadas. sell_on_market lê o inventário, depois
    decrementa. Entre check e update, outro request pode esgotar o item.
  Impacto: CRÍTICO — power-ups podem ser ativados/vendidos com inventário negativo
  Sugestão: Usar script Lua atômico: verificar+decrementar em uma operação

================================================================================
MATRIZ DE PRIORIDADE
================================================================================

CRÍTICOS (corrigir antes de deploy):
  [1.1] card_detail_key assinatura incompatível
  [5.1] Keys Redis inconsistentes (consequência de [1.1])
  [11.1] str() vs json.dumps() em eventos globais
  [11.7] Saldo pode ficar negativo em PvP
  [11.9] TOCTOU em power-ups e mercado

MÉDIOS (corrigir na próxima sprint):
  [3.1] publish_event_status nunca chamada
  [7.1] Operações financeiras sem try/except
  [7.2] Transferência PvP sem atomicidade
  [7.3] Race condition em mercado (pop-then-check)
  [8.1] Username em path sem validação
  [9.1] 10 endpoints sem rate limiting
  [10.1] Operações de saldo sem logging
  [11.2] SCAN operations em PvP
  [11.6] Race condition em compra de energia
  [11.8] PvP score update usa SCAN global

BAIXOS (melhorias técnicas):
  [1.2] Importação unused: field
  [1.3] Importação unused: event_envelope
  [1.4] Funções storage.py sem consumidores
  [2.1] healthcheck com dois decorators
  [2.2] GET com body em decoder_start
  [4.1] _event_relays acoplamento implícito
  [5.3] BIP39_WORDLIST com duplicatas
  [8.3] blocks_mined sem ge=0
  [10.2] _roll_crate_item sem logging
  [11.3] datetime.datetime redundante
  [11.4] random import dentro de função
  [11.5] time import dentro de função
