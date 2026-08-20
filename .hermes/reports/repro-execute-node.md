# Reprodução determinística — EXECUTE_NODE

**Data:** 2026-08-19  
**Ambiente:** Chrome headless limpo, conectado por Chrome DevTools Protocol a `http://localhost:8010/?audit-csp=1`.

## Passos automatizados

1. Abrir a aplicação em perfil de navegador limpo.
2. Ativar captura de `Runtime.exceptionThrown` e `Log.entryAdded`.
3. Aguardar carregamento completo.
4. Preencher `#miner-input` com `AUDIT_MINER`.
5. Executar `document.querySelector('#auth-modal button').click()`.
6. Aguardar 2,5 segundos e capturar estado do DOM/JS.

## Estado antes do clique

```json
{
  "readyState": "complete",
  "modalExists": true,
  "modalActive": true,
  "modalDisplay": "flex",
  "startSessionType": "function",
  "networkCatalogSize": 3,
  "gameStatus": "Aguardando uma rede jogável."
}
```

## Estado depois do clique

```json
{
  "modalActive": true,
  "modalDisplay": "flex",
  "operator": "OP: [F2P]ANON",
  "nodeStatus": "Escolha uma rede",
  "gameStatus": "Aguardando uma rede jogável.",
  "networkCatalogSize": 3,
  "socketState": null
}
```

## Erros confirmados no navegador

### 1. Handler inline bloqueado por CSP

```text
Executing inline event handler violates the following Content Security Policy directive
'script-src 'self''. ... The action has been blocked.
```

**Origem:**
- `frontend/nginx.conf:16`: `script-src 'self'`
- `frontend/index.html:478`: `onclick="startSession()"`

**Resultado:** o navegador não chama `startSession()`. O modal permanece aberto e nenhum WebSocket é criado.

### 2. Exceção global durante carregamento do game.js

```text
ReferenceError: handleWebSocketMessage is not defined
    at http://localhost:8010/game.js:5421:40
```

**Origem:** `frontend/game.js:5421`

```javascript
const originalHandleWebSocketMessage = handleWebSocketMessage;
```

Não existe definição de `handleWebSocketMessage` no arquivo atual. A exceção aborta a execução sequencial do restante do script; seções e listeners abaixo da linha 5421 não são inicializados.

### 3. CSP bloqueia estilos e fonte do redesign

- 135 atributos `style="..."` no HTML são bloqueados por `style-src 'self'`.
- A folha Google Fonts é bloqueada por `style-src 'self'` e `font-src 'self'`.
- 11 handlers inline são bloqueados por `script-src 'self'`.

## Integridade dos artefatos

Os hashes SHA-256 de `index.html`, `game.js`, `pixel.css` e `service-worker.js` coincidem entre host, container e HTTP. Portanto, o bug não é causado por imagem Docker desatualizada no teste reproduzido.

## Experimento de controle: chamada direta de `startSession()`

Para isolar a ligação HTML→JS, a mesma página foi recarregada e `startSession()` foi chamada diretamente pelo console CDP, sem usar o atributo `onclick`.

```json
{
  "resolved": true,
  "modalActive": false,
  "modalDisplay": "none",
  "operator": "DIRECT_MINER",
  "nodeStatus": "Pronta",
  "gameStatus": "Aguardando seis transações da rede ativa.",
  "networkCatalogSize": 3,
  "activeRealmId": "signet",
  "sessionReady": true,
  "socketState": 1
}
```

**Conclusão do controle:** catálogo, backend, proxy e WebSocket conseguem completar o fluxo core. O travamento inicial é causado pela fronteira HTML→JS: o navegador bloqueia o handler inline antes que `startSession()` seja chamado.

## Resultado

A reprodução é **vermelha e determinística**: o clique é bloqueado pela CSP. Quando a mesma função é invocada diretamente, o painel abre e o WebSocket conecta. O frontend também possui uma exceção global independente em `game.js:5421`, que interrompe a inicialização das mecânicas abaixo dessa linha.
