# Changelog

Este arquivo segue o formato Keep a Changelog. O projeto ainda não definiu uma
política formal de versionamento.

## 2026-08-20 — Correções de pipeline BIP39, fan-out e infraestrutura

### Adicionado

- `EventRelay` persistente com fan-out: cada evento PubSub é replicado para
  TODAS as filas de clientes WebSocket conectados (antes, um único cliente
  recebia cada evento);
- contador de conexões por realm (`_relay_connections`) para liberar o relay
  quando o último cliente desconecta;
- `txid` completo no payload público de `transaction_received`;
- aplicação de eventos globais (`apply_event_effects`) no ingestor —
  `fee_spike` (todas High Fee, 3×), `golden_rush` (golden 3× mais frequente,
  5×), `mempool_flood` (2×, grade 15×15) e `lightning_storm` (10×, grade 8×8)
  agora afetam as transações publicadas;
- `is_mev` calculado uma única vez em `get_tx_metadata` e reutilizado no
  `multiplier` (critério unificado: `int(txid[:8], 16) % 100 < 15`);
- `scripts/test_bip39_pipeline.py` — teste de ponta a ponta do pipeline
  (TX regtest → ZMQ → ingestor → Redis → WebSocket);
- entrypoint robusto do regtest (`bitcoin/entrypoint.sh`): aguarda o RPC com
  retry de 300 s, cria a wallet `miner`, gera 150 blocos e envia 10
  transações ao mempool; nunca encerra o container em falha.

### Corrigido

- fan-out do relay: antes da correção, o `ws_sender` consumia o evento de uma
  única fila (round-robin), então com 2+ clientes cada um recebia apenas uma
  fração dos eventos;
- vazamento de relays: `release_relay()` nunca era chamado; agora o relay é
  encerrado e removido quando o contador de conexões do realm chega a zero;
- `is_halving` → `is_halving_block` no card data do ingestor (campo não
  existia, quebrando o script Lua de reconciliação);
- credenciais RPC dos ingestores: os defaults `${RPC_USER:?...}` exigiam
  variáveis globais que não existem no `.env`; agora cada ingestor usa
  `REGTEST_RPC_USER`/`SIGNET_RPC_USER` com fallback para as credenciais
  declaradas no `bitcoin.conf` (`mempool_regtest`/`mempool_signet`);
- entrypoint do regtest: usava `/usr/bin/bitcoin-cli` (caminho inexistente na
  imagem; o binário está em `/opt/bitcoin-31.1/bin`); agora usa o `PATH`;
- entrypoint do regtest: `exit 1` quando o RPC demorava a subir no cold start
  causava loop de recriação do container; agora o script loga o erro e o
  bitcoind segue rodando;
- frontend: selector `.loader-text` inexistente no DOM (mensagens de falha da
  grade nunca apareciam) → `#tx-loading`;
- frontend: ID duplicado `#tx-loading` (o word bank criava um segundo
  elemento com o mesmo ID) → `#tx-loading-bank`;
- frontend: classes do word bank (`.word-item`, `.word-text`, `.word-fee`,
  `.fee-low/high/golden`) estavam presas em `@media (min-width: 1200px)` →
  movidas para o escopo global;
- frontend: `.hidden` ausente do `pixel.css` (boss-hud, banners e toasts não
  escondiam) → classe utilitária adicionada;
- frontend: `.word-grid` sem centralização → `justify-content: center` +
  `align-content: center`;
- `docker-compose.yaml`: `entrypoint.sh` não era montado no regtest → volume
  `./bitcoin/entrypoint.sh:/entrypoint.sh:ro` + `command: ["/entrypoint.sh"]`.

### Removido

- `frontend/style.css` (105 KB): arquivo morto, não referenciado por
  `index.html`, `game.js` nem `nginx.conf`; o tema ativo é `pixel.css`.
  Removido também do `COPY` do `frontend/Dockerfile`.

## 2026-08-16 — Correções de estabilidade e UX

### Adicionado

- persistência de sessão com `sessionStorage` (`saveSessionState`,
  `loadSessionState`, `clearSessionState`);
- `startSession()` aceita `realmIdOverride` para reconexão automática ao
  mesmo realm;
- verificação de epoch no frontend com reconexão automática ao WebSocket;
- retry RPC com backoff exponencial no ingestor;
- buffer do ingestor aumentado para 50 000 transações;
- font-size adaptativo com `clamp(12px, 2.5vw, 14px)`;
- `.modal-content` considera `safe-area-inset` para dispositivos móveis;

### Corrigido

- sessão restaurada automaticamente ao recarregar página (F5);
- estado salvo em 9 pontos críticos (saldo, hardware, lightning, RBF,
  resultado);
- z-index do `.floating-text` corrigido para 170 (elemento estava oculto
  atrás de outros componentes);
- `.grid-wrapper` com `min-height: min(480px, 80vh)` adaptativo;
- main-layout em 2 colunas para gap 560–760px;
- loop infinito no botão RBF — `btn.onclick = null` adicionado em ambos
  os fluxos (sucesso e erro);

## Não publicado

### Adicionado

- documentação técnica, operacional, de API, auditoria e roadmap;
- páginas HTML de apresentação e referência da API;
- SVGs animados e READMEs por módulo;
- healthcheck da API, testes unitários, CI, CodeQL, Dependabot e GitHub Pages;
- proxy Nginx same-origin, persistência Redis e redes Docker segmentadas;
- catálogo/API/WebSocket/leaderboard multi-rede por `realm_id`;
- ingestores singleton separados para Regtest, Signet e Mainnet;
- profile Mainnet opt-in com pruning configurável e volume próprio;
- heartbeat de nó, status IBD/playable e seletor de rede no frontend;
- lease/fencing Redis por realm e healthcheck vinculado à instância;
- smoke CI de transação ZMQ e mudança de epoch em Regtest;

### Alterado

- validação e atualização atômica do leaderboard;
- cálculo de taxa em sats/vB;
- encerramento de tarefas, logs e tratamento de falhas;
- grade responsiva, seleção retilínea e renderização segura do ranking;
- API removida do ciclo ZMQ/RPC e ingestão separada por processo;
- Redis migrado para canais, estado, epoch e ranking namespaced por realm;
- eventos v2 recebem node/network/realm, epoch, sessão e sequência de origem;
- backlog anterior a bloco é descartado e TXID é deduplicado por epoch.
- contador reconciliado com `getmempoolinfo` sob barreira de epoch.

### Segurança

- credenciais retiradas do bitcoin.conf;
- RPC e Redis deixaram de ser publicados no host;
- sink de XSS persistente removido do frontend principal;
- CORS restringido às origens configuradas.
- credenciais RPC podem ser rotacionadas separadamente por nó.
- autenticação obrigatória no Redis (``REDIS_PASSWORD``) via variável de ambiente.

### Corrigido

- ``load_dotenv()`` removido do ``engine.py`` — variáveis vêm do Docker.
- fallback para ``fee`` direto quando ``fees.base`` está ausente (Bitcoin Core v0.21+).
- dead code ZMQ removido de ``blockchain.py`` — terceiro frame nunca existe.
- double-await frágil substituído por verificação explícita de exceção no shutdown.
- KeyError silencioso corrigido com ``.get()`` + fallback em ``config.py``.
- ``process_interval_seconds <= 0`` rejeitado para evitar busy-loops.
- ``LEADERBOARD_KEY`` dead code removido de ``main.py``.
- log bomb ``warning`` → ``debug`` para eventos fora do contrato.
- WebSocket receiver com timeout de 5 minutos para evitar conexões órfãs.
- heartbeat periódico no WebSocket sender para detectar inatividade.
- RPC movido para fora do ``epoch_lock`` em ``update_status()``, ``process_transaction()`` e ``handle_block()``.
- ``RuntimeError`` de lease loss tratado explicitamente em ``heartbeat_loop`` e ``process_transactions()``.
- ``FileNotFoundError`` tratado com mensagem clara no healthcheck.
- ``AttributeError`` removido do ``except`` em ``get_network_definition``.
- docstring corrigida em ``__init__.py`` ("Mempool Miner" ao invés de "Search").
- ``validate_realm_id()`` renomeado para ``validate_id_format()`` com alias de compatibilidade.
- race condition documentada na docstring de ``process_transaction()``.
- ``conftest.py`` criado com fixtures compartilhadas e ``autouse=True``.
- ``os.environ.setdefault`` removido dos arquivos de teste.
- ``.dockerignore`` criado para excluir testes, docs, IDEs da imagem Docker.
- ``pytest-cov`` adicionado ao CI com threshold mínimo de 60%.
- ``test_blockchain.py``, ``test_storage.py``, ``test_healthcheck.py`` criados.
- ``create_mock_ingestor()`` adicionada — factory documentada para testes.
- ``Spacebar`` removido do ``game.js`` — ``event.key === ' '`` já cobre espaço.
- atributos redundantes removidos de ``GameEngine`` — acessa ``self.config`` diretamente.
- ``MAX_SCORE`` documentado — INT32_MAX para compatibilidade com Redis Sorted Sets.
- ``Sunset`` headers adicionados nos endpoints legados (``/api/health``, ``/api/leaderboard``).
- ``hardwarePrices[0] = 0`` removido — array alinhado com ``hardwareLevel`` (índice 1-based).
- ``scheduleForSession()`` usado em ``showFloatingText`` ao invés de ``setTimeout``.
- ``clearTimeout(catalogRetryTimeout)`` adicionado em ``teardownSession()``.
