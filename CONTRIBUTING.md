# Como contribuir

Obrigado por melhorar o Mempool Miner.

## Preparação

1. Leia [arquitetura](docs/ARQUITETURA.md) e [fluxos](docs/FLUXOS.md).
2. Copie .env.example para .env e use apenas credenciais locais.
3. Crie uma branch curta a partir de main.
4. Faça mudanças pequenas, com documentação e testes proporcionais ao risco.

## Verificações locais

Execute:

    python -m compileall -q backend/app
    node --check frontend/game.js
    pytest -q
    docker compose config --quiet

O guia completo está em [COMANDOS.md](docs/COMANDOS.md).

## Pull requests

- explique o problema antes da solução;
- não inclua .env, cookies RPC, chaves, dados ou logs sensíveis;
- atualize contratos em docs/API.md quando REST ou WebSocket mudar;
- acrescente uma entrada em CHANGELOG.md para mudanças visíveis;
- descreva risco, validação e reversão.

## Padrões

Python usa docstrings e nomes claros; documentação e comentários de domínio são
escritos em português. JavaScript público deve ter JSDoc. O projeto usa UTF-8,
LF, quatro espaços em Python e dois em arquivos web/YAML.
