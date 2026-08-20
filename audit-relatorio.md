# MEMPOOL MINER — AUDITORIA DE INTEGRAÇÃO BACKEND ↔ FRONTEND
# Gerado: 2026-08-16
# Arquivos auditados:
#   - backend/app/main.py (4594 linhas)
#   - backend/app/storage.py (302 linhas)
#   - frontend/game.js (4000 linhas)
#   - frontend/index.html (550 linhas)

================================================================================
RESUMO EXECUTIVO
================================================================================

Total de problemas encontrados: 47
  - CRÍTICOS: 12
  - MÉDIOS: 19
  - BAIXOS: 16

Categorias:
  1. Endpoints vs Chamadas: 8 problemas
  2. Payload Consistency: 7 problemas
  3. WebSocket Events: 5 problemas
  4. Redis Keys: 4 problemas
  5. Cross-feature Conflicts: 6 problemas
  6. State Synchronization: 5 problemas
  7. Error Responses: 4 problemas
  8. Authentication: 4 problemas
  9. Data Validation: 4 problemas
  10. Race Conditions: 4 problemas

================================================================================
1. ENDPOINTS VS CHAMADAS (8 problemas)
================================================================================

[P1] CRÍTICO — Endpoint decoder/start usa GET mas recebe body JSON
  Backend: main.py:4439 — @app.get("/api/v1/networks/{realm_id}/decoder/start")
  Frontend: game.js:3814-3819 — fetch com method: 'GET' e body JSON.stringify(...)
  Descrição: O backend declara o endpoint como GET, mas o frontend envia um body
    JSON com {username}. O FastAPI pode rejeitar GET com body, e o parâmetro
    `data: DecoderStart` no handler espera um body que GET não fornece.
  Impacto: O mini-game Decoder nunca inicia — o endpoint falha silenciosamente.
  Correção: Trocar @app.get para @app.post no backend (main.py:4439).

[P2] MÉDIO — Endpoint staking/status URL mismatch
  Backend: main.py:3871 — @app.get("/api/v1/networks/{realm_id}/staking/status")
  Frontend: game.js:3424-3427 — stakingStatusUrl inclui username no path:
    `/staking/status/${username}`
  Descrição: O backend não tem {username} no path do endpoint de status, mas o
    frontend constrói a URL com o username no final. A requisição retorna 404.
  Impacto: Status do stake nunca é carregado — countdown não inicia, histórico
    não é atualizado.
  Correção: Adicionar {username} ao path do backend OU remover username da URL
    do frontend. Recomenda-se adicionar username ao backend para consistência
    com outros endpoints player-specific.

[P3] MÉDIO — Endpoint staking/history URL mismatch
  Backend: main.py:3943 — @app.get("/api/v1/networks/{realm_id}/staking/history")
  Frontend: game.js:3429-3432 — stakingHistoryUrl inclui username no path:
    `/staking/history/${username}`
  Descrição: Mesmo problema de [P2] — o frontend adiciona username ao path mas
    o backend não espera.
  Impacto: Histórico de stakes nunca é carregado.
  Correção: Mesma correção de [P2].

[P4] MÉDIO — Endpoint energy/spend sem body no frontend
  Backend: main.py:4204-4205 — @app.post("/api/v1/networks/{realm_id}/energy/spend")
    espera username como path param (não como body)
  Frontend: game.js — NENHUMA CHAMADA ENCONTRADA para energy/spend
  Descrição: O endpoint de gastar energia existe no backend mas o frontend não
    faz nenhuma chamada para ele. O botão de comprar energia (btn-buy-energy)
    existe no HTML (index.html:163) mas não tem handler no game.js.
  Impacto: O sistema de energia não gasta energia ao iniciar rodadas. O botão
    de comprar energia não funciona.
  Correção: Adicionar handler para btn-buy-energy no frontend e integrar
    energy/spend no fluxo de início de rodada.

[P5] MÉDIO — Endpoint energy/buy sem handler no frontend
  Backend: main.py:4256-4323 — @app.post("/api/v1/networks/{realm_id}/energy/buy")
  Frontend: index.html:163 — botão btn-buy-energy existe
  game.js: NENHUMA CHAMADA para energy/buy
  Descrição: Botão de comprar energia existe no HTML mas não tem event listener
    nem função correspondente no game.js.
  Impacto: Jogador não pode comprar energia — feature quebrada.
  Correção: Adicionar event listener para btn-buy-energy e função buyEnergy().

[P6] MÉDIO — Endpoint friends/* sem integração no frontend
  Backend: main.py:4025-4130 — endpoints /friends/add, /friends/remove, /friends/{username}
  Frontend: game.js — NENHUMA CHAMADA para endpoints de amigos
  Descrição: Sistema de amigos completo no backend sem qualquer integração no
    frontend. Não há UI para adicionar/remover amigos ou ver lista.
  Impacto: Feature de amigos e co-op bonus inexistente do lado do cliente.
  Correção: Implementar painel de amigos no frontend com chamadas aos endpoints.

[P7] BAIXO — Endpoint global-events sem polling no frontend
  Backend: main.py:624-657 — @app.get("/api/v1/networks/{realm_id}/global-events")
  Frontend: game.js:641-660 — Estado de eventos globais existe (activeGlobalEvent,
    EVENT_META, EVENT_DURATION) mas NENHUMA CHAMADA fetch ao endpoint
  Descrição: O frontend tem toda a estrutura para eventos globais (banners,
    countdown, preannounce) mas não carrega dados do endpoint REST. Os eventos
    só chegam via WebSocket (event_preannounce, event_started, event_ended).
  Impacto: Se o WebSocket reconectar, o estado de eventos globais é perdido
    até o próximo evento. O frontend não sabe qual evento estava ativo.
  Correção: Adicionar fetch ao endpoint global-events no startSession() e
    após reconexão WebSocket.

[P8] BAIXO — Endpoint achievements/definitions nunca chamado
  Backend: main.py:1141-1162 — @app.get("/api/v1/networks/{realm_id}/achievements/definitions")
  Frontend: game.js — NENHUMA CHAMADA
  Descrição: Endpoint de definições de achievements existe mas nunca é chamado.
    O frontend carrega achievements via /achievements/{username} que já inclui
    todas as definições.
  Impacto: Nenhum — endpoint redundante mas inofensivo.
  Correção: Remover endpoint ou documentar como endpoint público para
    visualização sem login.

================================================================================
2. PAYLOAD CONSISTENCY (7 problemas)
================================================================================

[P9] CRÍTICO — card_detail_key signature mismatch
  Backend: storage.py:160-162 — card_detail_key(realm_id, card_id) aceita 2 args
  Backend: main.py:3314 — card_detail_key(realm_id, username, bh) passa 3 args
  Descrição: A função card_detail_key em storage.py aceita (realm_id, card_id)
    mas em main.py:3314 é chamada com 3 argumentos: (realm_id, username, bh).
    Isso causa TypeError em tempo de execução.
  Impacto: O sistema de Block Cards falha completamente ao tentar buscar
    detalhes de cards individuais.
  Correção: Corrigir a chamada em main.py:3314 para usar 2 argumentos ou
    atualizar storage.py para aceitar 3.

[P10] MÉDIO — PlayerStateUpdate não inclui hints_used/rbf_used/mev_found no sync
  Backend: main.py:318-331 — PlayerStateUpdate tem hints_used, rbf_used, mev_found
  Frontend: game.js:1218-1225 — syncPlayerState() envia apenas:
    username, balance, hardware_level, lightning_active,
    lightning_blocks_remaining, combo_multiplier
  Descrição: O frontend não sincroniza hints_used, rbf_used e mev_found com o
    backend. Esses campos existem no modelo mas nunca são atualizados via sync.
  Impacto: Stats de achievements que dependem de rbf_used (missão "Use RBF")
    nunca são atualizados corretamente.
  Correção: Adicionar hints_used, rbf_used, mev_found ao payload de
    syncPlayerState().

[P11] MÉDIO — WebSocket transaction_received: campo expand_grid não usado
  Backend: main.py:121 — expand_grid está em PUBLIC_EVENT_FIELDS
  Frontend: game.js:943 — txBuffer.push não inclui expand_grid
  Descrição: O backend pode enviar expand_grid no evento transaction_received
    mas o frontend não o processa. A grade só se expande baseada no vsize.
  Impacto: Se o backend usar expand_grid para controlar o tamanho da grade,
    o frontend ignora o sinal.
  Correção: Adicionar suporte a expand_grid no frontend ou remover do backend
    se não for usado.

[P12] MÉDIO — Achievement payload: stat_name vs stat inconsistency
  Backend: main.py:1086-1097 — achievements_list retorna sem stat_name
  Frontend: game.js:2163 — renderAchievementsModal() acessa ach.stat_name
  Descrição: O backend não inclui stat_name no payload de achievements, mas o
    frontend tenta acessá-lo para renderizar o label de progresso.
  Impacto: O label de progresso de achievements mostra "undefined/0" para
    best_rank.
  Correção: Adicionar stat_name ao payload do backend ou usar ach.requirement.stat
    no frontend.

[P13] BAIXO — Decoder start: frontend envia body em GET request
  Frontend: game.js:3814-3819 — fetch com method: 'GET' e body JSON
  Descrição: Mesmo problema de [P1] — o frontend envia body em uma requisição
    GET, que é contra a especificação HTTP e pode ser rejeitado por proxies.
  Impacto: Comportamento indefinido dependendo do servidor/proxy.
  Correção: Usar POST ou query params.

[P14] BAIXO — Mission progress update: frontend envia stats incompletos
  Frontend: game.js:2950-2961 — updateMissionsProgress() envia apenas:
    words_found, high_fee_found, mev_found, rbf_used, blocks_completed
  Backend: main.py:1480-1487 — Espera também max_round_earnings
  Descrição: A missão "earn_50k_round" (ganhar 50K sats em uma rodada) nunca
    é completada porque o frontend não envia max_round_earnings.
  Impacto: Missão "earn_50k_round" é impossível de completar.
  Correção: Adicionar max_round_earnings ao payload de updateMissionsProgress().

[P15] BAIXO — PvP score update: found_count calculado erroneamente
  Backend: main.py:3216 — found_count = data.score // 100
  Descrição: O backend calcula found_count dividindo score por 100, o que é
    uma estimativa arbitrária sem relação com o número real de palavras
    encontradas.
  Impacto: O display de progresso PvP (challenger_found/challenged_found)
    mostra valores imprecisos.
  Correção: Enviar found_count explícito no payload do frontend.

================================================================================
3. WEBSOCKET EVENTS (5 problemas)
================================================================================

[P16] CRÍTICO — Eventos globais WebSocket não tratados no frontend
  Backend: main.py:146-175 — PUBLIC_EVENT_FIELDS inclui:
    event_preannounce, event_started, event_ended
  Frontend: game.js:868-872 — scopedActions não inclui eventos globais
  Descrição: O backend envia eventos event_preannounce, event_started e
    event_ended via WebSocket, mas o frontend não os trata no handler
    socket.onmessage. O frontend tem toda a estrutura de UI para eventos
    globais (eventBannerEl, eventCountdownInterval, etc.) mas nunca recebe
    os dados.
  Impacto: Eventos globais (Fee Spike, Golden Rush, Mempool Flood, Lightning
    Storm) nunca são ativados no frontend.
  Correção: Adicionar handlers para event_preannounce, event_started e
    event_ended no socket.onmessage.

[P17] MÉDIO — Eventos PvP WebSocket não tratados no frontend
  Backend: main.py:3226-3243 — PUBLIC_EVENT_FIELDS inclui:
    pvp_challenge, pvp_start, pvp_score_update, pvp_end, pvp_timer
  Frontend: game.js — NENHUM HANDLER para eventos PvP via WebSocket
  Descrição: O backend publica eventos PvP no canal PubSub, mas o frontend
    não os consome. O painel PvP existe no HTML mas não recebe atualizações
    em tempo real.
  Impacto: PvP funciona apenas via polling REST (se implementado), sem
    atualizações em tempo real.
  Correção: Adicionar handlers para eventos PvP no socket.onmessage ou
    implementar polling REST para PvP.

[P18] MÉDIO — Evento heartbeat do WebSocket não tratado no frontend
  Backend: main.py:1873-1875 — ws_sender envia {"action":"heartbeat"}
  Frontend: game.js:868-872 — heartbeat não está em scopedActions e não
    tem handler
  Descrição: O backend envia heartbeats a cada 30s mas o frontend não os
    processa. O heartbeat deveria ser usado para manter o estado online
    do jogador.
  Impacto: O sistema de online status (Fase 11) não funciona corretamente
    porque o frontend não responde a heartbeats.
  Correção: Adicionar handler para heartbeat que envie player_heartbeat
    de volta ao backend.

[P19] BAIXO — Evento chat_message não enviado via WebSocket
  Backend: main.py:2238 — _store_chat_message cria envelope com action: "chat_message"
    mas armazena apenas no Redis List, não publica no canal de eventos
  Frontend: game.js:3288-3293 — Após enviar mensagem, adiciona localmente
    mas não recebe broadcast de outros jogadores
  Descrição: Mensagens de chat são armazenadas no Redis mas não publicadas
    no canal PubSub do realm. Outros jogadores não recebem mensagens em
    tempo real.
  Impacto: Chat não funciona em tempo real — cada jogador só vê suas próprias
    mensagens.
  Correção: Publicar mensagens de chat no canal events_channel do realm
    após armazenar no Redis.

[P20] BAIXO — Evento leaderboard_reset: frontend não trata campo realm_id
  Backend: main.py:134 — PUBLIC_EVENT_FIELDS["leaderboard_reset"] inclui realm_id
  Frontend: game.js:996-1001 — Handler verifica data.epoch mas não data.realm_id
  Descrição: O evento leaderboard_reset inclui realm_id mas o frontend não
    verifica se o reset é para o realm ativo.
  Impacto: Se houver múltiplos realms, o frontend pode processar resets de
    outros realms.
  Correção: Adicionar verificação de realm_id no handler.

================================================================================
4. REDIS KEYS (4 problemas)
================================================================================

[P21] CRÍTICO — decoder_key:pending não definida em storage.py
  Backend: main.py:4488 — answer_key = f"{key}:pending"
  storage.py:267-275 — decoder_key(realm_id, username) definida
  Descrição: O backend usa uma chave derivada {decoder_key}:pending para
    armazenar a resposta correta do decoder, mas esta chave não é definida
    em storage.py. Funciona mas viola a convenção de todas as keys serem
    declaradas em storage.py.
  Impacto: Baixo — funciona, mas dificulta auditoria de keys e pode causar
    vazamento de dados se o TTL de 60s não for respeitado.
  Correção: Adicionar decoder_pending_key() em storage.py.

[P22] MÉDIO — sprint_leaderboard_key definida mas nunca usada
  storage.py:238-240 — sprint_leaderboard_key(realm_id) definida
  main.py: NENHUMA REFERÊNCIA a sprint_leaderboard_key
  Descrição: A key do leaderboard de sprint é definida em storage.py mas
    nunca é usada no main.py. O modo sprint mencionado no comentário
    não tem implementação no backend.
  Impacto: Key órfã que nunca é populada.
  Correção: Implementar modo sprint no backend ou remover a key.

[P23] MÉDIO — streak_key e daily_reward_key definidas mas nunca usadas
  storage.py:110-118 — streak_key e daily_reward_key definidas
  main.py: NENHUMA REFERÊNCIA a streak_key ou daily_reward_key
  Descrição: Keys para streak de login diário e recompensa diária são
    definidas mas nunca usadas no backend.
  Impacto: Features de login diário e recompensa semanal não funcionam.
  Correção: Implementar endpoints de streak/daily reward ou remover keys.

[P24] BAIXO — epoch_key e dedupe_key definidas mas pouco usadas
  storage.py:50-62 — epoch_key e dedupe_key definidas
  main.py: epoch_key usada apenas em network_snapshot (indiretamente)
    dedupe_key NUNCA usada no main.py
  Descrição: dedupe_key é definida para deduplicação de TXIDs mas nunca
    é usada no main.py. A deduplicação parece ser feita apenas no frontend.
  Impacto: Se o ingestor publicar TXIDs duplicados, o backend não deduplica.
  Correção: Usar dedupe_key no ingestor ou remover se a deduplicação for
    responsabilidade do frontend.

================================================================================
5. CROSS-FEATURE CONFLICTS (6 problemas)
================================================================================

[P25] CRÍTICO — Energy System vs Modo Sprint: conflito de recursos
  Backend: main.py:4137-4253 — Energy System gasta 1 energy por rodada
  Frontend: game.js — Modo sprint não implementado no backend
  storage.py:238 — sprint_leaderboard_key existe
  Descrição: O sistema de energia consome energia por rodada, mas se existir
    um modo sprint (sugerido pela sprint_leaderboard_key), não está claro
    se o sprint deve ou não consumir energia. Sem documentação do contrato.
  Impacto: Se o modo sprint for implementado, pode haver conflito sobre
    se energia deve ser consumida.
  Correção: Documentar explicitamente se modo sprint consome energia.

[P26] MÉDIO — Staking bonus vs Achievement bonus vs Skill bonus: stacking não documentado
  Backend: main.py:3704-3708 — Staking: +5%/+15%/+30%
  Backend: main.py:1032-1053 — Achievements: reward_percent acumulado
  Backend: main.py:1606-1616 — Skills: lightning_reward_percent
  Frontend: game.js:2312-2315 — applyAchievementBonus aplica apenas achievement
  Descrição: Três sistemas de bônus de recompensa existem (staking, achievements,
    skills) mas não está claro como eles se combinam. O frontend aplica apenas
    o bônus de achievements. Os bônus de staking e skills não são aplicados
    no cálculo de pontos.
  Impacto: Bônus de staking e skills são invisíveis para o jogador — os
    recursos gastos não geram retorno perceptível.
  Correção: Definir ordem de aplicação dos bônus (multiplicativo vs aditivo)
    e implementar no frontend.

[P27] MÉDIO — Boss Battles vs Energy System: boss consome energia?
  Frontend: game.js:2490-2583 — buildBossPlayableBlock() inicia rodada de boss
  Backend: main.py:4204-4253 — spend_energy() gasta 1 energy
  Descrição: Não está claro se rodadas de boss consomem energia. O frontend
    não chama energy/spend antes de iniciar uma rodada de boss.
  Impacto: Se o energy system for ativado, rodadas de boss podem ser
    gratuitas (exploit) ou impossíveis (se energia for verificada).
  Correção: Explicitar se boss blocks consomem energia e implementar.

[P28] MÉDIO — Lightning Mode vs Energy System: conflito de timers
  Frontend: game.js:1330-1364 — Lightning mode: 10× recompensa, grid 8×8,
    timer 20s, dura LIGHTNING_CHANNEL_DURATION blocos
  Backend: main.py:4137-4253 — Energy System: 10 energy max, regenera a cada 30min
  Descrição: O modo Lightning altera o timer da rodada para 20s (ultra rápido)
    mas o sistema de energia não tem exceção para o modo Lightning. Se o
    jogador ficar sem energia durante o Lightning, o canal L2 fica ativo
    mas o jogador não pode jogar.
  Impacto: Jogador pode ficar preso com Lightning ativo mas sem energia.
  Correção: Adicionar exceção de energia para modo Lightning ou garantir
    energia suficiente ao ativar Lightning.

[P29] BAIXO — Multiple function wrapping: teardownSession sobrescrito 3 vezes
  Frontend: game.js:3354-3365 — teardownSession wrapped para chat
  Frontend: game.js:3754-3769 — teardownSession wrapped para staking
  Descrição: teardownSession é sobrescrito múltiplas vezes com wrappers
    diferentes. Cada wrapper chama o anterior, criando uma cadeia de
    chamadas. Se a ordem de carregamento mudar, o comportamento quebra.
  Impacto: Fragilidade na ordem de execução dos cleanup handlers.
  Correção: Usar um sistema de hooks/events em vez de sobrescrever funções.

[P30] BAIXO — startSession sobrescrito 2 vezes com wrappers encadeados
  Frontend: game.js:2981-2999 — startSession wrapped para missões
  Frontend: game.js:3368-3380 — startSession wrapped para chat/staking
  Descrição: startSession é sobrescrito duas vezes, criando uma cadeia
    de wrappers. O segundo wrapper chama o primeiro, que chama o original.
  Impacto: Fragilidade similar a [P29].
  Correção: Usar sistema de hooks.

================================================================================
6. STATE SYNCHRONIZATION (5 problemas)
================================================================================

[P31] CRÍTICO — Balance desincronizado: frontend calcula localmente
  Frontend: game.js:1792 — balanceSatoshis += Math.floor(points)
  Frontend: game.js:1787 — balanceSatoshis += mevBonus (50000)
  Frontend: game.js:1316 — balanceSatoshis -= nextPrice (hardware)
  Backend: main.py:880-898 — update_player_state via syncPlayerState()
  Descrição: O frontend calcula o saldo localmente e só sincroniza com o
    backend via syncPlayerState() (chamado após cada ação). Se a sync
    falhar, o saldo local diverge do backend. Além disso, o backend não
    valida o saldo enviado — aceita qualquer valor.
  Impacto: Se syncPlayerState() falhar, o saldo local diverge do backend.
    Ao reconectar, loadPlayerState() sobrescreve o saldo local com o
    valor do backend, causando perda ou ganho de sats.
  Correção: O backend deve calcular o saldo server-side e o frontend
    deve usar o saldo retornado pelo backend como source of truth.

[P32] MÉDIO — Energy state não sincronizado com backend
  Frontend: index.html:66-73 — UI de energia existe (energy-bar, energy-count)
  Frontend: game.js — NENHUMA VARIÁVEL DE ESTADO PARA ENERGIA
  Backend: main.py:4143-4201 — get_energy_status retorna estado completo
  Descrição: O frontend tem UI para energia mas não tem variável de estado
    local nem faz polling do endpoint de energia. A barra de energia no
    HTML nunca é atualizada.
  Impacto: A barra de energia mostra o valor inicial (10/10) e nunca muda.
  Correção: Adicionar variável de estado de energia no frontend e polling
    do endpoint /energy/status.

[P33] MÉDIO — Combo multiplier não persistido corretamente
  Frontend: game.js:1740-1743 — comboMultiplier calculado localmente
  Backend: main.py:312 — PlayerState.combo_multiplier: float, 1.0-4.0
  Frontend: game.js:1224 — syncPlayerState() envia combo_multiplier
  Descrição: O combo multiplier é resetado para 1.0 a cada erro (game.js:1840)
    e a cada rodada perdida (game.js:1953). Se o jogador reconectar, o
    combo do backend pode ser diferente do local.
  Impacto: Baixo — combo é resetado no início de cada rodada de qualquer
    forma, mas a persistência é inconsistente.
  Correção: Resetar combo_multiplier no backend ao iniciar nova rodada.

[P34] BAIXO — Session state (sessionStorage) pode estar desatualizado
  Frontend: game.js:116-143 — saveSessionState() salva em sessionStorage
  Frontend: game.js:698-732 — loadSessionState() restaura ao carregar
  Descrição: O sessionStorage salva o estado local que pode divergir do
    backend. Ao restaurar, o frontend carrega do sessionStorage E DO
    backend (loadPlayerState), mas a ordem de prioridade não está clara.
  Impacto: Se o backend tiver dados mais recentes, o sessionStorage pode
    sobrescrevê-los.
  Correção: Priorizar dados do backend sobre sessionStorage ao restaurar.

[P35] BAIXO — PvP state não sincronizado entre jogadores
  Backend: main.py:2866-2945 — _update_pvp_score atualiza score no Redis
  Frontend: game.js — NENHUMA CHAMADA para /pvp/score
  Descrição: O backend tem endpoint para atualizar score PvP mas o frontend
    nunca o chama. O estado PvP no Redis nunca é atualizado durante a
    partida.
  Impacto: O sistema PvP não funciona — scores não são rastreados.
  Correção: Chamar /pvp/score a cada palavra encontrada durante PvP.

================================================================================
7. ERROR RESPONSES (4 problemas)
================================================================================

[P36] MÉDIO — Erros 503 Redis não tratados especificamente no frontend
  Backend: main.py:423-447 — redis_error_handler retorna 503 com Retry-After: 5
  Frontend: game.js — fetch handlers genéricos verificam !response.ok
  Descrição: O frontend não trata especificamente erros 503 com Retry-After.
    Todas as requisições falham com "Erro ao buscar..." sem indicar que o
    serviço está temporariamente indisponível.
  Impacto: UX ruim — jogador não sabe se o erro é temporário ou permanente.
  Correção: Adicionar tratamento específico para 503 com retry automático.

[P37] MÉDIO — Erro 429 rate limit do chat não mostra tempo de espera
  Backend: main.py:2274-2275 — HTTPException 429 com detail genérico
  Frontend: game.js:3281-3284 — appendSystemMessage com detail do backend
  Descrição: O backend retorna "Limite de mensagens excedido. Aguarde 1 minuto."
    mas o frontend não extrai o tempo de espera para mostrar um countdown.
  Impacto: Jogador não sabe quando pode enviar novamente.
  Correção: Incluir Retry-After no response do backend e mostrar countdown
    no frontend.

[P38] BAIXO — Erro de saldo insuficiente em staking não atualiza UI
  Backend: main.py:3757-3761 — HTTPException 400 com detail do saldo
  Frontend: game.js:3636-3639 — announceGameStatus com errorData.detail
  Descrição: O erro é mostrado no game status mas o saldo na UI não é
    atualizado. Se o saldo do backend divergir do local, o jogador não sabe.
  Impacto: Baixo — jogador pode tentar staking novamente sem saber que o
    saldo mudou.
  Correção: Recarregar saldo do backend após erro de saldo insuficiente.

[P39] BAIXO — Erro de crate sem saldo não recarrega inventário
  Backend: main.py:3525-3526 — HTTPException 400 "Saldo insuficiente"
  Frontend: game.js — NENHUMA CHAMADA para crates (endpoint não integrado)
  Descrição: O sistema de crates não está integrado no frontend. O modal
    de crate existe no HTML mas não tem handlers no game.js.
  Impacto: Sistema de crates completamente inoperante do lado do cliente.
  Correção: Implementar integração completa de crates no frontend.

================================================================================
8. AUTHENTICATION (4 problemas)
================================================================================

[P40] CRÍTICO — Nenhum mecanismo de autenticação em endpoints sensíveis
  Backend: main.py:880-898 — update_player_state aceita qualquer username
  Backend: main.py:1108-1138 — update_stats aceita qualquer username
  Backend: main.py:3712-3796 — stake_sats aceita qualquer username
  Descrição: Todos os endpoints que modificam dados do jogador aceitam o
    username como parâmetro sem verificar se o cliente é realmente aquele
    jogador. Qualquer pessoa pode modificar o saldo, stats, staking, etc.
    de qualquer jogador.
  Impacto: Qualquer cliente pode roubar sats, modificar stats, cancelar
    stakes, e alterar dados de outros jogadores.
  Correção: Implementar autenticação (JWT, session tokens, ou pelo menos
    binding do WebSocket com username).

[P41] CRÍTICO — WebSocket não autentencia jogador
  Backend: main.py:4585-4588 — websocket_v1 aceita conexão sem username
  Backend: main.py:1912-1925 — ws_receiver aceita player_heartbeat com
    qualquer username
  Descrição: O WebSocket não requer autenticação. Qualquer cliente pode
    se conectar e enviar player_heartbeat com qualquer username, marcando
    qualquer jogador como online.
  Impacto: Falsificação de status online e potencial para spoofing de
    identidade.
  Correção: Exigir username no handshake WebSocket ou implementar tokens.

[P42] MÉDIO — PvP challenge: jogador pode desafiar com username falso
  Backend: main.py:3046-3139 — challenge_player aceita username e target
    sem verificar identidade
  Descrição: Qualquer cliente pode criar desafios PvP entre jogadores
    arbitrários sem ser nenhum deles.
  Impacto: Spam de desafios PvP e confusão entre jogadores.
  Correção: Verificar identidade do jogador antes de criar desafios.

[P43] MÉDIO — Market buy: comprador pode usar username diferente
  Backend: main.py:2541-2690 — buy_from_market usa data.username como
    comprador sem verificar identidade
  Descrição: Qualquer cliente pode comprar power-ups do mercado usando
    qualquer username, gastando o saldo de outro jogador.
  Impacto: Roubo de saldo via compras no mercado.
  Correção: Autenticar o jogador antes de processar compras.

================================================================================
9. DATA VALIDATION (4 problemas)
================================================================================

[P44] MÉDIO — syncPlayerState: backend não valida balance enviado
  Backend: main.py:880-898 — update_player_state aceita balance do cliente
  Frontend: game.js:1218-1225 — envia balanceSatoshis calculado localmente
  Descrição: O backend aceita o balance enviado pelo cliente sem validar
    se é consistente com as ações realizadas. Um cliente malicioso pode
    enviar um balance arbitrariamente alto.
  Impacto: Inflação de saldo — jogador pode definir qualquer valor de sats.
  Correção: O backend deve calcular o balance server-side ou validar que
    o balance enviado é consistente com as transações.

[P45] MÉDIO — StatsUpdate: frontend envia valores absolutos, backend armazena
  Backend: main.py:1108-1138 — update_stats faz hset (sobrescreve)
  Frontend: game.js:2246-2253 — pushStats envia valores absolutos
  Descrição: O frontend envia stats como valores absolutos (ex: words_found: 50)
    e o backend sobrescreve com hset. Se duas requisições chegarem em paralelo,
    a última sobrescreve a primeira, potencialmente perdendo incrementos.
  Impacto: Race condition em stats — contadores podem ser perdidos.
  Correção: Usar HINCRBY no backend para incrementar atomicamente ou
    implementar versioning/ETag.

[P46] BAIXO — Decoder answer: backend não valida formato
  Backend: main.py:4530 — answer = data.answer.strip().lower()
  Descrição: O backend converte a resposta para lowercase mas não valida
    se contém apenas caracteres válidos. Respostas com caracteres especiais
    podem causar comportamento inesperado.
  Impacto: Baixo — comparações de string podem falhar silenciosamente.
  Correção: Validar que a resposta contém apenas letras.

[P47] BAIXO — Chat message: backend não valida emojis/unicode
  Backend: main.py:2207-2220 — _is_message_banned verifica palavras proibidas
  Descrição: A validação de chat verifica palavras proibidas em lowercase
    mas não valida se a mensagem contém apenas caracteres permitidos.
    Emojis e caracteres unicode são permitidos sem limitação.
  Impacto: Baixo — possível abuso com caracteres especiais.
  Correção: Adicionar validação de caracteres permitidos.

================================================================================
10. RACE CONDITIONS (4 problemas)
================================================================================

[P48] CRÍTICO — Market buy: zpopmin + verificação de saldo não atômica
  Backend: main.py:2565-2601 — zpopmin remove o listing, depois verifica
    saldo do comprador, e se falha, devolve o listing
  Descrição: Entre o zpopmin e a verificação de saldo, outro cliente pode
    comprar o mesmo listing (se o zpopmin falhar em devolver). Além disso,
    a verificação de saldo (hget) e a dedução (hset) não são atômicas.
  Impacto: Double-spend — o mesmo power-up pode ser vendido duas vezes,
    ou o saldo do comprador pode ficar negativo.
  Correção: Usar script Lua atômico para todo o fluxo de compra (já existe
    parcialmente mas a verificação inicial não é atômica com o zpopmin).

[P49] MÉDIO — Energy buy: verificação + débito de saldo não atômico
  Backend: main.py:4273-4285 — Verifica saldo, depois debita com hset
  Descrição: Entre a verificação do saldo e o débito, outro request pode
    modificar o saldo. Se dois requests de buy_energy chegarem simultaneamente,
    ambos podem passar na verificação e debitar o dobro.
  Impacto: Saldo pode ficar negativo se dois requests competirem.
  Correção: Usar script Lua ou pipeline transacional para verificação + débito.

[P50] MÉDIO — Staking: verificação de stake ativo + débito não atômica
  Backend: main.py:3736-3765 — Verifica se há stake ativo, verifica saldo,
    depois debita e cria stake
  Descrição: Múltiplas operações não atômicas entre verificação e execução.
    Dois requests de stake simultâneos podem ambos passar na verificação
    e criar dois stakes ativos.
  Impacto: Jogador pode ter múltiplos stakes ativos (exploit de bônus).
  Correção: Usar script Lua atômico para verificação + criação do stake.

[P51] BAIXO — Leaderboard score: frontend envia score após cada ação
  Frontend: game.js:1179-1203 — submitScore() chamado após cada palavra,
    compra, slashing
  Backend: main.py:712-717 — zadd com gt=True, ch=True
  Descrição: Múltiplas chamadas de submitScore em rápida sucessão podem
    causar condições de corrida no leaderboard. O backend usa ZADD GT que
    é atômico, mas o frontend pode enviar scores desatualizados se as
    requisições forem reordenadas pela rede.
  Impacto: Baixo — ZADD GT garante que apenas o maior score é mantido,
    mas scores intermediários podem ser perdidos se a rede reordenar.
  Correção: Implementar debounce no frontend para enviar score apenas a
    cada N segundos ou ao final da rodada.

================================================================================
PROBLEMAS ADICIONAIS (não categorizados acima)
================================================================================

[P52] BAIXO — BIP39_WORDLIST tem duplicatas
  Backend: main.py:4416-4418 — "duela", "duende", "dublador", "dublar"
    repetidos 3 vezes na lista
  Impacto: Palavras duplicadas aumentam a probabilidade de certas palavras
    serem escolhidas no decoder.
  Correção: Remover duplicatas da lista.

[P53] BAIXO — STAKE_BONUS_TABLE permite apenas 1, 6, 24 horas
  Backend: main.py:3704-3708 — Tabela fixa com 3 durações
  Frontend: index.html:285-296 — Botões com data-hours="1", "6", "24"
  Descrição: A validação no backend (main.py:3748) verifica se duration_hours
    está na tabela, mas o frontend envia o valor do botão selecionado. Se
    o HTML for modificado para adicionar uma duração não suportada, o
    backend rejeita.
  Impacto: Baixo — inconsistência entre frontend e backend se o HTML mudar.
  Correção: Sincronizar durações suportadas entre frontend e backend.

[P54] BAIXO — CRATE_PRICES hard-coded no backend
  Backend: main.py:3379 — CRATE_PRICES = {"crate": 5000}
  Frontend: index.html:174 — "5.000 sats" hard-coded no HTML
  Descrição: O preço da crate está hard-coded em ambos os lados. Se o preço
    mudar, precisa ser atualizado em dois lugares.
  Impacto: Baixo — inconsistência se o preço mudar.
  Correção: Retornar crate_price do endpoint /crates/inventory e usar no
    frontend.

================================================================================
FIM DO RELATÓRIO
================================================================================
