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
| <img src="docs/assets/backend.svg" width="34" alt=""> Ingestores + FastAPI | Um ingestor singleton por rede; API REST/WebSocket desacoplada | [backend/README.md](backend/README.md) |
| <img src="docs/assets/redis.svg" width="34" alt=""> Redis | Eventos, estado e leaderboard isolados por realm | [Arquitetura](docs/ARQUITETURA.md) |
| <img src="docs/assets/frontend.svg" width="34" alt=""> Frontend | Grade, cronômetro, loja simulada e interface do jogador | [frontend/README.md](frontend/README.md) |

~~~mermaid
flowchart LR
    R[Core Regtest] --> IR[Ingestor Regtest]
    S[Core Signet] --> IS[Ingestor Signet]
    M[Core Mainnet pruned<br>profile opcional] -.-> IM[Ingestor Mainnet]
    IR --> Redis[(Redis por realm)]
    IS --> Redis
    IM -.-> Redis
    Redis --> API[FastAPI]
    API -->|/ws/v1/game/realm| UI[Frontend]
    UI -->|REST por realm| API
~~~

## Início rápido

Pré-requisitos: Docker Engine ou Docker Desktop com Compose 2.33.1 ou superior,
cerca de 4 GB de RAM livres para Regtest + Signet e a porta local 8010
disponível. O portal opcional usa a porta 8020. A versão mínima é necessária
para selecionar deterministicamente o gateway P2P dos nós públicos.

No PowerShell:

    Copy-Item .env.example .env
    # Edite .env e substitua as três senhas RPC de exemplo.
    docker compose config --quiet
    docker compose up -d --build
    docker compose ps

O comando padrão inicia Regtest e Signet. Mainnet permanece desativada. Para
incluir o nó Mainnet podado e seu ingestor:

    docker compose --profile mainnet config --quiet
    docker compose --profile mainnet up -d --build

O alvo de pruning Mainnet padrão é 10 GiB de blocos (`MAINNET_PRUNE_MIB=10240`).
Chainstate e índices exigem espaço adicional, e o IBD ainda baixa e valida a
cadeia antes de descartar blocos antigos.

O jogo mobile-first/PWA fica disponível em:

- jogo: http://localhost:8010

Documentação e apresentação não são copiadas para a imagem do jogo. Para subir
o portal público sanitizado em um serviço separado:

    docker compose --profile docs up -d --build docs

- documentação: http://localhost:8020/
- página pública da API: http://localhost:8020/api/
- apresentação: http://localhost:8020/apresentacao/

Swagger e OpenAPI bruto ficam desabilitados por padrão e não são publicados por
nenhum dos proxies.

Escolha a rede no diálogo inicial. Uma rede em IBD aparece como
"sincronizando" e não inicia partidas. Em Regtest, gere transações conforme o
[TUTORIAL.md](docs/TUTORIAL.md).

Em um navegador compatível, use o botão **Instalar app**. O service worker
mantém apenas o shell estático; API, WebSocket, health e leaderboard nunca são
armazenados no cache offline.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Portal técnico](docs/README.md) | Separação entre fontes Markdown e publicação sanitizada |
| [Arquitetura](docs/ARQUITETURA.md) | Camadas, decisões, limites e implantação |
| [Multi-rede](docs/MULTI_REDE.md) | Relatório Regtest/Signet/Mainnet, migração e aceite |
| [Fluxos](docs/FLUXOS.md) | Inicialização, transação, bloco, jogo e ranking |
| [Mecânicas](docs/MECANICAS.md) | Todas as mecânicas por aba: boss, eventos globais, RBF, conquistas, missões, season, staking, energia, crates, sprint, decoder, skill tree, social |
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

## Mudanças recentes (20/08/2026)

Quatro fases de correção foram aplicadas em 20/08/2026 após auditoria completa
(backend, frontend e infraestrutura):

- **Fan-out do relay** — `EventRelay` persistente replica cada evento PubSub
  para todos os clientes WebSocket conectados (antes, um único cliente
  recebia cada evento); o relay é liberado quando o último cliente
  desconecta.
- **Pipeline BIP39** — `txid` completo no payload público; eventos globais
  (`fee_spike`, `golden_rush`, `mempool_flood`, `lightning_storm`) aplicados
  no ingestor; `is_mev` unificado em `get_tx_metadata`.
- **Frontend** — seletores corrigidos (`.loader-text` → `#tx-loading`), ID
  duplicado resolvido, classes do word bank movidas para o escopo global,
  `.hidden` adicionada, grade centralizada; `style.css` morto removido.
- **Infraestrutura** — entrypoint do regtest robusto (caminho correto do
  `bitcoin-cli`, sem crash no cold start, wallet + 150 blocos + 10 TXs
  automáticas); credenciais RPC dos ingestores alinhadas com o
  `bitcoin.conf`.

Leia [CHANGELOG.md](CHANGELOG.md) para o histórico completo.

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
