# Segurança da aplicação

Esta página descreve as fronteiras de confiança e os controles técnicos do
Mempool Miner. Para o inventário completo, severidades e evidências, consulte a
[auditoria](AUDITORIA.md) e o [roadmap](ROADMAP.md).

## Modelo de ameaça

| Fronteira | Dado não confiável | Controle atual | Limite conhecido |
|---|---|---|---|
| navegador → REST | nickname e score | Pydantic, limite de tamanho e `ZADD GT` | score ainda é calculado pelo cliente |
| navegador → WebSocket | conexão e mensagens recebidas | proxy same-origin, Host/Origin allowlist e validação do realm | sem autenticação ou rate limit |
| Bitcoin Core → ingestor | frames ZMQ e respostas RPC | rede exclusiva, origem/sequence/epoch, dedupe e reconciliação periódica | sem replay/reconciliação durável da lista completa |
| backend → navegador | ranking e eventos | contratos JSON e `textContent` | sem versionamento formal do protocolo |
| host → serviços de dados | RPC e Redis | redes internas e nenhuma porta publicada | segredo RPC ainda vem do ambiente |

## Controles implementados

- `.env` ignorado pelo Git e exemplo sem credencial real;
- RPC, ZMQ, Redis e FastAPI sem publicação direta no host;
- Nginx do jogo como única origem de runtime em `127.0.0.1:8010`;
- portal sanitizado em imagem/profile próprios, com bind opcional em `127.0.0.1:8020`;
- Swagger/OpenAPI bruto desabilitados e ausentes dos proxies públicos;
- catálogo e eventos públicos sem identificador físico, topologia ou métricas operacionais;
- CSP, políticas de browser e bloqueio de arquivos ocultos no Nginx;
- service worker restrito ao shell estático, com bypass de API, WebSocket, health e ranking;
- um ingestor singleton por realm, separado da API e protegido por lease Redis;
- namespaces, volumes e redes de controle independentes por realm;
- username normalizado e validado; score limitado;
- conteúdo externo inserido com `textContent`, sem HTML interpretado;
- Redis persistente, healthchecks e containers com `no-new-privileges`;
- CI configurada com lint, testes, auditoria de dependências e smoke da stack.

## Antes de expor na internet

1. mova pontuação, compras e sessão para um motor autoritativo no servidor;
2. adicione autenticação e rate limiting REST/WebSocket;
3. termine TLS na borda e teste os cabeçalhos/CSP em todos os navegadores-alvo;
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
