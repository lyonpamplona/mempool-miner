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
| ws_sender | coroutine | Redis → WebSocket |
| ws_receiver | coroutine | detecta desconexão do cliente |
| serve_websocket | função | handshake e canal namespaced |

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
