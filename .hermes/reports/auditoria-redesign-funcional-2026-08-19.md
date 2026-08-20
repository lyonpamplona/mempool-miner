# Auditoria funcional completa do redesign — Mempool Miner

**Data:** 19 de agosto de 2026  
**Escopo:** frontend, backend, WebSocket, contratos REST, Docker/Nginx, CSP, PWA, testes e mecânicas migradas  
**Modo:** auditoria e roadmap; **nenhuma correção de produto aplicada nesta etapa**

---

## 1. Resumo executivo

O travamento no botão **EXECUTE_NODE** foi reproduzido de forma determinística em um Chrome limpo com captura via Chrome DevTools Protocol.

A causa imediata está confirmada:

1. `frontend/nginx.conf:16` envia `Content-Security-Policy: script-src 'self'`.
2. O botão visível em `frontend/index.html:478` depende exclusivamente de `onclick="startSession()"`.
3. O navegador bloqueia o handler inline antes de chamar `startSession()`.
4. O modal permanece aberto e nenhum WebSocket é criado.

O teste de controle chamou `startSession()` diretamente pelo console e comprovou que o núcleo consegue avançar: o modal fechou, a rede Signet ficou pronta e o WebSocket abriu. Portanto, catálogo, proxy, backend e WebSocket **não são a causa do travamento inicial**.

A auditoria também encontrou falhas sistêmicas independentes:

- `ReferenceError` global em `frontend/game.js:5421`, que interrompe a inicialização do restante do arquivo;
- 25 URLs frontend incompatíveis com as rotas backend;
- Season Pass e Mercado retornando HTTP 500 mesmo nas rotas canônicas;
- funções vazias usadas como “correções” (`loadPowerupsInventory`, `renderWordBank`);
- 10 wrappers encadeados de `startSession`;
- DOM duplicado/oculto usado como camada de compatibilidade;
- RBF e navegação migrados para botões sem ligação funcional válida;
- CSP bloqueando 135 estilos inline e a fonte externa do redesign;
- suíte backend com 11 falhas, 67 testes aprovados e 6 erros.

**Conclusão:** o redesign preservou parte da aparência e muitos IDs, mas não preservou integralmente os contratos de evento, segurança, DOM, API e inicialização das mecânicas.

---

## 2. Método e evidências

### 2.1 Auditoria delegada

Foram delegadas quatro frentes independentes:

1. frontend/login e fluxo DOM → JS;
2. backend/WebSocket e contratos REST;
3. inventário ponta a ponta das mecânicas;
4. runtime/infra, CSP, cache, hashes e logs.

Agents que excederam 15 minutos sem gravar relatório foram interrompidos e substituídos por consolidadores focados, usando os transcripts e evidências já verificadas.

### 2.2 Reprodução real no navegador

Estado antes do clique:

```json
{
  "readyState": "complete",
  "modalActive": true,
  "modalDisplay": "flex",
  "startSessionType": "function",
  "networkCatalogSize": 3,
  "gameStatus": "Aguardando uma rede jogável."
}
```

Estado após clicar no botão visível:

```json
{
  "modalActive": true,
  "modalDisplay": "flex",
  "operator": "OP: [F2P]ANON",
  "nodeStatus": "Escolha uma rede",
  "networkCatalogSize": 3,
  "socketState": null
}
```

Erro do navegador:

```text
Executing inline event handler violates the following Content Security Policy directive
'script-src 'self''. The action has been blocked.
```

### 2.3 Experimento de controle

Chamando `startSession()` diretamente, sem o `onclick`:

```json
{
  "resolved": true,
  "modalActive": false,
  "operator": "DIRECT_MINER",
  "nodeStatus": "Pronta",
  "activeRealmId": "signet",
  "sessionReady": true,
  "socketState": 1
}
```

Isso isola a causa do travamento na fronteira HTML → handler.

### 2.4 Integridade dos assets

Os hashes SHA-256 de `index.html`, `game.js`, `pixel.css` e `service-worker.js` coincidiram entre:

- filesystem do host;
- container Nginx;
- conteúdo HTTP servido.

O teste reproduzido não usou uma imagem Docker diferente da versão em disco.

---

## 3. Causas confirmadas — críticas

### C-01 — CSP bloqueia o login e outros 10 handlers

- **Arquivos:** `frontend/nginx.conf:16`, `frontend/index.html:192-528`
- **Evidência:** erro real do Chrome e estado antes/depois do clique.
- **Quantidade:** 11 handlers inline.
- **Impacto:** login, quatro tabs, próximo bloco, RBF, fechar Lightning e parte da loja.

Não é recomendado resolver com `'unsafe-inline'`, pois isso reduz a proteção da CSP. O correto é migrar para listeners externos.

### C-02 — Contrato DOM do login foi rompido

- Botão visível `EXECUTE_NODE`: `frontend/index.html:478`, sem ID e dependente de `onclick`.
- Botão controlado pelo JS: `#btn-start-session`, vazio e oculto em `frontend/index.html:545`.
- `startSessionButtonEl`: `frontend/game.js:250` aponta para o botão oculto.
- O JS adiciona listener `submit` em `#auth-modal` (`game.js:741`), mas `#auth-modal` é uma `<div>`, não um `<form>`.

**Impacto:** o JS habilita/desabilita o elemento errado e não existe fallback funcional para o clique visível.

### C-03 — Exceção global aborta o game.js

- **Arquivo:** `frontend/game.js:5421`

```javascript
const originalHandleWebSocketMessage = handleWebSocketMessage;
```

`handleWebSocketMessage` não existe. O handler real está embutido em `socket.onmessage` (`game.js:963`).

**Impacto:** todo código top-level abaixo da linha 5421 deixa de executar, incluindo listeners/wrappers de:

- Global Events;
- Sprint;
- Friends;
- Crates;
- Level;
- setup dos painéis/tabs finais.

### C-04 — 25 chamadas REST usam convenção inexistente

O frontend usa `/api/${activeRealmId}/...`; o backend implementa `/api/v1/networks/{realm_id}/...`.

Famílias afetadas:

- Skills;
- Energy;
- Season;
- Cards;
- Market;
- Power-ups;
- Global Events;
- Sprint;
- Friends;
- Crates;
- Level.

O experimento direto confirmou 404 reais para Energy, Season, Cards, Market e Power-ups, incluindo polling repetido de Energy a cada 10 segundos.

Há incompatibilidades adicionais além do prefixo:

- Skills: frontend `/unlock`, backend `/upgrade`;
- Energy: frontend coloca username no path, backend espera query parameter;
- Crates inventory: frontend coloca username no path, backend espera query parameter.

### C-05 — Season Pass falha no backend

- **Arquivos:** `backend/app/season_pass.py:104-269`, `backend/app/main.py:4616-4676`
- **Teste live:** `GET /api/v1/networks/signet/season/DIRECT_MINER` → HTTP 500.
- **Erro:** `'coroutine' object has no attribute 'get'`.

`season_pass.py` define funções síncronas e chama operações de `redis.asyncio` sem `await`: `hgetall`, `hset`, `expire`, `hincrby`, `hget`.

### C-06 — Mercado falha no backend

- **Arquivo:** `backend/app/main.py:2399`
- **Teste live:** `GET /api/v1/networks/signet/market/list` → HTTP 500.
- **Erro:** `SortedSetCommands.zrange() got multiple values for argument 'start'`.

---

## 4. Problemas estruturais de alta severidade

### A-01 — Cadeia de 10 wrappers em `startSession`

Reatribuições em `game.js` nas linhas aproximadas:

- 3144 — Missions;
- 3531 — Chat/Staking;
- 4493 — Energy;
- 4741 — Season;
- 4934 — Cards;
- 5261 — Market;
- 5433 — Global Events;
- 5863 — Friends;
- 6036 — Crates;
- 6173 — Level.

Cada feature envolve a função anterior. Um erro num módulo opcional pode interromper a cadeia e tornar o login dependente de subsistemas não essenciais.

### A-02 — Funções vazias mascaram mecânicas inativas

- `loadPowerupsInventory()` — `game.js:267`, corpo vazio;
- `renderWordBank()` — `game.js:1683`, corpo vazio.

Essas funções removem `ReferenceError`, mas não implementam comportamento.

### A-03 — RBF migrado para elemento incompatível

- Botão novo visível: `#rbf-btn`, `index.html:490`, chama `useRbf()` inexistente.
- Lógica real: `showOrphanBlockSalvage()` usa `#next-btn` (`game.js:2124-2182`).
- `#next-btn` está oculto na camada de compatibilidade (`index.html:541`).

Resultado: a UI mostra um controle sem implementação e esconde o controle utilizado pela lógica real.

### A-04 — Camada de compatibilidade depende de inline style bloqueado

`frontend/index.html:535` usa `<div style="display:none;">` para esconder aliases. A CSP bloqueia esse atributo. IDs de compatibilidade podem aparecer na UI ou afetar layout/foco.

Essa camada contém estado real (`network-select`, `network-status`, `ui-active-network`, `ui-node-status`) e botões vazios usados pelo JS.

### A-05 — CSP também quebra o visual

- 135 atributos `style="..."` bloqueados;
- Google Fonts bloqueada por `style-src 'self'`/`font-src 'self'`;
- o protótipo foi copiado com padrões inline incompatíveis com a borda de produção.

### A-06 — Service Worker e cache desalinhados

- cache fixo `mempool-miner-shell-v1`;
- `pixel.css` não está em `SHELL_ASSETS`;
- `style.css` antigo continua no precache;
- Nginx aplica `no-cache` a `style.css` e `game.js`, mas não a `pixel.css`.

Não foi a causa do teste limpo, porém pode manter clientes existentes em estado divergente e quebra o modo offline do redesign.

### A-07 — Código morto no backend

`backend/app/main.py:4677` contém `await serve_websocket(websocket, DEFAULT_REALM_ID)` após todos os caminhos da função retornarem ou levantarem exceção. Além de inalcançável, referencia `websocket` fora do contexto.

---

## 5. Estado das mecânicas após a migração

| Mecânica | Estado observado | Evidência principal |
|---|---|---|
| Login/Auth | **Quebrada na UI** | CSP bloqueia `onclick`; DOM aponta para botão oculto |
| Navegação por tabs | **Quebrada** | quatro `onclick` inline bloqueados |
| Núcleo/grade/WebSocket | **Operacional somente por bypass** | chamada direta iniciou Signet e WS; fluxo normal bloqueado |
| Leaderboard/Pools | **Operacional após bypass** | endpoints 200 e polling iniciado |
| Player/Achievements | **Operacional após bypass** | endpoints 200 |
| Missions | **Contrato funcional** | endpoint 200; wrapper antes do abort |
| Staking | **Contrato funcional** | status/history 200 |
| Chat | **Não verificada E2E; contrato coerente** | URLs canônicas e rotas existentes |
| Decoder | **Não verificada E2E; contrato coerente** | URLs/rotas canônicas |
| Loja Hint/HW/LN | **Parcial/inacessível** | listeners externos existem, mas tab é bloqueada; estado majoritariamente client-side |
| RBF | **Quebrada** | botão visível chama função inexistente; lógica usa botão oculto |
| Energy | **Quebrada no frontend** | 404 repetido; backend canônico 200 |
| Season Pass | **Quebrada ponta a ponta** | frontend 404; backend canônico 500 |
| Cards | **Quebrada no frontend** | frontend 404; backend canônico 200 |
| Market | **Quebrada ponta a ponta** | frontend 404; backend canônico 500 |
| Power-ups | **Quebrada/parcial** | URL errada + loader vazio; backend canônico 200 |
| Skills | **Quebrada no frontend** | prefixo errado + `/unlock` versus `/upgrade`; GET canônico 200 |
| Global Events | **Parcial/quebrada** | wrapper abortado + URL errada; handlers WS já existem no handler real |
| Sprint | **Quebrada** | listeners abaixo do abort + URLs erradas |
| Friends | **Quebrada no frontend** | listeners abaixo do abort + URLs erradas; backend 200 |
| Crates | **Quebrada no frontend** | listeners abaixo do abort + URL/shape errados; backend 200 |
| Level | **Quebrada no frontend** | wrapper abaixo do abort + URL errada; backend 200 |
| Boss/Combo/Slashing | **Não verificada E2E; lógica core presente** | depende do fluxo core alcançável apenas por bypass |
| PWA | **Parcial** | registro existe; cache não representa o redesign atual |

---

## 6. Testes e qualidade

Comando executado:

```bash
.venv/bin/pytest -q
```

Resultado real:

```text
11 failed, 67 passed, 6 errors
```

Categorias:

1. **Testes desatualizados:** `NodeConfig` agora exige credenciais; fixtures ZMQ não foram atualizadas.
2. **Factory ausente:** `create_mock_ingestor` é chamada em cinco testes e não existe/importa.
3. **Contrato alterado:** `ws_sender` mudou de assinatura e teste continua chamando a antiga.
4. **Segurança:** teste espera validação de Host 400, aplicação retorna 404.
5. **Compatibilidade:** teste espera dict no leaderboard legado, implementação retorna `JSONResponse`.
6. **Runtime não coberto:** Season e Market têm falhas 500 que a suíte atual não detecta.

A suíte não pode ser usada hoje como gate de regressão até ser reconciliada com a arquitetura atual.

---

## 7. Logs e infraestrutura

- 7 containers estavam saudáveis e sem restart no momento da auditoria.
- API live/ready e catálogo respondem 200.
- WebSocket Signet/regtest aceita `Origin` permitido e envia `game_start`/eventos.
- 403 sem `Origin` é comportamento esperado.
- Ingestor Signet gera erros `getmempoolentry` 500 frequentes; são ruído operacional separado do login, mas precisam de backoff/classificação correta.
- Após o bypass, logs registraram 404 repetidos das URLs antigas e os 500 de Season/Market.

---

## 8. Roadmap de correção

### Fase 0 — Congelamento e testes de reprodução (0,5 dia)

1. Preservar hashes/backup dos arquivos atuais.
2. Adicionar E2E que reproduz exatamente:
   - preencher nickname;
   - clicar EXECUTE_NODE;
   - modal fecha;
   - `sessionReady === true`;
   - WebSocket aberto;
   - zero erros de console/CSP;
   - zero 404/500 na inicialização.
3. Criar verificação estática que falha se houver `on*=` ou `style=` inline sob a CSP atual.

**Critério de saída:** teste vermelho reproduz o bug atual de forma determinística.

### Fase 1 — Restaurar login, tabs e inicialização (0,5–1 dia)

1. Manter CSP estrita; **não adicionar `unsafe-inline`**.
2. Transformar auth em contrato DOM real:
   - `<form id="auth-form">`;
   - botão visível com ID estável e `type="submit"`;
   - remover botão oculto duplicado.
3. Migrar os 11 handlers inline para `addEventListener`.
4. Remover a tentativa de wrap de `handleWebSocketMessage` em `game.js:5421` e integrar somente no `socket.onmessage` existente — os handlers de Global Events já estão presentes ali.
5. Verificar login, quatro tabs, resultado, próximo bloco, Lightning e RBF.

**Critério de saída:** E2E do login verde, WebSocket aberto, nenhuma exceção global e nenhum handler inline.

### Fase 2 — Unificar contratos REST e corrigir 500 backend (1–2 dias)

1. Criar um único construtor/API client para `/api/v1/networks/{realm}`.
2. Migrar as 25 chamadas antigas.
3. Corrigir shapes especiais:
   - Skills `/upgrade`;
   - Energy com query/body conforme backend;
   - Crates inventory com query parameter.
4. Tornar Season Pass integralmente assíncrono e adicionar `await` a todas as operações Redis.
5. Corrigir `zrange` do Market para a assinatura da versão instalada.
6. Parar/reduzir polling em erros não transitórios para evitar flood de 404.

**Critério de saída:** smoke tests canônicos de todas as famílias sem 404/500; payloads validados por contrato.

### Fase 3 — Reconciliar mecânicas e DOM do redesign (2–3 dias)

1. Substituir aliases ocultos por elementos reais ou adaptadores explícitos.
2. Reconectar RBF, próximo bloco, rede, estado do nó e controles de modal aos elementos visíveis.
3. Implementar ou remover UI de funções vazias:
   - `loadPowerupsInventory`;
   - `renderWordBank`.
4. Substituir a cadeia de wrappers por inicialização centralizada de módulos/hooks, isolando falhas opcionais.
5. Inicializar cada módulo com resultado/erro independente.
6. Validar cada mecânica da matriz ponta a ponta.

**Critério de saída:** nenhuma UI “decorativa” sem handler/endpoint; nenhuma mecânica depende de elemento oculto duplicado.

### Fase 4 — Conformidade visual, CSP e PWA (1–2 dias)

1. Migrar 135 estilos inline para classes em `pixel.css` sem alterar o visual aprovado.
2. Self-host das fontes ou ajuste explícito de CSP para Google Fonts; preferência por self-host.
3. Criar classe externa para ocultar compatibilidade durante a transição.
4. Versionar cache por build/hash.
5. Incluir `pixel.css` e remover `style.css` do precache.
6. Aplicar política de cache coerente a `pixel.css`.
7. Testar atualização de service worker e perfil com cache antigo.

**Critério de saída:** zero violações CSP, visual comparado ao `new-design.html`, atualização PWA previsível e offline com CSS correto.

### Fase 5 — Restaurar quality gate (1–2 dias)

1. Atualizar fixtures `NodeConfig`/ZMQ.
2. Restaurar `create_mock_ingestor` no `conftest.py`.
3. Atualizar testes para a assinatura atual de `ws_sender`.
4. Decidir e testar política de Host/CORS.
5. Atualizar contrato dos endpoints legados.
6. Adicionar testes de Season, Market e dos 25 endpoints frontend.
7. Rodar suíte completa, E2E e auditoria de logs.

**Critério de saída:** `pytest` 100% verde, E2E crítico verde, zero erro de console e zero 404/500 inesperado.

### Estimativa total

**5–8 dias úteis**, dependendo da profundidade exigida para completar as mecânicas atualmente representadas apenas por UI/stubs.

---

## 9. Ordem recomendada de implementação

1. Fase 0 — teste vermelho;
2. Fase 1 — login/CSP/exceção global;
3. auditoria de verificação da Fase 1;
4. Fase 2 — contratos e 500 backend;
5. auditoria de verificação da Fase 2;
6. Fase 3 — mecânicas/DOM;
7. auditoria mecânica completa;
8. Fase 4 — visual/PWA;
9. auditoria visual e responsiva;
10. Fase 5 — suíte/gates finais.

Não é recomendado aplicar todas as mudanças de uma vez. Cada fase deve ter build, health check, E2E, logs e auditoria independente antes da próxima.

---

## 10. Relatórios de apoio

- `.hermes/reports/repro-execute-node.md`
- `.hermes/reports/auditoria-runtime-infra.md`
- `.hermes/reports/auditoria-mecanicas-e-contratos.md`
- `.hermes/reports/auditoria-frontend-login.md`
- `.hermes/reports/auditoria-backend-websocket.md`

Os dois últimos são consolidados por agents substitutos quando os agentes originais excederam o limite operacional.
