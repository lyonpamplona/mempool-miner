# Roadmap de correção e evolução

O roadmap parte do estado entregue, não do código original. Prioridade combina
risco, dependências e valor de validação.

## Progresso em 2026-08-14

- [x] API desacoplada da ingestão ZMQ;
- [x] um ingestor/volume/rede Redis por realm;
- [x] Regtest + Signet no Compose padrão;
- [x] Mainnet pruned sob profile opcional;
- [x] catálogo, health, leaderboard e WebSocket por realm;
- [x] frontend com troca transacional de sessão e heartbeat;
- [x] epoch, dedupe de TXID e descarte de backlog em bloco;
- [x] barreira de epoch, reconciliação periódica e lease singleton por realm;
- [ ] validação real do Compose/build/smoke — Docker não está instalado no host;
- [ ] `rpcauth`/secrets por rede e binário Mainnet verificado;
- [ ] HA com dois nós da mesma arena e replay durável.

## Fase 0 — Antes do primeiro push

Prazo sugerido: imediato. Esforço: pequeno.

### R0.1 Rotacionar credencial RPC

- gerar usuário/senha novos no .env local;
- confirmar que .env está ignorado;
- se houve compartilhamento anterior, pesquisar/limpar histórico e revogar o
  valor antigo.

Aceite:

    git check-ignore -v .env
    git ls-files .env

O segundo comando retorna vazio.

### R0.2 Executar validação Docker

- o workflow de CI já contém build, health, transação ZMQ e bloco Regtest;
- instalar/iniciar Docker;
- reproduzir config, build, up e smoke localmente e confirmar a primeira CI;
- testar health, WS, seis transações e hashblock;
- registrar versão/digest das imagens validadas.

Aceite: topologia Regtest isolada healthy, catálogo correto e tutorial Regtest
concluído; config do profile Mainnet validada separadamente.

### R0.3 Definir licença e proprietário

- escolher licença;
- adicionar LICENSE e, se necessário, CODEOWNERS;
- definir contato privado de segurança.

## Fase 1 — Integridade competitiva

Prazo sugerido: 1–2 sprints. Esforço: grande.

### R1.1 Sessões de jogador

- identidade anônima assinada ou conta;
- token curto, expiração e rotação;
- nickname separado do identificador.

### R1.2 Motor de partida autoritativo

- browser envia seleção/compra, não score final;
- servidor valida grade, tempo, recompensa e saldo;
- cada ação possui game_id e idempotency_key;
- leaderboard deriva de eventos aceitos.

### R1.3 Proteções de abuso

- rate limit por IP/sessão;
- limite de WebSockets e mensagens;
- retenção/limite do Sorted Set;
- validação de Origin;
- telemetria de rejeições.

Aceite: POST arbitrário não altera score; replay não duplica recompensa; duas
sessões concorrentes mantêm saldo consistente.

## Fase 2 — Pipeline de eventos confiável

Prazo sugerido: 1–2 sprints. Esforço: grande.

### R2.1 Extrair ingestor singleton — concluído

`python -m app.ingestor` é executado uma vez por realm. A API não abre ZMQ/RPC.

### R2.2 Sequência e reconciliação — parcial

- [x] ler sequence do frame ZMQ e identificar a sessão;
- [x] associar evento a epoch e descartar backlog anterior ao bloco;
- [x] deduplicar TXID dentro da epoch;
- [x] reconciliar `mempool_count` periodicamente com `getmempoolinfo.size`;
- [ ] consumir a semântica completa do tópico `sequence`;
- [ ] armazenar sequência por tópico;
- detectar saltos;
- reconciliar a lista/identidade completa com `getrawmempool` após saltos;

### R2.4 Multi-rede Docker — concluído, pendente smoke real

- Regtest e Signet sobem por padrão com datadirs independentes;
- Mainnet e seu ingestor compartilham `profiles: [mainnet]`;
- Mainnet usa pruning configurável e não bloqueia a API quando ausente/IBD;
- RPC/ZMQ ficam em redes de controle exclusivas de cada par nó/ingestor;
- leaderboard, canal, contador, estado e epoch são isolados por realm.

### R2.5 Multi-node HA por realm — futuro

- [x] impedir dois publicadores acidentais com lease Redis por realm;
- registro de dois ou mais nós para o mesmo realm;
- eleição/failover com `stream_id` e epoch canônica;
- dedupe de TXID/hash entre origens e tratamento de reorg;
- log durável para replay e `resync_required` em descontinuidade.

### R2.3 Separar ingestão de sampling

Ingerir na velocidade da fonte e escolher eventos do jogo em uma camada própria.
Adicionar métricas queue_depth, event_lag_seconds, duplicates_total e
reconciliation_total.

Aceite: teste com perda/repetição não altera estado final; nenhuma fila cresce
sem limite sob carga-alvo.

## Fase 3 — Segurança operacional

Prazo sugerido: 1 sprint. Esforço: médio.

### R3.1 Segredos

- gerar rpcauth;
- Docker/Kubernetes secret;
- rpcallowip para subnet exata;
- procedimento de rotação.

### R3.2 Supply chain

- lock transitivo com hashes;
- SBOM de pacotes e imagens;
- pip-audit e scanner de imagem como checks obrigatórios;
- imagens/actions por digest/SHA;
- verificação dos binários Bitcoin.

### R3.3 Borda

- TLS/HSTS;
- CSP sem handlers inline;
- cabeçalhos e limites Nginx;
- logs sem dados sensíveis.

### R3.4 Containers e operação

- Nginx não-root em porta alta;
- `cap_drop`, filesystem somente leitura e `tmpfs` mínimo;
- rotação de logs e limites confirmados no runtime;
- backup/restauração periódicos de Redis e Bitcoin Core.

Aceite: threat model revisado, scans sem vulnerabilidade crítica não aceita e
rotação testada.

## Fase 4 — Testes e observabilidade

Prazo sugerido: contínuo. Esforço: médio.

- [x] ampliar o smoke para transação Regtest, contador e mudança de epoch;
- testes WebSocket e shutdown;
- concorrência de score;
- carga ZMQ/fila;
- Playwright em 320, 768 e 1440 px;
- teste de toque após várias rodadas;
- dashboards, tracing, alertas e SLO.

Aceite: fluxo do tutorial executado automaticamente e rollback ensaiado.

## Fase 5 — UX e acessibilidade

Prazo sugerido: 1 sprint. Esforço: médio.

- grade operável por teclado;
- focus trap, Escape e retorno de foco;
- controle/mute de áudio;
- anúncio acessível de tempo/acertos;
- internacionalização coerente;
- reconexão WS com snapshot;
- remover handlers/style inline e aplicar CSP.

Aceite: auditoria WCAG 2.2 AA sem bloqueadores e E2E nos navegadores suportados.

## Fase 6 — Organização do produto

Prazo sugerido: oportunístico. Esforço: pequeno/médio.

- mover protótipos para examples/legacy;
- versionar contratos WebSocket;
- publicar releases e changelog;
- decidir se Lightning vira integração real ou permanece narrativa;
- separar documentação pública de runbooks privados.

## Backlog priorizado

| ID | Item | Prioridade | Esforço | Dependência |
|---|---|---|---|---|
| R0.1 | rotação e higiene Git | P0 | P | nenhuma |
| R0.2 | smoke Docker | P0 | P | Docker |
| R1.2 | score autoritativo | P1 | G | R1.1 |
| R2.1 | ingestor separado | concluído | — | — |
| R2.2 | sequência/reconciliação completa | P1 | G | R2.1 |
| R2.4 | smoke real multi-rede/profile | P0 | M | Docker disponível |
| R2.5 | HA multi-node por realm | P1 | G | R2.2 + stream durável |
| R1.3 | rate limit/authz | P1 | M | R1.1 |
| R3.1 | rpcauth/secrets | P1 | M | infraestrutura |
| R4 | integração/E2E | P2 | M | stack estável |
| R5 | WCAG/UX | P2 | M | testes E2E |
| R3.2 | lock/SBOM/digests | P2 | M | CI |
| R6 | limpar legados/releases | P3 | P | decisão de produto |

P = pequeno, M = médio, G = grande.
