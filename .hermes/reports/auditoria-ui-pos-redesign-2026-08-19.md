# Auditoria consolidada da UI pós-redesign — Mempool Miner

**Data:** 19 de agosto de 2026  
**Escopo:** `frontend/index.html`, `frontend/pixel.css`, `frontend/style.css`, `frontend/game.js`, `frontend/service-worker.js`, `frontend/icons/ui-sprite.svg` e contratos REST/WebSocket relacionados  
**Modo:** auditoria estática + execução real em Docker + Chrome CDP; relatório atualizado a cada fase verificada  
**Resoluções:** 320×800, 768×1024, 1024×768, 1440×900 e 2560×1440  

## 1. Resumo executivo

O redesign está estruturalmente mais organizado do que a versão anterior: existem exatamente cinco tabs principais, o grid central se adapta às cinco resoluções, os emojis foram removidos e o sprite SVG está íntegro. A auditoria inicial encontrou um bloqueador crítico e oito falhas altas que impediam considerar a UI pronta.

O maior problema era uma colisão entre `.modal-wrap.active` e `.modal-wrap.hidden`: cinco modais essenciais recebiam `active`, mas continuavam `display:none`. A Fase 1 corrigiu a fonte de verdade de visibilidade e comprovou no Chrome real que Result, Boss, conquistas, Lightning e Decoder abrem com `display:flex`.

Além disso, Decoder usa método HTTP incorreto, Guilda/Pool gera username inválido, Staking destrói as opções do próprio select, Market cria IDs duplicados e filtro inoperante, e o teardown permite estado de uma sessão/rede aparecer na seguinte.

No layout, o problema central não é mais apenas largura: a arquitetura de informação ainda concentra mecânicas demais em painéis únicos. `PERFIL` chega a 2.650 px de conteúdo dentro de 154–718 px disponíveis. Em mobile/tablet, a navegação aparece somente depois do jogo, abaixo do primeiro viewport. Em 320 px, `SOCIAL` ainda gera overflow horizontal.

### Contagem consolidada

| Severidade | Quantidade | Situação |
|---|---:|---|
| Crítica | 1 | Corrigida e reproduzida no bundle v11 |
| Alta | 8 | Mecânicas quebradas, navegação/IA e estado entre sessões |
| Média | 10 | Responsividade, acessibilidade, legibilidade e consistência |
| Baixa | 2 | Ruído de automação e dívida técnica |

## 2. Evidências positivas

- 113/113 testes do projeto passaram após a Fase 1.
- 17/17 contratos estáticos frontend passaram.
- `node --check frontend/game.js` passou.
- 7/7 serviços Docker estavam `healthy` após rebuild sem cache.
- Smoke REST e WebSocket passaram.
- 25 cenários CDP foram executados: cinco tabs em cinco resoluções.
- Nenhuma exceção JavaScript foi capturada durante a matriz responsiva.
- Nenhum emoji foi encontrado em HTML, JS, CSS, JSON, WebManifest ou SVG.
- O catálogo dinâmico possui 31 nomes e o sprite possui os mesmos 31 símbolos; não há ícone ausente.
- Não existem IDs duplicados no HTML estático.
- `btn-close-crate` e `btn-sprint-play-again` são criados dinamicamente e não são referências quebradas.
- O grid central não apresenta overflow horizontal nas cinco resoluções.

## 3. Achados confirmados

### UI-001 — Modais ficam `hidden active` e continuam invisíveis

**Severidade:** CRÍTICA  
**Status:** CORRIGIDA NA FASE 1 E VERIFICADA NO BUNDLE PWA v11  
**Arquivos:** `frontend/pixel.css:461-526`, `frontend/game.js:639-656`, `frontend/index.html:501-549`

**Causa raiz:**

- `.modal-wrap.active { display:flex; }` aparece antes de `.modal-wrap.hidden { display:none; }`.
- As duas regras têm a mesma especificidade; a regra posterior `hidden` vence.
- `setModalState()` alterna somente `active` e `aria-hidden`; não remove a classe `hidden`.

**Prova runtime via Chrome CDP:**

| Modal | Classes após abrir | `display` | `aria-hidden` |
|---|---|---|---|
| `result-modal` | `modal-wrap hidden active` | `none` | `false` |
| `boss-defeat-modal` | `modal-wrap hidden active` | `none` | `false` |
| `achievements-modal` | `modal-wrap hidden active` | `none` | `false` |
| `lightning-modal` | `modal-wrap hidden active` | `none` | `false` |
| `decoder-modal` | `modal-wrap hidden active` | `none` | `false` |

O banner PWA sofre da mesma causa: o JS muda o atributo `hidden`, mas mantém a classe CSS `hidden`.

**Impacto:** o modal de resultado não exibe `PROCEED_NEXT_BLOCK`, podendo bloquear o loop principal após uma rodada. Boss, conquistas, Lightning e Decoder também ficam invisíveis. O estado ARIA contradiz o estado visual.

**Correção recomendada:** tornar `setModalState()` a única fonte de verdade. Ao abrir, remover `hidden` e adicionar `active`; ao fechar, remover `active` e adicionar `hidden`. Alternativamente, remover a classe estática `hidden` dos modais e controlar visibilidade somente por `active`, mas não manter dois mecanismos concorrentes. Criar teste DOM/runtime para todos os modais.

**Verificação pós-correção:** `setModalState()` agora sincroniza `active`, classe `hidden`, propriedade nativa `hidden` e `aria-hidden`. O banner PWA usa o mesmo helper. Result, Boss, Achievements, Lightning e Decoder foram abertos via CDP e todos retornaram `class="modal-wrap active"`, `display:flex` e `aria-hidden=false`.

---

### UI-002 — Decoder usa GET, backend exige POST

**Severidade:** ALTA  
**Arquivos:** `frontend/game.js:4119-4130`, `backend/app/main.py:4516-4517`

**Evidência:** `startDecoderGame()` envia `method:'GET'` com body JSON; FastAPI expõe `@app.post(.../decoder/start)`.

**Prova HTTP:** o request usado pelo frontend retornou `405 Method Not Allowed`.

**Impacto:** o mini-game Decoder nunca inicia. O botão volta ao estado anterior após o catch, sem mensagem de erro específica para o usuário.

**Correção recomendada:** usar POST, `Content-Type: application/json`, body validado e tratamento de 422/429/5xx. Cobrir com teste de contrato frontend-backend.

---

### UI-003 — Pool/Guilda gera identidade inválida

**Severidade:** ALTA  
**Arquivos:** `frontend/index.html:490-493`, `frontend/game.js:909-930`, modelos `Username` do backend

**Causa raiz:** o frontend concatena `"[POOL] Operador"` no próprio username. O backend aceita no máximo 12 caracteres e apenas letras, números, `_` e `-`.

**Prova HTTP:** `"[F2P] Miner"` recebeu 422 com “use apenas letras, números, hífen e sublinhado”.

**Impacto:** qualquer jogador que preencher o campo opcional de Pool/Guilda perde persistência de stats/estado e pode falhar em várias mecânicas.

**Correção recomendada:** manter `operator_id` e `pool_tag` como campos separados no estado e nos payloads. Exibir a tag apenas na apresentação. Não incorporar a tag à chave de identidade. Ajustar `maxlength` do operador para 12 e mostrar validação, sem truncamento silencioso.

---

### UI-004 — Staking apaga as opções de duração

**Severidade:** ALTA  
**Arquivos:** `frontend/index.html:325`, `frontend/game.js:3717,3758-3777`

**Causa raiz:** `stakingDurationEl` aponta para `<select id="staking-duration">`, mas `updateStakingUI()` executa `stakingDurationEl.textContent = "...h"` quando o stake fica ativo.

**Impacto:** atribuir `textContent` ao select remove todas as `<option>`. Depois de cancelar/expirar, o jogador não consegue escolher nova duração sem recarregar a página.

**Correção recomendada:** separar o display ativo em outro elemento, por exemplo `#staking-active-duration`, e preservar `staking-duration` exclusivamente como select. Criar teste DOM que confirme que as opções permanecem após ciclo ativo/inativo.

---

### UI-005 — Market cria IDs duplicados e filtro não funciona

**Severidade:** ALTA  
**Arquivos:** `frontend/index.html:448-460`, `frontend/game.js:5141-5195`

**Causa raiz:** existem controles estáticos `#btn-refresh-market` e `#market-filter-powerup` fora de `#market-browse`. Quando há listings, `renderMarketList()` cria controles com os mesmos IDs dentro de `#market-browse`.

**Impacto:**

- dois elementos com cada ID;
- seletores globais tornam-se ambíguos;
- `marketFilterPowerupEl` continua apontando para o elemento estático, que é um `<div>` sem `value`;
- ao mudar o select dinâmico, o render lê novamente `all`, portanto o filtro não persiste.

**Correção recomendada:** manter um único toolbar estático com `<select>` e botão; `renderMarketList()` deve renderizar somente listings. Usar referências estáveis e teste com pelo menos dois tipos de power-up.

---

### UI-006 — Estado de mecânicas vaza entre sessão/rede

**Severidade:** ALTA  
**Arquivo:** `frontend/game.js:565-634` e estados de Boss/Event/Decoder/Season/Market/Achievements

**Evidência:** `teardownSession()` limpa sockets, intervals e parte do estado base, mas não chama `resetBossState()`, não zera `activeGlobalEvent`, não fecha/reset Decoder e mantém caches de Season, Market, Cards, Friends e Achievements.

**Impacto:** ao trocar rede ou operador durante Boss/evento/modal, a nova sessão pode começar com banner, bônus, dados ou flags da sessão anterior. Boss é o caso mais grave porque `isBossActive` altera o fluxo do jogo.

**Correção recomendada:** criar um `resetFeatureState()` central, idempotente, chamado pelo teardown antes de iniciar a nova sessão. Cobrir troca de realm durante Boss, evento global e Decoder.

---

### UI-007 — Navegação principal fica abaixo do primeiro viewport

**Severidade:** ALTA  
**Arquivos:** `frontend/index.html:197-213`, `frontend/pixel.css:2041-2168`

**Métricas CDP:**

| Viewport | Topo da navegação | Altura do viewport | Topo do painel ativo |
|---|---:|---:|---:|
| 320×800 | 791 px | 800 px | 863 px |
| 768×1024 | 1.049 px | 1.024 px | 1.113 px |

**Impacto:** em mobile/tablet, o usuário precisa atravessar todo o jogo antes de descobrir/trocar entre Jogo, Upgrades, Competir, Perfil e Social. `position:sticky` só ajuda depois que a navegação já foi alcançada.

**Correção recomendada:** manter a mesma navegação unificada, mas posicioná-la antes do conteúdo secundário ou como bottom navigation fixa/safe-area em `<=1023px`. Preservar 44 px por alvo e não criar uma segunda taxonomia de tabs.

---

### UI-008 — Perfil mistura mecânicas e cria scroll excessivo

**Severidade:** ALTA  
**Arquivos:** `frontend/index.html:310-411`, estrutura `.tab-pane`

**Conteúdo atual:** introdução/tutorial, staking, skill tree, season pass, cards, achievements e status de Decoder na mesma coluna.

**Métricas CDP:**

| Viewport | Área visível do pane | Conteúdo de Perfil |
|---|---:|---:|
| 1024×768 | 154 px | 2.629 px |
| 1440×900 | 259 px | 2.629 px |
| 2560×1440 | 718 px | 2.650 px |

**Impacto:** o problema persiste em todas as larguras; aumentar breakpoint não resolve. Em notebook há scroll interno longo dentro de uma área muito baixa, com baixa descoberta e mecânicas misturadas.

**Correção recomendada:** manter `PERFIL` como tab principal e criar subáreas internas: Visão geral, Progressão, Coleção e Economia. Em desktop usar segmented control; em mobile usar acordeões com uma seção aberta. Mover tutorial/protocolo para Ajuda contextual, não para o fluxo principal.

---

### UI-009 — Tabs e modais não são operáveis corretamente por teclado

**Severidade:** ALTA  
**Arquivos:** `frontend/game.js:55-72,658-682`, `frontend/index.html:198-212`

**Evidência:**

- tabs inativas recebem `tabindex=-1`;
- não há handler de ArrowLeft/ArrowRight/Home/End;
- o focus trap procura `.modal-overlay.active`, mas os modais usam `.modal-wrap`;
- não há Escape padronizado para fechar modais.

**Impacto:** usuário de teclado alcança apenas a tab já ativa e não consegue alternar. Depois de corrigir a visibilidade dos modais, foco pode escapar para o fundo.

**Correção recomendada:** implementar padrão WAI-ARIA Tabs com roving tabindex e setas; corrigir seletor do focus trap; suportar Escape; restaurar foco ao controle que abriu o modal.

---

### VALIDAÇÃO-01 — Direção visual está fiel ao `new-design.html`

**Classificação:** NÃO É BUG; FALSO POSITIVO REMOVIDO  
**Arquivos:** `new-design.html:9-34`, `frontend/index.html:5-8`, `frontend/pixel.css:17-45`

**Evidência:** `new-design.html` é a fonte de verdade indicada pelo usuário e define explicitamente o Mecha HUD escuro/neon. A comparação automatizada encontrou os mesmos 19 tokens principais no frontend atual, com valores idênticos, incluindo `#0e1117`, `#161b22`, `#00f0ff`, `#00ff88` e `#f7931a`.

Todas as 56 classes CSS presentes no protótipo possuem implementação no `pixel.css`. A migração de quatro tabs demonstrativas para cinco tabs de produto é intencional para acomodar as mecânicas. O frontend de produção também removeu corretamente fontes remotas, dez handlers inline e 38 estilos inline do protótipo.

**Conclusão:** preservar a direção Mecha Sci-Fi escura. Os ajustes restantes devem corrigir integração, densidade, navegação e responsividade sem substituir a paleta ou criar outro redesign.

---

### UI-011 — Overflow horizontal em Social a 320 px

**Severidade:** MÉDIA  
**Arquivos:** `frontend/index.html:420-427`, `frontend/pixel.css:1981` (`.u-inline-032`)

**Prova CDP:** documento atinge 352 px em viewport de 320 px. O último botão de reação ocupa `x=308..352`.

**Causa:** barra flex sem wrap/overflow control; a classe semântica `.chat-emoji-bar` não está aplicada ao container real.

**Correção recomendada:** aplicar classe específica e `flex-wrap:wrap`, ou transformar em grid de cinco colunas `minmax(44px,1fr)`.

---

### UI-012 — Percentual do Season Pass é invisível

**Severidade:** MÉDIA  
**Arquivos:** `frontend/index.html:350-353`, `frontend/pixel.css:1723-1737`

**Evidência:** `.season-progress-bar` tem 8 px e `overflow:hidden`; `.season-progress-text` tem fonte 12 px e `margin-top:4px`. O CDP mediu texto de 26 px dentro de 6 px úteis, cortado nas cinco resoluções.

**Correção recomendada:** mover o texto para fora da barra ou aumentar a track e centralizar um label overlay legível, mantendo `aria-valuenow`/`aria-valuetext`.

---

### UI-013 — Semântica de modais e formulários incompleta

**Severidade:** MÉDIA  
**Arquivos:** `frontend/index.html:5,501-549`

**Evidência:** somente autenticação tem `role="dialog"`/`aria-modal`. Result, Boss, Achievements, Lightning e Decoder não possuem semântica de diálogo. Inputs de staking, Decoder, chat, amigos e mercado dependem de placeholder. O viewport desabilita zoom com `user-scalable=no`.

**Correção recomendada:** adicionar nomes acessíveis, labels e descrição; remover bloqueio de zoom; usar `role=dialog`, `aria-modal=true`, `aria-labelledby`, `aria-describedby` e estado `aria-hidden` coerente.

---

### UI-014 — Touch targets e controles pequenos no desktop/tablet landscape

**Severidade:** MÉDIA  
**Arquivos:** `frontend/pixel.css:1803-1806,2220-2226`

**Evidência:** ações secundárias permanecem com 28 px; `#staking-duration` foi medido com 22 px em 1024/1440/2560. A regra de 44 px vale somente até 1023 px.

**Correção recomendada:** aplicar mínimo 44×44 por `@media (pointer:coarse)` independentemente da largura e mínimo visual de 36 px para mouse.

---

### UI-015 — Tipografia não escala e operador é truncado

**Severidade:** MÉDIA  
**Arquivos:** utilitários `u-inline-*` em `frontend/pixel.css:1940-2029`

**Evidência:** vários labels usam 6–10 px absolutos inclusive em 2560 px. O operador `UIAUDIT2026` fica limitado a 42 px e truncado em 320 px.

**Correção recomendada:** substituir tamanhos absolutos críticos por tokens `clamp()`, definir piso de legibilidade e permitir ao tag do operador ocupar espaço disponível antes de truncar.

---

### UI-016 — `maxlength` comunica 16, lógica usa 12

**Severidade:** MÉDIA  
**Arquivos:** `frontend/index.html:491`, `frontend/game.js:910-913`

**Evidência:** o input aceita 16 caracteres, mas o JS faz `.slice(0,12)` sem feedback.

**Impacto:** identidade exibida/persistida pode diferir do que o usuário digitou.

**Correção recomendada:** `maxlength=12`, contador/feedback e uma função compartilhada de validação coerente com backend.

---

### UI-017 — Confirmação nativa rompe o design

**Severidade:** MÉDIA  
**Arquivo:** `frontend/game.js:3988-3993`

**Evidência:** cancelamento de stake usa `confirm()` nativo.

**Impacto:** UI visualmente inconsistente e sem controle sobre acessibilidade/estilo, contrariando a navegação customizada aprovada.

**Correção recomendada:** modal de confirmação reutilizável em pixel art, com teclado, foco e ação assíncrona segura.

---

### UI-018 — Corte residual de 3 px em 1024 px

**Severidade:** MÉDIA/BAIXA  
**Arquivo:** `frontend/pixel.css`, sizing de `.stage-center`

**Prova CDP:** conteúdo 497 px dentro de 494 px com `overflow:hidden` em 1024×768.

**Correção recomendada:** recalcular altura útil usando header/footer/padding ou permitir overflow visível/auto somente no container correto.

---

### UI-019 — `user-select:none` global

**Severidade:** MÉDIA  
**Arquivo:** `frontend/pixel.css:72-77`

**Impacto:** impede copiar TXIDs, mensagens de erro e valores; pode afetar seleção em inputs em alguns browsers.

**Correção recomendada:** aplicar somente em controles/jogo; liberar `user-select:text` para inputs, logs, TXIDs, status e conteúdo informativo.

---

### UI-020 — AudioContext gera warning repetido em automação

**Severidade:** BAIXA  
**Arquivo:** `frontend/game.js:96-144`

**Evidência:** 100 warnings idênticos na matriz CDP: `AudioContext was not allowed to start`. A automação usa `element.click()` não confiável, portanto isso não reproduz necessariamente com clique humano.

**Correção recomendada:** aguardar `audioCtx.resume()` antes de criar oscillator e ignorar som quando o contexto permanecer suspended. Tratar como robustez/testabilidade, não como bloqueador visual.

---

### UI-021 — `style.css` é legado não carregado

**Severidade:** BAIXA / DÍVIDA TÉCNICA  
**Arquivos:** `frontend/style.css`, `frontend/Dockerfile`, `frontend/README.md`, `frontend/index.html:18`

**Evidência:** o HTML carrega somente `pixel.css`; `style.css` ainda é copiado para a imagem e documentado como ativo.

**Impacto:** não afeta a cascata atual, mas confunde manutenção e agentes, aumenta imagem e sugere duas fontes de design.

**Correção recomendada:** remover da imagem/README ou arquivar explicitamente fora dos assets servidos após confirmar que nenhuma regra necessária depende dele.

## 4. Matriz responsiva consolidada

| Resolução | Resultado | Principais observações |
|---|---|---|
| 320×800 | Reprovada | Social gera 352 px; nav começa em y=791; operador truncado; página Perfil ~3.690 px |
| 768×1024 | Reprovada | nav começa em y=1.049; painéis ficam após o jogo; página muito longa |
| 1024×768 | Reprovada | pane com 154 px; Perfil 2.629 px; corte de 3 px no stage |
| 1440×900 | Parcial | largura estável, mas pane com 259 px e scroll interno excessivo |
| 2560×1440 | Parcial | grid e largura estáveis; Perfil 2.650 px e fontes fixas muito pequenas |

## 5. Evidências e artefatos

- JSON CDP: `/tmp/mempool-ui-final-audit.json` (CP850)
- Screenshots atuais: `/mnt/c/Temp/mempool-ui-audit/`
- Prova dos modais: `/mnt/c/Temp/mempool-modal-proof.ps1`
- Auditor visual: `/mnt/c/Temp/mempool-ui-audit.ps1`
- Screenshot-chave: `/mnt/c/Temp/mempool-ui-audit/320x800-social.png`
- Screenshot-chave: `/mnt/c/Temp/mempool-ui-audit/1024x768-perfil.png`
- Screenshot-chave: `/mnt/c/Temp/mempool-ui-audit/2560x1440-perfil.png`

## 6. Achados de agents descartados após verificação

- “Season/Sprint/Level não existem no backend”: falso; as rotas existem e foram testadas.
- “`style.css` não carregado quebra a UI”: falso como bug runtime; `pixel.css` é autocontido. Mantido apenas como dívida.
- “Ícones ausentes no sprite”: falso; catálogo e sprite têm 31/31.
- “`btn-close-crate` e `btn-sprint-play-again` ausentes”: falso; são dinâmicos.
- “Todos os offscreen são quebras”: falso; a maioria é conteúdo vertical dentro de scroll. Foram mantidos apenas overflow horizontal, navegação abaixo do viewport e scroll arquitetural do Perfil.

## 7. Critério para considerar a UI pronta

A UI só deve ser declarada pronta quando:

1. todos os modais abrirem/fecharem e o resultado permitir avançar;
2. Decoder, Staking, Market e Pool/Guilda passarem smokes funcionais;
3. não houver overflow horizontal nas cinco resoluções;
4. as cinco tabs forem acessíveis antes de rolar e operáveis por teclado;
5. cada pane tiver uma única estratégia de scroll previsível;
6. Perfil e Social tiverem suborganização interna;
7. a direção visual aprovada estiver versionada e aplicada;
8. o rebuild Docker estiver healthy e a matriz CDP/console estiver limpa;
9. auditor independente não encontrar regressão crítica/alta.
