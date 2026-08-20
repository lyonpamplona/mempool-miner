# Roadmap de correção da UI pós-redesign — Mempool Miner

**Data:** 19 de agosto de 2026  
**Base:** `.hermes/reports/auditoria-ui-pos-redesign-2026-08-19.md`  
**Objetivo:** corrigir falhas funcionais/visuais, reorganizar mecânicas sem abandonar as cinco tabs aprovadas e alinhar a UI ao design pixel art validado  
**Estimativa total:** 10 a 18 dias de desenvolvimento, incluindo validação e auditorias  

## Regras de execução

1. Executar estritamente fase a fase.
2. Escrever testes antes da correção para cada bug funcional.
3. Não avançar com teste, build, health check ou smoke degradado.
4. Ao fim de cada fase:
   - `pytest` completo;
   - `node --check frontend/game.js`;
   - `docker compose up --build -d`;
   - aguardar 7/7 serviços `healthy`;
   - smoke REST e WebSocket;
   - smoke funcional das mecânicas tocadas;
   - Chrome CDP em 320×800, 768×1024, 1024×768, 1440×900 e 2560×1440;
   - auditor independente sem crítico/alto novo.
5. Não alterar a taxonomia principal: JOGO, UPGRADES, COMPETIR, PERFIL e SOCIAL.
6. Não usar emojis, ícones genéricos, confirm/alert nativos ou design genérico de IA.
7. Manter o sprite SVG customizado e o estilo pixel art profissional.

## Ordem resumida

| Fase | Prioridade | Escopo | Estimativa |
|---|---|---|---:|
| 0 | Concluída | `new-design.html` validado como fonte visual | Concluída |
| 1 | Concluída | Sistema de modais e loop principal | Concluída |
| 2 | P1 | Decoder, Staking, Market e Pool/Guilda | 1,5–2,5 dias |
| 3 | P1 | Lifecycle de sessão e isolamento por realm | 0,5–1,5 dia |
| 4 | P1 | Arquitetura de informação e navegação | 2–4 dias |
| 5 | P1/P2 | Responsividade e alinhamento visual | 2–4 dias |
| 6 | P2 | Acessibilidade, teclado e PWA | 1,5–2,5 dias |
| 7 | P2/P3 | Modularização, limpeza e regressão automatizada | 2–4 dias |

---

## Fase 0 — Fixar baseline e fonte de verdade visual

**Objetivo:** impedir um terceiro redesign divergente.

**Status:** CONCLUÍDA — `new-design.html` é a fonte de verdade Mecha HUD escura/neon.

### Ações

1. Usar `new-design.html` como fonte de verdade para composição, tokens, tipografia, componentes e comportamento responsivo.
2. Preservar o Mecha HUD escuro/neon definido no protótipo; não migrar para tema claro/bege.
3. Usar a matriz atual de 25 cenários como baseline “antes”.
4. Tratar `pixel.css` como folha ativa e `style.css` como base legada sobrescrita.
5. Preservar a extensão intencional do protótipo de quatro tabs demonstrativas para as cinco tabs de produto.

### Aceite

- direção visual assinada e versionada;
- tokens sem ambiguidade;
- nenhuma alteração de mecânica nesta fase;
- baseline reproduzível.

---

## Fase 1 — Restaurar modais e loop principal

**Objetivo:** eliminar UI-001 antes de qualquer trabalho cosmético.

**Status:** CONCLUÍDA — 113/113 testes, 17/17 contratos frontend, 7/7 serviços healthy e cinco modais comprovados via CDP no bundle PWA v11.

### Testes RED

1. Abrir cada modal deve resultar em:
   - `display != none`;
   - `active=true`;
   - `hidden=false`;
   - `aria-hidden=false`.
2. Fechar deve produzir o inverso.
3. `showResult()` deve tornar `#next-btn` visível e acionável.
4. Banner PWA deve aparecer quando `registration.waiting` existir.
5. Nenhum modal pode ficar simultaneamente `hidden active`.

### Implementação

1. Tornar `setModalState()` a única fonte de verdade.
2. Remover conflito entre classe `hidden`, atributo `hidden` e classe `active`.
3. Padronizar abertura/fechamento para:
   - Auth;
   - Result/RBF;
   - Boss;
   - Achievements;
   - Lightning;
   - Decoder;
   - PWA update;
   - modal dinâmico de Crate.
4. Restaurar foco após fechar.
5. Atualizar `CACHE_VERSION` do service worker.

### Smoke obrigatório

- completar/forçar uma rodada e avançar;
- abrir/fechar conquistas;
- ativar Lightning;
- abrir resultado Boss;
- simular `registration.waiting` do PWA.

### Aceite

- todos os modais visíveis e coerentes com ARIA;
- loop de rodada não fica preso;
- zero regressão de console.

---

## Fase 2 — Corrigir mecânicas quebradas

**Objetivo:** restaurar quatro fluxos funcionais altos.

### 2.1 Decoder

- trocar GET por POST;
- enviar `Content-Type: application/json`;
- tratar 422, 429 e indisponibilidade;
- corrigir barra de timer para usar track + fill separados;
- teste contrato frontend-backend;
- smoke completo: start, submit correto, submit incorreto, timeout e cooldown.

### 2.2 Staking

- criar `#staking-active-duration` separado;
- nunca escrever `textContent` no select;
- garantir que opções persistem após stake/cancel/expire;
- substituir `confirm()` nativo por modal customizado;
- smoke com 6h, 12h e 24h.

### 2.3 Market

- manter toolbar única e estática;
- remover IDs dinâmicos duplicados;
- renderizar somente listings em `#market-browse`;
- preservar filtro após rerender;
- testar lista vazia, múltiplos tipos, refresh, compra, venda e histórico;
- validar visualmente dados longos e preço alto.

### 2.4 Pool/Guilda e identidade

- separar `operator_id` de `pool_tag` no frontend;
- nunca concatenar tag na chave username;
- ajustar `maxlength=12`;
- validar caracteres antes da sessão;
- exibir tag apenas em label visual;
- migrar/invalidar sessão antiga em `sessionStorage` com formato concatenado;
- smoke com/sem tag e troca de rede.

### Aceite

- Decoder não retorna 405;
- Staking mantém todas as opções;
- zero IDs duplicados após render do Market;
- filtro Market funciona;
- Pool/Guilda não causa 422;
- feedback visível em todo erro.

---

## Fase 3 — Isolar estado por sessão e realm

**Objetivo:** eliminar UI-006 e impedir vazamento entre redes/jogadores.

### Ações

1. Criar `resetFeatureState()` idempotente.
2. Resetar:
   - Boss;
   - evento global e banner;
   - Decoder/modal/cooldown local;
   - Season;
   - Cards;
   - Market/listings/history/inventory;
   - Friends/Chat;
   - Achievements/bonuses/counters;
   - Missions;
   - Energy;
   - Staking.
3. Fechar todos os modais no teardown.
4. Manter AbortControllers por sessão e ignorar resposta de geração antiga.
5. Substituir wrappers restantes por hooks explícitos de lifecycle em uma etapa controlada, sem refatorar toda a UI ainda.

### Testes

- trocar realm durante Boss;
- trocar realm durante Decoder;
- trocar realm durante evento global;
- respostas HTTP antigas não podem alterar nova sessão;
- abrir operador B depois do operador A não mostra dados de A.

### Aceite

- nova sessão começa sempre em estado limpo;
- timers/listeners/requests anteriores não atualizam DOM;
- WebSocket reconecta apenas para a geração atual.

---

## Fase 4 — Reorganizar mecânicas mantendo cinco tabs

**Objetivo:** resolver mistura, baixa descoberta e scroll excessivo sem criar mais tabs principais.

### Arquitetura proposta

#### JOGO

- grade principal;
- word bank/transactions da rodada;
- status da rede e evento global;
- ações imediatas de gameplay.

Não colocar progressão, social ou economia permanente aqui.

#### UPGRADES

Subáreas internas:

1. **Loja** — Hint, Hardware, Lightning, Energy.
2. **Inventário** — power-ups e Crates.
3. **Utilitários** — disponibilidade/entrada do Decoder.

Desktop: segmented control.  
Mobile: acordeões, um aberto por vez.

#### COMPETIR

Subáreas internas:

1. **Ranking** — leaderboard e top pools.
2. **Missões** — diárias/semanais e claims.
3. **Sprint** — modo, timer e resultado.
4. **Pools/PvP** — competição coletiva quando habilitada.

#### PERFIL

Subáreas internas:

1. **Visão geral** — rank, XP, stats e resumo.
2. **Progressão** — Skill Tree + Season Pass.
3. **Coleção** — Cards + Achievements.
4. **Economia** — Staking e histórico.

Mover tutorial/protocolo para Ajuda contextual no header ou primeira experiência; não deixá-lo como seção permanente acima das mecânicas.

#### SOCIAL

Subáreas internas:

1. **Chat**.
2. **Amigos/Equipe**.
3. **Mercado**.

### Navegação responsiva

- manter um único conjunto das cinco tabs;
- em `<=1023px`, torná-lo bottom nav fixa com safe-area ou colocá-lo antes do painel secundário;
- não exigir rolagem pelo grid para trocar de tab;
- desktop permanece na sidebar;
- salvar subárea ativa por tab, sem misturar estados.

### Estratégia de scroll

- um único scroll vertical por pane;
- evitar page scroll + pane scroll simultâneos em notebook;
- cabeçalho da subárea pode ser sticky;
- modais e dropdowns fora do clipping do pane.

### Aceite quantitativo

- navegação integralmente visível no primeiro viewport em 320 e 768;
- pane de Perfil não mostra todas as seções simultaneamente;
- no máximo uma subárea aberta no mobile;
- zero scroll aninhado desnecessário;
- cada mecânica encontrada em até dois passos após a tab principal.

---

## Fase 5 — Responsividade e alinhamento visual aprovado

**Objetivo:** corrigir UI-010 a UI-019 sem alterar lógica.

### Ações de design

1. Aplicar tokens do tema aprovado claro/bege.
2. Preservar linguagem pixel art e SVG customizado.
3. Remover paleta neon escura somente após decisão da Fase 0.
4. Trocar tamanhos absolutos de 6–10 px por escala `clamp()` com piso legível.
5. Ajustar `#ui-operator-tag` para espaço flexível e truncamento informativo.
6. Corrigir Social 320:
   - reaction bar com wrap/grid;
   - sem `scrollWidth > viewport`.
7. Corrigir Season Pass:
   - label fora da track ou overlay legível;
   - barra sem clipping.
8. Corrigir corte de 3 px no stage em 1024.
9. Aplicar touch targets por `pointer:coarse`, não apenas largura.
10. Tratar 2560+ e 4K com largura útil e tipografia adequadas à distância.
11. Respeitar safe-area em header, bottom nav e modais.

### Metas mensuráveis

| Métrica | Meta |
|---|---|
| Overflow horizontal | 0 em todas as tabs/resoluções |
| Touch target coarse | mínimo 44×44 px |
| Texto funcional | mínimo 12 px; preferível 14 px |
| Pane visível em notebook | sem área útil inferior a 320 px, salvo modal |
| Elementos clipped | 0 fora de truncamentos intencionais |
| Ícones ausentes | 0 |
| Emojis | 0 |

### Aceite

- screenshots comparados com baseline aprovado;
- visual consistente nos cinco breakpoints;
- nenhuma cor/fonte genérica introduzida;
- service worker atualizado e cache invalidado.

---

## Fase 6 — Acessibilidade, teclado e PWA

**Objetivo:** tornar a interface operável sem mouse e semanticamente coerente.

### Ações

1. Implementar padrão WAI-ARIA Tabs:
   - ArrowLeft/ArrowRight;
   - Home/End;
   - roving tabindex;
   - foco visível.
2. Corrigir focus trap para `.modal-wrap.active` visível.
3. Escape fecha modal quando seguro.
4. `role=dialog`, `aria-modal`, labels e descriptions para todos os modais.
5. Labels reais para inputs de Staking, Decoder, Chat, Friends e Market.
6. Remover `user-scalable=no` e `maximum-scale=1`.
7. Limitar `user-select:none` a controles; liberar texto/inputs/TXIDs.
8. Corrigir AudioContext:
   - aguardar `resume()`;
   - não iniciar oscillator suspenso;
   - manter opção de som desligado.
9. Confirmar banner PWA e foco após update/dismiss.
10. Respeitar `prefers-reduced-motion` e forced colors.

### Testes

- navegar cinco tabs sem mouse;
- abrir/fechar cada modal por teclado;
- focus nunca escapa ao fundo;
- zoom a 200%;
- leitor de tela identifica nome/estado dos controles;
- reduced motion sem animações essenciais perdidas.

### Aceite

- zero bloqueio de teclado;
- zero modal sem nome acessível;
- contraste e foco aprovados;
- PWA update operável.

---

## Fase 7 — Sustentabilidade técnica e regressão

**Objetivo:** reduzir risco de o layout/mecânicas voltarem a se misturar.

### Ações

1. Remover/arquivar `style.css` e atualizar Docker/README.
2. Dividir `game.js` por domínio, sem mudar comportamento:
   - core/session;
   - api/client;
   - ui/tabs;
   - ui/modals;
   - mechanics/season;
   - mechanics/staking;
   - mechanics/market;
   - mechanics/decoder;
   - mechanics/social;
   - mechanics/competition.
3. Substituir monkey patches por hooks/event bus tipado/documentado.
4. Criar wrapper fetch com:
   - AbortController por geração;
   - timeout real;
   - parsing de erro;
   - feedback consistente.
5. Adicionar testes DOM/E2E para:
   - modais;
   - tabs;
   - Market;
   - Staking;
   - Decoder;
   - Pool/Guilda;
   - troca de realm;
   - matriz responsiva.
6. Tornar auditor CDP parte de CI/manual release gate.
7. Salvar métricas em JSON UTF-8 e limpar screenshots antigos antes de cada run.

### Aceite

- nenhum arquivo JS monolítico concentra todas as mecânicas;
- testes falham para regressões `hidden active`, IDs duplicados e overflow;
- documentação reflete assets realmente carregados;
- auditoria independente final sem crítico/alto.

---

## Checklist obrigatório ao final de cada fase

```text
[ ] Teste RED reproduziu o bug antes da correção
[ ] Teste GREEN passou após a correção
[ ] pytest completo passou
[ ] node --check passou
[ ] git diff --check passou
[ ] docker compose up --build -d executado
[ ] 7/7 serviços healthy
[ ] smoke REST passou
[ ] smoke WebSocket passou
[ ] smoke funcional da mecânica passou
[ ] CDP 320/768/1024/1440/2560 passou
[ ] screenshots comparadas
[ ] console sem erro novo
[ ] agent independente não encontrou crítico/alto
[ ] relatório/checkpoint atualizado
```

## Sequência recomendada imediata

1. Executar Fase 0 e confirmar fonte visual.
2. Aplicar Fase 1 isoladamente; não misturar com redesign.
3. Aplicar cada item da Fase 2 em subcheckpoints: Decoder, Staking, Market, identidade.
4. Corrigir lifecycle na Fase 3 antes de reorganizar DOM.
5. Só então mover mecânicas na Fase 4.
6. Aplicar tokens/responsividade na Fase 5 sobre a arquitetura já estável.
7. Fechar acessibilidade e modularização nas Fases 6–7.

Essa ordem evita maquiar bugs funcionais com CSS e evita refazer o layout depois de corrigir a estrutura das mecânicas.
