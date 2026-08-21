# Módulos e funções

## Backend

### app/engine.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| GameEngine.__init__ | método | recebe NodeConfig explícita, RPC, taxa e pool HTTP |
| GameEngine.tx_to_word | método | deriva a primeira palavra BIP39 de 128 bits |
| GameEngine._rpc_call | método interno | executa JSON-RPC e normaliza falhas |
| GameEngine.get_tx_metadata | método assíncrono | retorna palavra, vsize, sats/vB e flags |
| GameEngine.get_mempool_size | método assíncrono | consulta getmempoolinfo.size |
| GameEngine.get_blockchain_info | método assíncrono | consulta chain, IBD e pruning |
| GameEngine.validate_declared_network | método assíncrono | recusa RPC de outra chain |
| GameEngine.close | método assíncrono | fecha o pool HTTP |

### app/blockchain.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| BlockCallback | alias | contrato assíncrono para eventos de bloco |
| BitcoinZMQListener.__init__ | método | prepara um socket para uma origem explícita |
| BitcoinZMQListener.start | método assíncrono | assina tópicos e encaminha mensagens |
| BitcoinZMQListener.stop | método | solicita encerramento |

### app/config.py, events.py e storage.py

| Símbolo | Responsabilidade |
|---|---|
| NodeConfig | configuração privada service-local do ingestor |
| NETWORK_CATALOG | realms públicos, sem endpoints ou credenciais |
| event_envelope | identidade, realm, epoch, sequence e timestamp |
| funções `*_key` | namespace Redis validado por realm |
| ingestor_lease_key | exclusão mútua do publicador de um realm |
| migrate_legacy_default | copia contador/ranking antigo sem apagar rollback |

### app/ingestor.py

| Símbolo | Responsabilidade |
|---|---|
| NodeIngestor.enqueue_transaction | put_nowait e métrica de descarte |
| process_transaction(s) | BIP39/RPC, recheck de epoch, dedupe e publicação |
| handle_block | serializa a troca de epoch e remove backlog anterior |
| update_status | heartbeat, IBD, pruning, reconciliação da mempool e playable |
| acquire_lease / lease_loop | aquisição e renovação da lease por token |
| scripts `COMMIT_*` | fencing atômico de TX, bloco, status e shutdown |
| run / close | supervisão, lease e shutdown do processo singleton |

### app/ingestor_healthcheck.py

Valida no Redis se heartbeat e lease pertencem ao token local da instância, se
`NODE_ID`/`REALM_ID` são os esperados, se o estado é `ready`/`syncing` e se a
atualização ocorreu nos últimos 45 segundos. O token interno não é enviado pela
API ou WebSocket.

### app/main.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| normalize_username | função | remove bordas e valida caracteres |
| ScoreSubmit | modelo | contrato nickname/score |
| network_snapshot | função assíncrona | combina catálogo e heartbeat sanitizado |
| lifespan | context manager | testa Redis e migra chaves legadas |
| healthcheck / readiness | endpoints | saúde da API/Redis |
| get_networks | endpoint | catálogo multi-rede |
| submit_score_for_realm | função | grava recorde isolado com ZADD GT/CH |
| leaderboard_for_realm | função | retorna Top 10 do realm |
| get_pools_v1 | endpoint | Top 10 de pools (guildas) do realm |
| EventRelay | classe | assinatura PubSub persistente com fan-out para todos os ws_senders do realm |
| _relay_connections | dict | contador de conexões por realm; libera o relay no último desconectado |
| ws_sender | coroutine | fila do relay → WebSocket |
| ws_receiver | coroutine | detecta desconexão do cliente |
| serve_websocket | função | handshake e canal namespaced |
| ACHIEVEMENTS | dict | 28 conquistas em 5 categorias com bônus |
| _check_and_unlock_achievements | função | desbloqueia conquistas ao atualizar stats |
| _calculate_achievement_bonuses | função | soma bônus ativos do jogador |
| daily_mission_defs | lista | 6 missões diárias (3 rotativas por dia) |
| SKILL_BRANCHES | dict | ramos mining/search/lightning com níveis |
| CARD_RARITIES | dict | pesos common/rare/epic/legendary (60/25/10/5) |
| CRATE_PRICES / CRATE_POWERUPS / CRATE_SKINS | constantes | preço, power-ups e skins de crate |
| STAKE_BONUS_TABLE / STAKE_PENALTY_PERCENT | constantes | bônus por duração (1/6/24 h) e penalidade 10% |
| ENERGY_MAX / ENERGY_REFILL_INTERVAL / ENERGY_BUY_* | constantes | energia (máx 10, recarga 30 min, compra 3 por 2.000) |
| SPRINT_TIME_LIMIT / SPRINT_WORD_COUNT / SPRINT_REWARD_MULTIPLIER | constantes | sprint (30 s, 4 palavras, 0,5×) |
| RANK_DEFINITIONS / get_rank_for_level | função | 10 ranks temáticos por faixa de nível |
| xp_to_next_level / get_level_bonus | funções | curva de XP (nível×100) e bônus passivos |
| PVP_DURATION | constante | duração do duelo PvP (60 s) |

Endpoints de mecânicas (todos por realm): player, level, achievements, stats,
missions, skills, powerups, chat, market, pvp, cards, crates, staking,
friends, energy, decoder, season, sprint e global-events.

### app/global_events.py

| Símbolo | Responsabilidade |
|---|---|
| GlobalEventType | enum: `fee_spike`, `golden_rush`, `mempool_flood`, `lightning_storm` |
| EVENT_META / EVENT_DURATION_SECONDS | rótulos, ícones e durações (10/5/10/3 min) |
| EVENT_PREANNOUNCE_SECONDS | aviso antecipado de 120 s |
| GlobalEventScheduler | sorteia evento, publica `event_preannounce`/`event_started`/`event_ended` |
| get_active_event | lê o estado do evento global para o ingestor e a API |

### app/season_pass.py

| Símbolo | Responsabilidade |
|---|---|
| SEASON_DURATION_DAYS / SEASON_XP_PER_LEVEL | temporada de 28 dias, 100 XP/nível |
| SEASON_FREE_REWARDS / SEASON_PREMIUM_REWARDS | recompensas dos níveis 1–20 e 21–40 |
| get_season_data / add_season_xp | estado e progressão da temporada |
| claim_season_reward / buy_season_premium | resgate de recompensa e desbloqueio premium |

## Frontend

### Inicialização e infraestrutura

| Função | Responsabilidade |
|---|---|
| playSound | sintetiza feedback de tick, acerto, derrota e compra |
| registerPwa | registra o worker e acompanha atualizações sem recarregar durante a partida |
| updateConnectivityStatus | informa online/offline sem simular disponibilidade da API |
| setModalState | sincroniza classe, ARIA e foco inicial |
| configureGridSize | calcula trilhas e células responsivas |
| isValidTransactionEvent | valida o contrato mínimo recebido por WebSocket |
| isValidLeaderboardPayload | valida o JSON antes de alterar o Top 10 |
| initEmptyGrid | renderiza a grade decorativa inicial |
| loadNetworkCatalog | descobre status, IBD, pruning e opções jogáveis |
| teardownSession | invalida geração, socket, requests, timers e estado |
| pollNetworkHealth | detecta heartbeat expirado durante a sessão |
| startSession | escolhe realm, espera handshake e abre polling isolado |
| fetchLeaderboard | consulta e renderiza Top 10 com textContent |
| submitScore | envia o saldo fictício como recorde candidato |

### Loja e rodada

| Função | Responsabilidade |
|---|---|
| updateStoreUI | habilita e rotula compras |
| buyHint | destaca uma palavra pendente |
| buyHardware | compra nível e adiciona tempo |
| buyLightning | ativa o modo L2 simulado em transição atômica entre rodadas |
| prepareNextBlock | limpa estado e retorna à coleta |
| buildPlayableBlock | escolhe dificuldade, monta grade e inicia timer |
| injectWordInGrid | posiciona palavra sem sobreposição |
| renderBankWord | cria item seguro no banco de palavras |

### Entrada, feedback e resultado

| Função | Responsabilidade |
|---|---|
| handlePointerStart / Move / End / Cancel | unificam toque, mouse e caneta sem acumular listeners |
| handleGridKeydown | opera foco, seleção e cancelamento com teclado |
| startSelection | registra primeira célula |
| continueSelection | garante adjacência e direção retilínea |
| endSelection | valida, pontua e encerra tentativa |
| showFloatingText | anima recompensa |
| drawAnimatedLine | marca palavra no SVG |
| startNetworkRace | atualiza cronômetro/progressbar |
| showResult | exibe vitória ou derrota |
| showOrphanBlockSalvage | oferece RBF (100.000 sats → +15 s, janela 3 s) |

### Boss block

| Função | Responsabilidade |
|---|---|
| handleBossBlock | monta grade de boss (15×15, 10 palavras, 45 s) ao receber `boss_block` |
| updateBossHpUI | atualiza a barra de HP do `boss-hud` |
| handleBossTransaction | reduz HP a cada palavra encontrada |
| buildBossPlayableBlock | posiciona as 10 palavras do boss |
| startBossNetworkRace | cronômetro do boss |
| showBossResult / showBossDefeatModal | vitória (loot 50.000 sats) ou derrota |
| resetBossState | limpa estado do boss |

### Eventos globais

| Função | Responsabilidade |
|---|---|
| handleGlobalEventMessage | reage a `event_preannounce`/`event_started`/`event_ended` |
| renderGlobalEventBanner | mostra banner com ícone, descrição e cor |
| startGlobalEventCountdown / hideGlobalEventBanner | contagem regressiva e encerramento |
| loadActiveGlobalEvent | consulta o evento ativo ao conectar |

### Conquistas e estatísticas

| Função | Responsabilidade |
|---|---|
| fetchAchievements / loadAchievementStats | carrega conquistas e stats |
| renderAchievementsModal / openAchievementsModal | modal de conquistas com filtros |
| showAchievementToast | notificação de desbloqueio |
| trackWordFound / trackCombo / trackBlockCompleted / trackRealmPlayed / trackScoreSubmitted / trackPoolJoined / trackBestRank / trackEpochSurvived / trackPoolRank1 | alimentam as estatísticas |
| pushStats | envia stats ao backend (dispara desbloqueio) |
| applyAchievementBonus | soma bônus de conquistas à pontuação |

### Missões

| Função | Responsabilidade |
|---|---|
| loadMissions / renderMissions / createMissionCard | carrega e renderiza diárias/semanal |
| claimReward | resgata recompensão de missão |
| updateMissionsProgress | atualiza progresso local |

### Chat

| Função | Responsabilidade |
|---|---|
| loadChatHistory / renderChatMessages / appendChatMessage | histórico e render |
| sendChatMessage | envia mensagem com rate limiting |
| insertChatToken | insere emoji/token |
| updateRateLimitInfo | mostra limite restante |

### Staking

| Função | Responsabilidade |
|---|---|
| performStake / cancelStake | trava/cancela sats (1/6/24 h) |
| loadStakingStatus / loadStakingHistory | estado e histórico |
| updateStakingUI / startStakeCountdown / updateStakeTimer | UI e contagem regressiva |

### Decoder

| Função | Responsabilidade |
|---|---|
| startDecoderGame / submitDecoderAnswer | mini-game de 30 s (txid → palavra) |
| updateDecoderTimer / handleDecoderTimeout | cronômetro e timeout |
| checkDecoderAvailability | disponibilidade do mini-game |

### Skill tree

| Função | Responsabilidade |
|---|---|
| loadSkillTree / renderSkillTree | ramos mining/search/lightning |
| unlockSkill | compra nível |
| applySkillBonuses | soma bônus ativos |

### Energia

| Função | Responsabilidade |
|---|---|
| loadEnergyState / updateEnergyUI | energia (máx 10, recarga 30 min) |
| spendEnergy / buyEnergy | consome/compra (3 por 2.000 sats) |

### Season pass

| Função | Responsabilidade |
|---|---|
| loadSeasonData / renderSeasonUI / renderRewards | temporada, níveis e recompensas |
| claimSeasonReward / buySeasonPremium | resgate e desbloqueio premium |
| startSeasonTimer | contagem regressiva da temporada |

### Cards e crates

| Função | Responsabilidade |
|---|---|
| loadCardsData / renderCardsUI / renderCardsGrid | coleção de block cards |
| showCardPullAnimation | animação de card novo |
| loadCrateInventory / updateCrateUI | inventário e UI de crates |
| openCrate / showCrateResult | abre crate (grátis ou 5.000 sats) |

### Nível e XP

| Função | Responsabilidade |
|---|---|
| loadLevelState / updateLevelUI | nível, XP e rank |
| addXP | adiciona XP local |
| calculateWordXP | XP por palavra (comprimento×10 + combo×5) |

### Sprint

| Função | Responsabilidade |
|---|---|
| startSprintRound / showSprintTimer / updateSprintTimerDisplay / startSprintCountdown | corrida de 4 palavras em 30 s |
| endSprintRound / submitSprintResult / showSprintResult | encerra e envia resultado |
| loadSprintLeaderboard / renderSprintLeaderboard | ranking de sprint |

### Amigos e mercado

| Função | Responsabilidade |
|---|---|
| loadFriendsList / renderFriendsUI / renderFriendsList | lista de amigos |
| addFriend / removeFriend | gerencia amigos |
| loadMarketList / loadMarketHistory / loadMarketInventory | mercado de power-ups |
| renderMarketList / renderMarketHistory / populateSellDropdown | UI do mercado |
| buyMarketListing / sellMarketPowerup | compra e venda |

## Infraestrutura

| Arquivo | Responsabilidade |
|---|---|
| docker-compose.yaml | topologia, saúde, redes, volumes e limites |
| backend/Dockerfile | runtime Python sem root |
| frontend/Dockerfile | imagem Nginx contendo somente o PWA do jogo |
| frontend/nginx.conf | shell estático, CSP, proxy REST e upgrade WebSocket |
| frontend/manifest.webmanifest | instalação, escopo, tema e ícones do PWA |
| frontend/service-worker.js | cache limitado ao shell e atualização controlada |
| docs/Dockerfile / nginx.conf | portal sanitizado independente, profile `docs` |
| bitcoin/bitcoin.conf | parâmetros não secretos do nó |
| .env.example | contrato de configuração |

## Artefatos legados

As duas demonstrações antigas da raiz foram removidas do conjunto versionável;
eram mocks divergentes e não participavam da stack. Novos protótipos usam a
pasta local ignorada `prototypes/`; o atual é `mobile-pwa.html` e não define o
comportamento do runtime.
