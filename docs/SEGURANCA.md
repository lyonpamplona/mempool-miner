# Segurança da aplicação

Esta página descreve as fronteiras de confiança e os controles técnicos do
Mempool Miner. Para o inventário completo, severidades e evidências, consulte a
[auditoria](AUDITORIA.md) e o [roadmap](ROADMAP.md).

## Modelo de ameaça

| Fronteira | Dado não confiável | Controle atual | Limite conhecido |
|---|---|---|---|
| navegador → REST | nickname e score | Pydantic, limite de tamanho e `ZADD GT` | score ainda é calculado pelo cliente |
| navegador → WebSocket | conexão e mensagens recebidas | proxy same-origin e validação no cliente | sem autenticação, Origin explícita ou rate limit |
| Bitcoin Core → backend | frames ZMQ e respostas RPC | validação multipart, timeouts e logs | sem deduplicação/sequence durável |
| backend → navegador | ranking e eventos | contratos JSON e `textContent` | sem versionamento formal do protocolo |
| host → serviços de dados | RPC e Redis | redes internas e nenhuma porta publicada | segredo RPC ainda vem do ambiente |

## Controles implementados

- `.env` ignorado pelo Git e exemplo sem credencial real;
- RPC, ZMQ, Redis e FastAPI sem publicação direta no host;
- Nginx como única origem local em `127.0.0.1:8010`;
- um worker de ingestão, evitando duplicação de eventos;
- username normalizado e validado; score limitado;
- conteúdo externo inserido com `textContent`, sem HTML interpretado;
- Redis persistente, healthchecks e containers com `no-new-privileges`;
- CI configurada com lint, testes, auditoria de dependências e smoke da stack.

## Antes de expor na internet

1. mova pontuação, compras e sessão para um motor autoritativo no servidor;
2. adicione autenticação, rate limiting e validação de Origin no WebSocket;
3. use TLS, cabeçalhos de segurança e uma CSP sem handlers inline;
4. substitua senha RPC em argumento por `rpcauth`/secret manager e rotacione a
   credencial local;
5. fixe imagens e GitHub Actions por digest/SHA, gere lock e SBOM;
6. execute testes de integração, carga, backup e restauração.

## Comunicação responsável

Não publique credenciais, dados do nó ou provas de conceito exploráveis em uma
issue. Depois de configurar o remoto GitHub, use um *private vulnerability
report* e informe commit afetado, impacto, pré-condições e reprodução mínima com
logs sanitizados.

O ranking atual não comprova saldo, mineração ou propriedade de Bitcoin. Toda a
economia exibida pelo jogo é simulada.
