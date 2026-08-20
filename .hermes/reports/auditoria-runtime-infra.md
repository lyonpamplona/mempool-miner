# Auditoria Runtime/Infra — Mempool Miner

**Data:** 2026-08-19 16:15 UTC-3
**Status:** 7 containers em execução · 0 restarts
**Sintoma:** Clique em EXECUTE_NODE não avança
**Hipótese validada:** ✅ CSP bloqueia inline `onclick` handlers

---

## 1. CSP — Impacto nos handlers inline (CAUSA RAIZ)

### Evidência: headers reais

```
Content-Security-Policy: default-src 'self'; base-uri 'self'; connect-src 'self' ws: wss:;
  font-src 'self'; form-action 'self'; frame-ancestors 'none'; img-src 'self' data:;
  object-src 'none'; script-src 'self'; style-src 'self'; worker-src 'self'
```

**Arquivo:** `frontend/nginx.conf:16`

### Problema confirmado

- `script-src 'self'` — **NÃO inclui `'unsafe-inline'`**
- `style-src 'self'` — **NÃO inclui `'unsafe-inline'`**
- **11 handlers `onclick` inline** no HTML (index.html)
- **135 atributos `style=` inline** no HTML

### Handlers inline bloqueados (lista completa)

| Linha | Elemento | Handler | Impacto |
|-------|----------|---------|---------|
| 192 | Nav button | `onclick="switchTab('tx', this)"` | ❌ Navegação por abas |
| 196 | Nav button | `onclick="switchTab('shop', this)"` | ❌ Navegação por abas |
| 200 | Nav button | `onclick="switchTab('rank', this)"` | ❌ Navegação por abas |
| 204 | Nav button | `onclick="switchTab('info', this)"` | ❌ Navegação por abas |
| 221 | Shop button | `onclick="buyHint()"` | ❌ Compra de hint |
| 229 | Shop button | `onclick="buyHardware()"` | ❌ Compra de hardware |
| 237 | Shop button | `onclick="buyLightning()"` | ❌ Compra Lightning |
| **478** | **Auth button** | **`onclick="startSession()"`** | **❌ EXECUTE_NODE — CRÍTICO** |
| 490 | Result button | `onclick="useRbf()"` | ❌ RBF emergency |
| 493 | Result button | `onclick="prepareNextBlock()"` | ❌ Próximo bloco |
| 528 | Lightning modal | `onclick="document.getElementById('lightning-modal').classList.add('hidden')"` | ❌ Fechar modal |

### Prova de reprodução (Chrome headless)

```
CSP bloqueia inline onclick; estado antes/depois confirma nenhuma transição e ws=null.
Runtime.exceptionThrown game.js:5421 handleWebSocketMessage undefined.
```

### Análise do fluxo EXECUTE_NODE

1. Usuário clica no botão `onclick="startSession()"` (linha 478)
2. **CSP bloqueia o inline handler** — `startSession()` nunca é chamado
3. O modal de autenticação permanece visível
4. `ws` permanece `null` — sem conexão WebSocket
5. O jogo nunca inicia

### Google Fonts também bloqueadas

```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet">
```

- `font-src 'self'` não permite `https://fonts.googleapis.com` nem `https://fonts.gstatic.com`
- **Impacto:** Fontes JetBrains Mono, Press Start 2P e VT323 não carregam
- **Arquivo:** `frontend/index.html:15`

---

## 2. Cache-Control e Service Worker

### Cache-Control por asset

| Asset | Cache-Control | Expires | ETag | Observação |
|-------|--------------|---------|------|------------|
| `/` (index.html) | `no-cache` | -1 | `"6a85c026-8b48"` | ✅ Correto |
| `/service-worker.js` | `no-cache` | -1 | `"6a7f6b4a-8c5"` | ✅ Correto |
| `/style.css` | `no-cache` | -1 | `"6a8261fa-19e05"` | ✅ Correto |
| `/game.js` | `no-cache` | -1 | `"6a85d106-37a2a"` | ✅ Correto |
| `/manifest.webmanifest` | `no-cache` | -1 | `"6a7f699e-31b"` | ✅ Correto |
| `/pixel.css` | **(nenhum)** | **(nenhum)** | `"6a85c41a-d265"` | ⚠️ Sem cache directive |
| `/icons/icon-192.svg` | `max-age=604800` | 7d | `"6a7f69a2-5d2"` | ✅ Correto |

### pixel.css — sem cache directive

- **Nginx:** `pixel.css` NÃO é coberto por `location ~* ^/(?:style\.css|game\.js)$` (nginx.conf:71)
- **Falls through** para `location / { try_files $uri =404; }` (nginx.conf:86) — sem `expires`
- **Resultado:** Sem `Cache-Control` nem `Expires` no response header
- **Arquivo:** `frontend/nginx.conf:71` — regex não inclui `pixel.css`

### Service Worker — pixel.css NÃO está no precache

```javascript
// service-worker.js:5-13
const SHELL_ASSETS = [
    './',
    './index.html',
    './style.css',
    './game.js',
    './manifest.webmanifest',
    './icons/icon-192.svg',
    './icons/icon-512.svg'
];
```

- **`pixel.css` é referenciado em `index.html:19`** mas **NÃO está em `SHELL_ASSETS`**
- **Impacto:** Em modo offline, o service worker não tem `pixel.css` em cache
- O CSS principal (`style.css`) está no precache, mas `pixel.css` (53KB) não
- **Arquivo:** `frontend/service-worker.js:5-13`

### Service Worker — versão do cache

- `CACHE_NAME = 'mempool-miner-shell-v1'` — versão hardcoded `v1`
- Se assets mudarem sem incrementar a versão, o cache serve conteúdo stale
- **Arquivo:** `frontend/service-worker.js:4`

### index.html → 308 redirect

- `GET /index.html` retorna `308 Permanent Redirect → /`
- **Arquivo:** `frontend/nginx.conf:56-58`
- Comportamento correto, mas o service worker precache ambos `./` e `./index.html` (redundante)

---

## 3. API e WebSocket

### API HTTP — funcionando

| Endpoint | Status | Resposta |
|----------|--------|----------|
| `/api/v1/health/live` | 200 | `{"status":"ok"}` |
| `/api/v1/health/ready` | 200 | `{"status":"ready"}` |
| `/api/v1/networks` | 200 | 3 redes (regtest, signet, mainnet) |

### WebSocket — endpoint correto funciona

| Endpoint | Resultado | Observação |
|----------|-----------|------------|
| `/ws/` (curl sem Origin) | **403 Forbidden** | ❌ Sem Origin header |
| `/ws/v1/game/regtest` (com Origin) | **101 Switching Protocols** | ✅ Handshake OK |
| `/ws/v1/game/signet` (com Origin) | **101 Switching Protocols** | ✅ Handshake OK + dados fluindo |

### WebSocket handshake detalhado (signet)

```
→ GET /ws/v1/game/signet
  Origin: http://127.0.0.1:8010
  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
  Sec-WebSocket-Version: 13

← 101 Switching Protocols
  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

→ {"action":"game_start", "realm_id":"signet", "playable":true, "status":"ready"}
→ {"action":"transaction_received", "word":"DECIDE", ...}
→ {"action":"transaction_received", "word":"ONLY", ...}
→ {"action":"heartbeat"}
```

### WebSocket — validação de origem

- Backend valida `Origin` header contra `cors_origins` (main.py:475-494)
- CORS_ORIGINS: `http://localhost:8010,http://127.0.0.1:8010`
- **Sem Origin → rejeição 403** (comportamento correto)
- **Arquivo:** `backend/app/main.py:475-494`

### WebSocket — erro no frontend

- `game.js:5421` — `const originalHandleWebSocketMessage = handleWebSocketMessage;`
- `handleWebSocketMessage` **nunca é definido como variável global** antes do monkey-patch
- O handler real do WebSocket está inline em `socket.onmessage` (game.js:963)
- **Impacto:** `ReferenceError: handleWebSocketMessage is not defined` ao carregar a seção de Global Events
- **Arquivo:** `frontend/game.js:5421`

---

## 4. Hashes — Host vs Container vs HTTP

### SHA-256 comparison (host filesystem vs container)

| Asset | Host SHA-256 | Container SHA-256 | Match? |
|-------|-------------|-------------------|--------|
| index.html | `13ae1b3e...d71` | `13ae1b3e...d71` | ✅ |
| style.css | `6a360562...972` | `6a360562...972` | ✅ |
| pixel.css | `d6cb1ee9...e8e` | `d6cb1ee9...e8e` | ✅ |
| game.js | `ee46f080...d4f` | `ee46f080...d4f` | ✅ |
| manifest.webmanifest | `ba2c641c...e45` | `ba2c641c...e45` | ✅ |
| service-worker.js | `bd0cfd5c...9f` | `bd0cfd5c...9f` | ✅ |

### HTTP content vs filesystem

- `curl http://127.0.0.1:8010/ | sha256sum` → `13ae1b3e...d71`
- Host `index.html` → `13ae1b3e...d71`
- **Match perfeito** — sem discrepância

### Timestamps dos assets

| Asset | Last-Modified | Idade |
|-------|--------------|-------|
| index.html | 2026-08-19 14:39 | ~2h |
| game.js | 2026-08-19 15:51 | ~30min |
| pixel.css | 2026-08-19 14:56 | ~1.5h |
| style.css | 2026-08-17 01:20 | ~2 dias |
| service-worker.js | 2026-08-14 19:23 | ~5 dias |
| manifest.webmanifest | 2026-08-14 19:16 | ~5 dias |

---

## 5. Logs — Erros causais vs ruído

### Backend — sem erros

- **0 erros** nos últimos 100 logs
- Apenas healthchecks (`/api/v1/health/live`) e requests de `/api/v1/networks`
- WebSocket 403 do teste curl (esperado — sem Origin header)

### Ingestor regtest — sem erros

- RPC calls consistentes a cada ~10s
- Todos retornam `200 OK`
- **0 erros**

### Ingestor signet — ruído (NÃO causal)

- **Padrão:** `getmempoolentry` retorna `500 Internal Server Error` intermitentemente
- **Frequência:** ~80% das chamadas falham, ~20% succeedem
- **Causa:** Signet node instável ou transações não-existentes na mempool
- **Impacto:** NÃO afeta o fluxo do frontend — o ingestor continua operando
- **Classificação:** Ruído signet — não relacionado ao sintoma

### Frontend (nginx) — sem erros

- **0 erros** no access log
- Healthchecks a cada 10s (Wget)
- Requests normais do browser (Chrome 151)
- **Nenhum 4xx ou 5xx** exceto o teste WS sem Origin

---

## 6. Readiness, Restarts e Nginx

### Container health

| Container | Status | RestartCount | Uptime |
|-----------|--------|-------------|--------|
| frontend-1 | healthy | 0 | 19min |
| backend-1 | healthy | 0 | 19min |
| ingestor-regtest-1 | healthy | 0 | 51min |
| ingestor-signet-1 | healthy | 0 | 51min |
| redis-1 | healthy | 0 | 2h |
| bitcoin-regtest-1 | healthy | 0 | 2h |
| bitcoin-signet-1 | healthy | 0 | 2h |

### Nginx — configuração

- `server_tokens off` ✅
- `autoindex off` ✅
- `charset utf-8` ✅
- `read_only: true` + tmpfs ✅
- Healthcheck: `wget -qO- http://127.0.0.1:80/` ✅

### Regras de proxy

| Location | Proxy | Timeout | Observação |
|----------|-------|---------|------------|
| `/api/` | `http://backend:8000/api/` | 30s | ✅ Correto |
| `/ws/` | `http://backend:8000` | 3600s read | ✅ Correto |
| `/` | static files | N/A | ✅ Correto |

---

## 7. Resumo de achados

### CRÍTICO — Causa raiz confirmada

| # | Problema | Arquivo:linha | Evidência |
|---|----------|---------------|-----------|
| 1 | **CSP `script-src 'self'` bloqueia 11 inline `onclick` handlers** | `nginx.conf:16` + `index.html:192-528` | Headers reais + repro Chrome |
| 2 | **EXECUTE_NODE (`onclick="startSession()"`) é bloqueado pela CSP** | `index.html:478` | Botão nunca dispara `startSession()` |
| 3 | **CSP `style-src 'self'` bloqueia 135 inline `style=` attributes** | `nginx.conf:16` + `index.html` | Headers reais |
| 4 | **Google Fonts bloqueadas por `font-src 'self'`** | `nginx.conf:16` + `index.html:15` | CSP não permite `fonts.googleapis.com` |

### MÉDIO — Bugs funcionais

| # | Problema | Arquivo:linha | Impacto |
|---|----------|---------------|---------|
| 5 | **`pixel.css` não está no precache do service worker** | `service-worker.js:5-13` | Offline: CSS pixel não disponível |
| 6 | **`pixel.css` sem Cache-Control no nginx** | `nginx.conf:71` | Sem cache directive — browser decide |
| 7 | **`handleWebSocketMessage` undefined em game.js:5421** | `game.js:5421` | ReferenceError ao carregar Global Events |
| 8 | **Service Worker cache version hardcoded `v1`** | `service-worker.js:4` | Stale cache sem version bump |

### BAIXO — Observações

| # | Problema | Arquivo:linha | Impacto |
|---|----------|---------------|---------|
| 9 | **Signet ingestor: getmempoolentry 500 intermitente** | Logs ingestor-signet | Ruído — não afeta frontend |
| 10 | **`/index.html` → 308 redirect para `/`** | `nginx.conf:56-58` | Comportamento correto, mas redundante no SW |

---

## 8. Recomendações (NÃO aplicadas — auditoria apenas)

### Para resolver o sintoma EXECUTE_NODE

1. **Remover todos os `onclick` inline do HTML** e migrar para `addEventListener` no JavaScript
   - Ou adicionar `'unsafe-inline'` à CSP (menos seguro)
   - Ou usar `nonce`/hash para cada inline handler (complexo)

2. **Remover todos os `style=` inline do HTML** e migrar para classes CSS
   - Ou adicionar `'unsafe-inline'` à `style-src` (menos seguro)

3. **Adicionar Google Fonts à CSP:**
   ```
   font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com;
   ```

4. **Adicionar `pixel.css` ao precache do service worker**

5. **Adicionar `pixel.css` à regex do nginx** ou criar location dedicado:
   ```nginx
   location ~* ^/(?:style\.css|pixel\.css|game\.js)$ {
       try_files $uri =404;
       expires -1;
   }
   ```

6. **Corrigir `handleWebSocketMessage` em game.js:5421** — definir a função antes do monkey-patch ou remover o patch

7. **Versionar o cache do service worker** baseado no hash dos assets

---

## 9. Comandos de auditoria utilizados

```bash
# Headers reais
curl -sI http://127.0.0.1:8010/
curl -sI http://127.0.0.1:8010/pixel.css
curl -sI http://127.0.0.1:8010/style.css
curl -sI http://127.0.0.1:8010/game.js
curl -sI http://127.0.0.1:8010/service-worker.js
curl -sI http://127.0.0.1:8010/manifest.webmanifest
curl -sI http://127.0.0.1:8010/icons/icon-192.svg

# API
curl -s http://127.0.0.1:8010/api/v1/health/live
curl -s http://127.0.0.1:8010/api/v1/health/ready
curl -s http://127.0.0.1:8010/api/v1/networks

# WebSocket
curl -s -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Origin: http://127.0.0.1:8010" http://127.0.0.1:8010/ws/v1/game/signet

# Hashes
sha256sum frontend/{index.html,style.css,pixel.css,game.js,manifest.webmanifest,service-worker.js}
docker exec mempool-miner-frontend-1 sha256sum /usr/share/nginx/html/*

# Logs
docker logs mempool-miner-frontend-1 --tail 100
docker logs mempool-miner-backend-1 --tail 100
docker logs mempool-miner-ingestor-signet-1 --tail 50
docker logs mempool-miner-ingestor-regtest-1 --tail 50

# Container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker inspect --format '{{.Name}} | RestartCount: {{.RestartCount}}' $(docker ps -q)

# Backend routes
docker exec mempool-miner-backend-1 python -c "import app.main; [print(r.path, type(r).__name__) for r in app.main.app.routes]"
```
