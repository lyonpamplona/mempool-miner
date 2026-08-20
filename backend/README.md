<p align="center"><img src="../docs/assets/backend.svg" width="96" alt="Ícone animado do backend"></p>

# Backend

Imagem Python compartilhada por dois papéis: API HTTP/WebSocket e ingestor
singleton de um realm Bitcoin.

## Responsabilidades

- executar um ingestor independente para Regtest, Signet ou Mainnet;
- consumir tópicos ZMQ rawtx e hashblock com origem/sequence explícitas;
- calcular TXID de uma transação serializada;
- converter 128 bits do TXID em uma palavra BIP39;
- consultar vsize e taxa pelo JSON-RPC do Bitcoin Core;
- publicar eventos, heartbeat e epoch em namespace Redis por realm;
- reconciliar periodicamente a mempool e impedir publicadores concorrentes do
  mesmo realm por lease Redis;
- entregar catálogo e eventos isolados por WebSocket;
- armazenar e consultar um Top 10 por realm.

## Estrutura

| Arquivo | Papel |
|---|---|
| app/main.py | API REST/WebSocket e catálogo; não acessa RPC/ZMQ |
| app/ingestor.py | Fila, lease, epoch, dedupe, reconciliação e publicação |
| app/ingestor_healthcheck.py | valida heartbeat recente do processo |
| app/config.py | Catálogo público e configuração service-local |
| app/events.py | Notices ZMQ e envelope público v2 |
| app/storage.py | Chaves/canais por realm e migração legada |
| app/engine.py | RPC, BIP39, vsize e taxa em sats/vB |
| app/blockchain.py | Subscriber ZMQ assíncrono |
| tests/ | Contratos e regras unitárias |
| requirements.txt | Dependências de runtime |

## Execução isolada

Redis e Bitcoin Core precisam estar acessíveis.

    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r backend/requirements-dev.txt
    $env:PYTHONPATH = "backend"
    uvicorn app.main:app --host 127.0.0.1 --port 8000

Um ingestor isolado requer Redis, RPC e ZMQ configurados:

    python -m app.ingestor

As variáveis obrigatórias e opcionais estão em
[CONFIGURACAO.md](../docs/CONFIGURACAO.md). O caminho recomendado continua sendo
Docker Compose, pois ele fornece as dependências e as redes corretas.

## Qualidade

    python -m compileall -q backend/app
    ruff check backend
    pytest -q

Detalhes dos endpoints e eventos: [API.md](../docs/API.md).
