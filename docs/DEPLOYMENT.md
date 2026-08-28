# Implantação

## Perfil atual

O Compose entregue é um ambiente local endurecido, não uma topologia pronta
para dinheiro real. O Nginx do jogo publica somente `127.0.0.1:8010` e serve a
documentação sanitizada em `/docs/` (mesma origem).

## Checklist antes de expor

- [ ] TLS e HSTS em proxy de borda;
- [ ] identidade do jogador e score calculado no servidor;
- [ ] rate limiting REST/WebSocket;
- [x] validação de Host/Origin no WebSocket;
- [ ] rpcauth/secret manager e rotação;
- [ ] subnet RPC exata;
- [ ] lock com hashes, SBOM e imagens por digest;
- [ ] Nginx não-root, capabilities mínimas e filesystem somente leitura;
- [ ] rotação de logs e limites de recursos verificados no runtime;
- [ ] backup/restauração testados;
- [ ] observabilidade e alertas;
- [x] ingestão singleton separada da API por realm;
- [x] jogo/PWA e portal em imagens/document roots separados;
- [x] Swagger/OpenAPI bruto fora dos proxies públicos;
- [ ] política de privacidade e licença definidas.

## Escala

Os serviços `ingestor-*` não devem ser escalados como réplicas do mesmo realm.
Uma lease Redis com token e TTL recusa um segundo publicador acidental, mas não
implementa HA nem agrega dois nós. A API já não assina ZMQ e pode ser escalada
após introduzir fan-out WebSocket/limites de conexão compatíveis. Pub/Sub ainda
não tem replay; Redis Streams permanece como próxima etapa para failover e
recuperação.

O entrypoint do ingestor converte o `SIGTERM` enviado pelo Docker em cancelamento
ordenado, grava `stopped` e libera a lease atomicamente. O Compose reserva 30 s
de graça antes de forçar o encerramento.

## TLS

O frontend já usa URLs same-origin e escolhe ws/wss conforme o protocolo.
Termine TLS antes do Nginx interno ou substitua-o pelo proxy corporativo,
preservando /api, /ws, Upgrade e timeouts.

Service workers exigem contexto seguro fora de `localhost`/loopback. Em domínio
real, publique o jogo somente por HTTPS e preserve o escopo do manifest na raiz
do PWA. API, WebSocket e leaderboard não devem entrar no cache da borda nem do
service worker.

## Portal de documentação

O portal não é dependência do jogo:

    docker compose --profile docs up -d --build docs

Sua imagem recebe apenas `index.html`, a página visual da API, a apresentação,
CSS e SVGs públicos. Markdown, relatórios locais, protótipos, `.env`, Swagger e
OpenAPI não entram no artefato. O workflow Pages monta a mesma allowlist em uma
pasta temporária antes da publicação.

## Mainnet

Mainnet aumenta tráfego, disco, tempo de sincronização e consequências
operacionais. O `up` padrão não a cria. Para validar e iniciar explicitamente:

    docker compose --profile mainnet config --quiet
    docker compose --profile mainnet up -d bitcoin-mainnet ingestor-mainnet

O nó usa `prune=10240` por padrão, `txindex=0`, wallet desabilitada e volume
próprio. Antes de habilitar:

1. use volume novo;
2. revise `MAINNET_PRUNE_MIB`, disco, RAM e banda de IBD;
3. teste a taxa da fila e o contador de descartes;
4. confirme que nenhum RPC/ZMQ está publicado;
5. migre senha em argumentos para `rpcauth`/secret;
6. substitua a imagem de laboratório por cadeia de fornecimento verificada.

Pruning limita retenção de blocos; não evita baixar e validar a cadeia inteira,
nem contabiliza sozinho chainstate e índices.

## Rollout da API v2

Backend e frontend deste repositório devem ser implantados juntos. A API mantém
aliases para clientes antigos, mas o frontend novo exige o catálogo v2. Ordem:

1. subir Redis, nós e ingestores;
2. confirmar `/api/v1/networks` e heartbeat;
3. promover API e frontend no mesmo rollout;
4. preservar aliases por pelo menos uma versão;
5. remover aliases somente após observar zero clientes antigos.

## Rollback

Imagens e configuração devem ser versionadas juntas. Preserve o volume, reverta
o commit, restaure a tag anterior e suba. Downgrade de Bitcoin Core pode não
aceitar dados produzidos por versão nova; valide em cópia antes.
