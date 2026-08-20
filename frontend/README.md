<p align="center"><img src="../docs/assets/frontend.svg" width="96" alt="Ícone animado da interface"></p>

# Frontend

Aplicação PWA estática em HTML, CSS e JavaScript. O layout parte de telas móveis;
o Nginx entrega somente o jogo e atua como proxy same-origin para a API e o
WebSocket. Documentação e apresentação usam outra imagem/profile.

## Arquivos

| Arquivo | Papel |
|---|---|
| index.html | Semântica da interface, painéis e modais |
| style.css | Tema mobile-first, áreas seguras, grade, animações e breakpoints progressivos |
| game.js | Catálogo multi-rede, lifecycle da sessão, PWA, partida e entrada pointer/teclado |
| manifest.webmanifest | identidade, escopo e instalação do PWA |
| service-worker.js | cache exclusivo do shell e ciclo de atualização |
| icons/ | ícones vetoriais `any`/`maskable` sem dependência externa |
| nginx.conf | Arquivos estáticos e proxy para o backend |
| Dockerfile | Imagem Nginx contendo somente o PWA |

## Estado do jogo

O navegador mantém uma sessão por vez, identificada por `realm_id`, além de
nickname, saldo fictício, hardware, combo, modo Lightning
simulado, buffer de transações e cronômetro. Esse modelo é adequado para demonstração,
mas não oferece integridade competitiva: o roadmap prevê um servidor
autoritativo.

## URLs em runtime

Por padrão o cliente usa a própria origem:

- GET /api/v1/networks
- GET/POST /api/v1/networks/{realm_id}/leaderboard
- GET /api/v1/networks/{realm_id}/health
- WebSocket /ws/v1/game/{realm_id}

Ao trocar rede, a geração da sessão invalida socket, requests, intervals e
timeouts anteriores. Saldo/upgrades não atravessam realms. Os aliases antigos
são usados somente por frontends de uma versão anterior.

A meta tag api-base-url em index.html permite apontar para outro host em
desenvolvimento. Em produção, prefira o proxy Nginx e HTTPS na borda.

## Mobile-first e acessibilidade

- base em coluna única; layouts de tablet/desktop entram somente com `min-width`;
- `100dvh`, safe areas e navegação inferior para o celular;
- tamanho das células calculado conforme grade e largura disponível;
- Pointer Events unificam mouse, caneta e toque;
- setas, Enter e Escape operam a grade pelo teclado;
- status usam regiões live e animações respeitam `prefers-reduced-motion`.

## Política PWA

O service worker guarda apenas HTML, CSS, JavaScript, manifest e ícones. Rotas
`/api`, `/ws`, health, ranking, Swagger e OpenAPI nunca entram no cache. Offline,
o shell explica que redes e eventos exigem conexão. Atualizações aguardam ação
explícita no banner antes de ativar o novo worker.

O protótipo visual autônomo fica em `prototypes/mobile-pwa.html`; a pasta é
local/ignorada e não entra no Docker nem no GitHub.

## Validação

    node --check frontend/game.js
    node --check frontend/service-worker.js
    python scripts/validate_docs.py

Teste manualmente mouse e toque, matrizes 8×8, 12×12 e 15×15, perda de conexão,
resultado por bloco e por timeout. O roteiro está em
[TUTORIAL.md](../docs/TUTORIAL.md).
