# Dependências

## Runtime

| Tecnologia | Versão configurada | Uso |
|---|---:|---|
| Python | 3.11.13 | backend |
| FastAPI | 0.141.1 | REST/WebSocket/OpenAPI |
| Uvicorn | 0.24.0 | servidor ASGI |
| websockets | 12.0 | protocolo WebSocket |
| PyZMQ | 27.1.0 | subscriber Bitcoin |
| python-dotenv | 1.2.2 | .env em execução local |
| mnemonic | 0.20 | dicionário BIP39 |
| redis-py | 5.0.1 | Pub/Sub e Sorted Sets |
| HTTPX | 0.25.1 | JSON-RPC assíncrono |
| Pydantic | 2.13.4 | validação de contratos |
| Redis Server | 7.4 | persistência e fan-out |
| Nginx | 1.28 | estáticos e proxy |
| Bitcoin Core | 31.1 | RPC e ZMQ |

As versões Python estão em backend/requirements.txt. pytest, pytest-asyncio e
Ruff são dependências de desenvolvimento.

## Dependências indiretas

O arquivo atual fixa apenas pacotes diretos. O resolvedor escolhe Starlette,
AnyIO, httpcore e outras transitivas durante o build. Isso significa que dois
builds em datas diferentes podem divergir.

Próximo passo recomendado:

1. gerar lock para Python 3.11 com hashes;
2. revisar licenças;
3. produzir SBOM CycloneDX;
4. executar pip-audit no lock;
5. promover atualizações por PR do Dependabot.

## Auditoria de segurança

FastAPI 0.104.1, presente no inventário inicial, era afetado por
[CVE-2024-24762](https://nvd.nist.gov/vuln/detail/CVE-2024-24762) em fluxos de
form data. O projeto usa JSON e não instalava python-multipart, mas a versão foi
atualizada para remover o componente sinalizado.

python-dotenv 1.0.0 também foi identificado pelo pip-audit como afetado por
[CVE-2026-28684](https://github.com/advisories/GHSA-mf9w-mj56-hr94), uma falha
local ao reescrever arquivos por links simbólicos. Embora o backend apenas leia
.env, o pacote foi atualizado para 1.2.2.

A revisão de uma versão direta não substitui uma auditoria do ambiente
resolvido. O workflow Security executa pip-audit semanalmente e em pull
requests.

Em 14/08/2026, pip-audit 2.10.1 resolveu o requirements.txt atualizado e
retornou “No known vulnerabilities found”. Como ainda não há lock transitivo,
esse resultado é um snapshot e deve ser reproduzido em cada build.

## Imagens

Tags foram fixadas por versão, mas não por digest. O repositório
[bitcoin/bitcoin](https://hub.docker.com/r/bitcoin/bitcoin) declara que suas
imagens são de terceiros e voltadas a testes. Uma implantação financeira deve
verificar binários Bitcoin Core e manter proveniência própria.

## Estratégia de atualização

- patch: Dependabot + CI, merge após testes;
- minor: revisar changelog e contratos;
- major: branch dedicada, testes de integração e plano de rollback;
- imagem Bitcoin: sincronizar nó em volume descartável antes de tocar dados
  persistentes;
- nunca atualizar automaticamente mainnet sem janela operacional.

## Navegador

O frontend requer JavaScript moderno: WebSocket, Web Audio, Unicode property
escapes, optional chaining, CSS Grid e custom properties. Use versões atuais de
Chrome, Edge, Firefox ou Safari. O modo reduced motion é respeitado.
