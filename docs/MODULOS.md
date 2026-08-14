# Módulos e funções

## Backend

### app/engine.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| required_environment | função | exige uma variável sem criar segredo padrão |
| GameEngine.__init__ | método | carrega rede, RPC, limiar de taxa e pool HTTP |
| GameEngine.tx_to_word | método | deriva a primeira palavra BIP39 de 128 bits |
| GameEngine._rpc_call | método interno | executa JSON-RPC e normaliza falhas |
| GameEngine.get_tx_metadata | método assíncrono | retorna palavra, vsize, sats/vB e flags |
| GameEngine.get_mempool_size | método assíncrono | consulta getmempoolinfo.size |
| GameEngine.close | método assíncrono | fecha o pool HTTP |

### app/blockchain.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| BlockCallback | alias | contrato assíncrono para eventos de bloco |
| BitcoinZMQListener.__init__ | método | prepara endereço, SUB socket e fila |
| BitcoinZMQListener.start | método assíncrono | assina tópicos e encaminha mensagens |
| BitcoinZMQListener.stop | método | solicita encerramento |

### app/main.py

| Símbolo | Tipo | Responsabilidade |
|---|---|---|
| normalize_username | função | remove bordas e valida caracteres |
| ScoreSubmit | modelo | contrato nickname/score |
| process_tx_queue | worker assíncrono | calcula TXID, busca metadados e publica |
| handle_block | callback assíncrono | reconcilia contador e publica bloco |
| lifespan | context manager | startup e shutdown de tarefas/recursos |
| healthcheck | endpoint | testa Redis |
| submit_score | endpoint | grava recorde com ZADD GT e informa mudanças com CH |
| get_leaderboard | endpoint | retorna Top 10 |
| ws_sender | coroutine | Redis → WebSocket |
| ws_receiver | coroutine | detecta desconexão do cliente |
| websocket_endpoint | endpoint | sessão WebSocket completa |

## Frontend

### Inicialização e infraestrutura

| Função | Responsabilidade |
|---|---|
| playSound | sintetiza feedback de tick, acerto, derrota e compra |
| setModalState | sincroniza classe, ARIA e foco inicial |
| configureGridSize | calcula trilhas e células responsivas |
| isValidTransactionEvent | valida o contrato mínimo recebido por WebSocket |
| isValidLeaderboardPayload | valida o JSON antes de alterar o Top 10 |
| initEmptyGrid | renderiza a grade decorativa inicial |
| startSession | normaliza nickname, abre WebSocket e polling |
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
| handleTouchStart / handleTouchMove | adaptam toque para a seleção |
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
| frontend/Dockerfile | imagem Nginx com app e documentação |
| frontend/nginx.conf | arquivos, proxy REST e upgrade WebSocket |
| bitcoin/bitcoin.conf | parâmetros não secretos do nó |
| .env.example | contrato de configuração |

## Artefatos legados

prototipo-v2.html e prototipo-game-L2.html são demonstrações standalone com
dados mockados. Não participam da stack e não definem o comportamento atual.
Eles permanecem como histórico de produto e são auditados em
[AUDITORIA.md](AUDITORIA.md).
