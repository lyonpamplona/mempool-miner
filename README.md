<p align="center">
  <img src="docs/assets/mempool-miner-banner.svg" alt="Mempool Miner — eventos Bitcoin transformados em Proof of Search" width="100%">
</p>

# Mempool Miner

Jogo educacional em tempo real que transforma notificações de transações do
Bitcoin Core em palavras BIP39 dentro de uma grade. A stack combina FastAPI,
ZMQ, Redis Pub/Sub, WebSocket, Nginx e JavaScript sem framework.

> O projeto não minera Bitcoin, não abre canais Lightning e não movimenta
> fundos. Sats, hashrate, carteira, recompensas e modo L2 são mecânicas
> simuladas.

## Visão rápida

| Componente | Responsabilidade | Documento |
|---|---|---|
| <img src="docs/assets/bitcoin.svg" width="34" alt=""> Bitcoin Core | Publica transações e blocos via ZMQ; fornece metadados via RPC | [bitcoin/README.md](bitcoin/README.md) |
| <img src="docs/assets/backend.svg" width="34" alt=""> FastAPI | Ingestão, transformação BIP39, API REST e gateway WebSocket | [backend/README.md](backend/README.md) |
| <img src="docs/assets/redis.svg" width="34" alt=""> Redis | Pub/Sub, contador observado e Top 10 | [Arquitetura](docs/ARQUITETURA.md) |
| <img src="docs/assets/frontend.svg" width="34" alt=""> Frontend | Grade, cronômetro, loja simulada e interface do jogador | [frontend/README.md](frontend/README.md) |

~~~mermaid
flowchart LR
    BTC[Bitcoin Core] -->|rawtx / hashblock| ZMQ[Listener ZMQ]
    ZMQ --> Queue[Fila limitada]
    Queue --> Engine[GameEngine + RPC]
    Engine --> Redis[(Redis)]
    Redis -->|Pub/Sub| API[FastAPI / WebSocket]
    API -->|/ws/game| UI[Frontend]
    UI -->|REST| Rank[Leaderboard]
    Rank --> Redis
~~~

## Início rápido

Pré-requisitos: Docker Engine ou Docker Desktop com Compose v2, pelo menos
2 GB de RAM livres e portas locais 8010 disponíveis.

No PowerShell:

    Copy-Item .env.example .env
    # Edite .env e substitua RPC_PASSWORD por uma senha aleatória.
    docker compose config --quiet
    docker compose up -d --build
    docker compose ps

Abra:

- jogo: http://localhost:8010
- apresentação: http://localhost:8010/apresentacao.html
- documentação: http://localhost:8010/docs/
- página técnica da API: http://localhost:8010/docs/api.html
- Swagger da instância: http://localhost:8010/backend-docs

Em regtest, o jogo precisa de transações. Consulte o roteiro de geração em
[TUTORIAL.md](docs/TUTORIAL.md).

## Documentação

| Documento | Conteúdo |
|---|---|
| [Portal técnico](docs/README.md) | Índice completo e páginas HTML |
| [Arquitetura](docs/ARQUITETURA.md) | Camadas, decisões, limites e implantação |
| [Fluxos](docs/FLUXOS.md) | Inicialização, transação, bloco, jogo e ranking |
| [Módulos](docs/MODULOS.md) | Arquivos, classes, funções e responsabilidades |
| [API](docs/API.md) | REST, WebSocket, esquemas e erros |
| [Configuração](docs/CONFIGURACAO.md) | Ambiente, redes e parâmetros |
| [Dependências](docs/DEPENDENCIAS.md) | Runtime, bibliotecas e estratégia de atualização |
| [Tutorial](docs/TUTORIAL.md) | Uso do zero ao primeiro bloco |
| [Comandos](docs/COMANDOS.md) | Runbook operacional |
| [Segurança técnica](docs/SEGURANCA.md) | Fronteiras de confiança e checklist de exposição |
| [Deployment](docs/DEPLOYMENT.md) | Perfis, proxy, backup e produção |
| [Auditoria](docs/AUDITORIA.md) | Revisão completa, achados e correções aplicadas |
| [Roadmap](docs/ROADMAP.md) | Plano priorizado para riscos remanescentes |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Diagnóstico dos erros mais comuns |
| [Apresentação](guia-apresentacao.html) | Página visual completa do projeto |

## Segurança e estado atual

A entrega corrige a exposição direta de Redis/RPC, o XSS persistente no
frontend principal, a duplicação causada por quatro workers, a corrida não
atômica do ranking e falhas de estado da grade. O risco estrutural mais
importante permanece: a pontuação ainda é calculada pelo navegador e, portanto,
pode ser forjada. Não use o leaderboard como ativo financeiro ou prova de
trabalho.

Leia [SECURITY.md](SECURITY.md) antes de publicar e rotacione a credencial RPC
local se o projeto já tiver sido compartilhado.

## Desenvolvimento

    python -m compileall -q backend/app
    node --check frontend/game.js
    pytest -q

Contribuições seguem [CONTRIBUTING.md](CONTRIBUTING.md). O histórico de mudanças
está em [CHANGELOG.md](CHANGELOG.md).

## Licença

Uma licença ainda não foi escolhida. Até que o autor adicione um arquivo
LICENSE, nenhum direito de redistribuição deve ser presumido.
