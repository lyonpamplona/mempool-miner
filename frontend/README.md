<p align="center"><img src="../docs/assets/frontend.svg" width="96" alt="Ícone animado da interface"></p>

# Frontend

Aplicação web estática em HTML, CSS e JavaScript. O Nginx entrega os arquivos e
atua como proxy same-origin para a API e o WebSocket.

## Arquivos

| Arquivo | Papel |
|---|---|
| index.html | Semântica da interface, painéis e modais |
| style.css | Tema, grade, animações e responsividade |
| game.js | Estado da partida, conexão, seleção, pontuação e loja |
| nginx.conf | Arquivos estáticos e proxy para o backend |
| Dockerfile | Imagem Nginx com app e documentação |

## Estado do jogo

O navegador mantém nickname, saldo fictício, hardware, combo, modo Lightning
simulado, buffer de transações e cronômetro. Esse modelo é adequado para demonstração,
mas não oferece integridade competitiva: o roadmap prevê um servidor
autoritativo.

## URLs em runtime

Por padrão o cliente usa a própria origem:

- GET/POST /api/leaderboard
- WebSocket /ws/game

A meta tag api-base-url em index.html permite apontar para outro host em
desenvolvimento. Em produção, prefira o proxy Nginx e HTTPS na borda.

## Validação

    node --check frontend/game.js

Teste manualmente mouse e toque, matrizes 8×8, 12×12 e 15×15, perda de conexão,
resultado por bloco e por timeout. O roteiro está em
[TUTORIAL.md](../docs/TUTORIAL.md).
