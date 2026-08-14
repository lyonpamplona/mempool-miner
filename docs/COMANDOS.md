# Comandos

Runbook para desenvolvimento e operação local.

## Configuração

| Ação | PowerShell | Bash |
|---|---|---|
| criar .env | Copy-Item .env.example .env | cp .env.example .env |
| validar Compose | docker compose config --quiet | igual |
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

Atualização consciente de imagens:

    docker compose pull
    docker compose build --pull
    docker compose up -d

## Logs

    docker compose logs --tail 200 backend
    docker compose logs -f backend
    docker compose logs -f bitcoind redis
    docker compose events

## Saúde

    curl http://localhost:8010/api/health
    docker compose exec redis redis-cli ping
    docker compose exec bitcoind bitcoin-cli -regtest getblockchaininfo
    docker compose exec bitcoind bitcoin-cli -regtest getmempoolinfo

No PowerShell, Invoke-RestMethod evita o alias histórico de curl:

    Invoke-RestMethod http://localhost:8010/api/health
    Invoke-RestMethod http://localhost:8010/api/leaderboard

## Leaderboard

PowerShell:

    $body = @{ username = "Miner_42"; score = 1200 } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri http://localhost:8010/api/leaderboard -ContentType application/json -Body $body

Bash:

    curl -X POST http://localhost:8010/api/leaderboard \
      -H "Content-Type: application/json" \
      -d '{"username":"Miner_42","score":1200}'

## Bitcoin regtest

    docker compose exec bitcoind bitcoin-cli -regtest createwallet miner
    docker compose exec bitcoind bitcoin-cli -regtest -rpcwallet=miner getnewaddress
    docker compose exec bitcoind bitcoin-cli -regtest generatetoaddress 101 ENDERECO
    docker compose exec bitcoind bitcoin-cli -regtest -rpcwallet=miner sendtoaddress ENDERECO 0.001
    docker compose exec bitcoind bitcoin-cli -regtest getrawmempool
    docker compose exec bitcoind bitcoin-cli -regtest generatetoaddress 1 ENDERECO

## Redis

    docker compose exec redis redis-cli ZREVRANGE global_leaderboard 0 9 WITHSCORES
    docker compose exec redis redis-cli GET mempool_count
    docker compose exec redis redis-cli PUBSUB NUMSUB game_events
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
    docker volume rm mempool-miner_bitcoin_data
    docker volume rm mempool-miner_redis_data

Nunca os inclua automaticamente em scripts de CI ou setup.
