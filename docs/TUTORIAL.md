# Tutorial de uso

## 1. Preparar

Instale Docker Desktop no Windows ou Docker Engine + Compose 2.33.1 ou superior
no Linux.
Confirme:

    docker --version
    docker compose version

Copie a configuração:

PowerShell:

    Copy-Item .env.example .env

Bash:

    cp .env.example .env

Edite `.env` e troque `REGTEST_RPC_PASSWORD`, `SIGNET_RPC_PASSWORD` e
`MAINNET_RPC_PASSWORD`. Para o primeiro teste, mantenha:

    DEFAULT_REALM_ID=regtest

## 2. Validar e iniciar

    docker compose config --quiet
    docker compose --profile mainnet config --quiet
    docker compose up -d --build
    docker compose ps

Espere todos os serviços ficarem healthy. Acompanhe:

    docker compose logs -f bitcoin-regtest bitcoin-signet ingestor-regtest ingestor-signet redis backend frontend

## 3. Abrir o jogo

Acesse http://localhost:8010, escolha Regtest, informe um nickname de até 12
caracteres e conecte. Signet pode aparecer sincronizando; Mainnet fica
desativada no catálogo até seu profile ser iniciado. Em Regtest a mempool começa
vazia, portanto gere atividade.

Em navegadores compatíveis, o botão **Instalar app** adiciona o PWA ao sistema.
O modo offline abre somente o shell e informa que uma conexão é necessária; ele
não reutiliza eventos, rankings nem respostas da API em cache.

## 4. Criar transações em regtest

O entrypoint do regtest (`bitcoin/entrypoint.sh`) já executa automaticamente:
cria a wallet `miner`, gera 150 blocos e envia 10 transações ao mempool. Na
maioria dos casos a grade já começa a receber palavras assim que o jogo
conecta.

Se a mempool estiver vazia (ex.: o RPC não ficou pronto a tempo no cold
start), execute manualmente:

Crie (ou carregue) uma carteira de laboratório:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" createwallet miner'

Se a carteira já existir, carregue-a:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" loadwallet miner'

Obtenha um endereço:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcwallet=miner getnewaddress'

Copie o endereço retornado e amadureça saldo de teste:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" generatetoaddress 101 ENDERECO'

Gere pelo menos seis transações. Para cada uma, crie outro endereço e envie uma
quantidade fictícia:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcwallet=miner getnewaddress'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcwallet=miner sendtoaddress ENDERECO 0.001'

Repita até o browser receber seis palavras únicas. Colisões são possíveis porque
cada TXID usa apenas a primeira palavra de uma frase BIP39.

## 5. Jogar

1. Aguarde a grade aparecer.
2. Arraste horizontal, vertical ou diagonalmente sobre uma palavra.
3. A direção fica fixa após a segunda célula.
4. Encontre todas antes do cronômetro.
5. Use sats fictícios para dica/hardware.
6. Ative Lightning somente entre rodadas.

Para simular um bloco real vencendo a rodada, gere um bloco enquanto joga:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" generatetoaddress 1 ENDERECO'

## 6. Inspecionar

- catálogo: http://localhost:8010/api/v1/networks
- ranking Regtest: http://localhost:8010/api/v1/networks/regtest/leaderboard
- healthcheck: http://localhost:8010/api/v1/health/live

A documentação pública é servida pelo mesmo nginx do jogo, em `/docs/`:

- portal: http://localhost:8010/docs/
- API visual sanitizada: http://localhost:8010/docs/api/
- apresentação: http://localhost:8010/docs/apresentacao/

Swagger e OpenAPI bruto não são publicados pelos proxies e ficam desabilitados
por padrão no backend.

## 7. Encerrar

Preservando volumes:

    docker compose down

Remover volumes apaga as três blockchains locais, carteira Regtest e ranking.
Use somente se essa perda for intencional:

    docker compose down --volumes

## Mainnet opcional

Antes de habilitar, revise disco, RAM e banda. O nó é podado, mas ainda executa
o IBD completo:

    docker compose --profile mainnet up -d bitcoin-mainnet ingestor-mainnet
    docker compose --profile mainnet logs -f bitcoin-mainnet ingestor-mainnet

O jogo só habilita Mainnet quando `playable=true`. Para desligar sem afetar as
outras redes:

    docker compose --profile mainnet stop ingestor-mainnet bitcoin-mainnet

## O que é real e o que é simulado

| Recurso | Natureza |
|---|---|
| evento ZMQ, TXID, vsize, taxa e hash de bloco | integração real com o nó |
| palavra BIP39 | derivação determinística para o jogo |
| saldo em sats, carteira fria, hashrate e reward | simulação local |
| hardware e dica | mecânica local |
| Lightning/zero-conf | simulação visual |
| leaderboard | Redis real, score não autoritativo |
