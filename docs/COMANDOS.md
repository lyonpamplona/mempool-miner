# Comandos

Runbook para desenvolvimento e operação local.

## Configuração

| Ação | PowerShell | Bash |
|---|---|---|
| criar .env | Copy-Item .env.example .env | cp .env.example .env |
| validar Compose | docker compose config --quiet | igual |
| validar com Mainnet | docker compose --profile mainnet config --quiet | igual |
| mostrar configuração | docker compose config | igual |

Nunca cole a saída completa de docker compose config em tickets: ela pode
conter a credencial RPC resolvida.

## Ciclo de vida

    docker compose build
    docker compose up -d
    docker compose up -d --build
    docker compose ps
    docker compose stop
    docker compose start
    docker compose restart backend
    docker compose down

Mainnet é opt-in:

    docker compose --profile mainnet up -d bitcoin-mainnet ingestor-mainnet
    docker compose --profile mainnet logs -f bitcoin-mainnet ingestor-mainnet
    docker compose --profile mainnet stop ingestor-mainnet bitcoin-mainnet

Atualização consciente de imagens:

    docker compose pull
    docker compose build --pull
    docker compose up -d

## Logs

    docker compose logs --tail 200 backend
    docker compose logs -f backend
    docker compose logs -f bitcoin-regtest bitcoin-signet ingestor-regtest ingestor-signet redis
    docker compose events

## Saúde

    curl http://localhost:8010/api/v1/health/live
    curl http://localhost:8010/api/v1/networks
    docker compose exec redis redis-cli ping
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getmempoolinfo'
    docker compose exec bitcoin-signet sh -lc 'bitcoin-cli -signet -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'

No PowerShell, Invoke-RestMethod evita o alias histórico de curl:

    Invoke-RestMethod http://localhost:8010/api/v1/health/live
    Invoke-RestMethod http://localhost:8010/api/v1/networks/regtest/leaderboard

## Leaderboard

PowerShell:

    $body = @{ username = "Miner_42"; score = 1200 } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri http://localhost:8010/api/v1/networks/regtest/leaderboard -ContentType application/json -Body $body

Bash:

    curl -X POST http://localhost:8010/api/v1/networks/regtest/leaderboard \
      -H "Content-Type: application/json" \
      -d '{"username":"Miner_42","score":1200}'

## Bitcoin regtest

O entrypoint (`bitcoin/entrypoint.sh`) já cria a wallet `miner`, gera 150
blocos e envia 10 transações ao mempool automaticamente. Os comandos abaixo
servem para inspeção e para recriar a atividade manualmente:

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" createwallet miner'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcwallet=miner getnewaddress'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" generatetoaddress 101 ENDERECO'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" -rpcwallet=miner sendtoaddress ENDERECO 0.001'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getrawmempool'
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" generatetoaddress 1 ENDERECO'

## Signet e Mainnet

    docker compose exec bitcoin-signet sh -lc 'bitcoin-cli -signet -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'
    docker compose --profile mainnet exec bitcoin-mainnet sh -lc 'bitcoin-cli -chain=main -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'

No retorno, observe `initialblockdownload`, `verificationprogress`, `pruned` e
`pruneheight`. Mainnet só fica selecionável no jogo após sair do IBD.

## Redis

    docker compose exec redis redis-cli ZREVRANGE "mempool_miner:v2:{regtest}:leaderboard" 0 9 WITHSCORES
    docker compose exec redis redis-cli GET "mempool_miner:v2:{regtest}:mempool_count"
    docker compose exec redis redis-cli PUBSUB NUMSUB "mempool_miner:v2:{regtest}:events"
    docker compose exec redis redis-cli BGSAVE

Não execute FLUSHALL fora de um ambiente descartável.

## Qualidade

Com dependências de desenvolvimento instaladas:

    python -m compileall -q backend/app
    ruff check .
    ruff format --check .
    pytest -q
    node --check frontend/game.js
    node --check docs/api-page.js
    python scripts/validate_docs.py

Auditoria:

    python -m pip_audit -r backend/requirements.txt

## Git

    git status --short
    git diff --check
    git add .
    git diff --cached --stat
    git diff --cached
    git commit -m "docs: documenta arquitetura e operação"

Antes de git add, confirme:

    git check-ignore -v .env
    git ls-files .env

O segundo comando deve retornar vazio.

## Backup

Redis:

    docker compose exec redis redis-cli BGSAVE

Bitcoin e Redis usam volumes nomeados. Planeje backup com a stack parada ou
ferramenta consistente com cada banco; copiar arquivos em escrita pode gerar
snapshot inconsistente.

## Comandos destrutivos

Os comandos abaixo apagam dados e exigem confirmação humana do alvo:

    docker compose down --volumes

Evite `docker volume rm` manual: resolva primeiro os nomes com
`docker volume ls` e mantenha backup. Nunca inclua remoção automaticamente em
scripts de setup. A CI só usa `down --volumes` no projeto efêmero criado por ela.
