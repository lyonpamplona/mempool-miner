<p align="center"><img src="../docs/assets/backend.svg" width="96" alt="Ícone animado do backend"></p>

# Backend

Serviço FastAPI responsável pela ponte entre Bitcoin Core, Redis e os
navegadores.

## Responsabilidades

- consumir tópicos ZMQ rawtx e hashblock;
- calcular TXID de uma transação serializada;
- converter 128 bits do TXID em uma palavra BIP39;
- consultar vsize e taxa pelo JSON-RPC do Bitcoin Core;
- publicar eventos no Redis;
- entregar eventos aos clientes por WebSocket;
- armazenar e consultar o Top 10.

## Estrutura

| Arquivo | Papel |
|---|---|
| app/main.py | Ciclo de vida, fila, REST, WebSocket e Redis |
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

As variáveis obrigatórias e opcionais estão em
[CONFIGURACAO.md](../docs/CONFIGURACAO.md). O caminho recomendado continua sendo
Docker Compose, pois ele fornece as dependências e as redes corretas.

## Qualidade

    python -m compileall -q backend/app
    ruff check backend
    pytest -q

Detalhes dos endpoints e eventos: [API.md](../docs/API.md).
