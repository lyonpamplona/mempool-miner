# Auditoria técnica

Data da revisão: 14 de agosto de 2026.

## Sumário executivo

A leitura inicial encontrou quatro riscos de impacto imediato:

1. credencial RPC fixa e portas sensíveis expostas;
2. quatro workers duplicando todos os eventos ZMQ;
3. XSS persistente pelo nickname do leaderboard;
4. pontuação inteiramente confiada ao navegador.

Os três primeiros foram mitigados na aplicação principal. O quarto exige
mudança de arquitetura e permanece aberto. Também foram corrigidos bugs de
grade insolúvel, touch acumulado, estado após block_mined, matriz 15×15,
coordenadas SVG, taxa absoluta, atualização não atômica e contaminação entre
redes. Regtest e Signet agora podem operar simultaneamente; Mainnet podada é
opt-in por profile.

## Escopo revisado

Todos os arquivos executáveis e de configuração existentes no início da
auditoria foram lidos integralmente. A tabela registra o snapshot após as
correções; o hash curto ajuda a identificar a versão analisada.

| Arquivo | Linhas | SHA-256 curto | Resultado |
|---|---:|---|---|
| backend/app/__init__.py | 1 | 12CEC4DDFADD | sem achado |
| backend/app/blockchain.py | 115 | 9D85ED55FD83 | listener supervisionado / dívida de replay ZMQ |
| backend/app/config.py | 184 | 6FFE6F8B3C67 | catálogo e identidade multi-rede validados |
| backend/app/engine.py | 155 | 3FBF56EC70D6 | RPC validado / reconciliação implementada |
| backend/app/events.py | 81 | 211DB51A2067 | envelope de eventos v2 implementado |
| backend/app/ingestor.py | 518 | 356FACC7ACD8 | ingestor por realm / commits com lease fenced |
| backend/app/ingestor_healthcheck.py | 59 | 48D6AA5314A4 | identidade, lease e heartbeat validados |
| backend/app/main.py | 342 | 44D1634872A1 | API multi-rede / risco de score permanece |
| backend/app/storage.py | 88 | 1EEE8DADD143 | namespace por realm / migração atômica |
| backend/Dockerfile | 19 | 7D9C4A925DC5 | endurecido |
| backend/requirements.txt | 9 | 7C0EDFDF9A8A | atualização parcial |
| backend/tests/test_engine.py | 88 | DB4B62504B2B | contratos RPC cobertos |
| backend/tests/test_models.py | 68 | 1C567E2AEEE9 | modelos e validações cobertos |
| backend/tests/test_multi_network.py | 476 | 680BF20CC5E0 | isolamento, epoch e lease cobertos |
| bitcoin/bitcoin.conf | 23 | 6A59A0F50980 | base comum sem segredo versionado |
| docker-compose.yaml | 343 | 84954499ED06 | três redes / runtime Docker pendente |
| frontend/Dockerfile | 8 | 45D6E1BF6CF2 | ajustado |
| frontend/nginx.conf | 40 | 6A69CCCDAFB8 | novo proxy |
| frontend/index.html | 149 | 8FE6F05505D4 | seletor e status de rede adicionados |
| frontend/style.css | 168 | DB29EA687355 | responsivo / estados multi-rede |
| frontend/game.js | 1058 | C66D3ABDC598 | sessões isoladas / score local permanece |
| prototipo-v2.html | 653 | F32CE984D66F | legado sinalizado, fora do runtime |
| prototipo-game-L2.html | 566 | FEFF694FFD66 | legado sinalizado, fora do runtime |
| guia-apresentacao.html | 201 | 8AD67DC45DC0 | substituído e revisado |
| .github/workflows/ci.yml | 128 | 5D75DF441791 | smoke ZMQ multi-rede definido, não executado |

Arquivos criados depois da leitura foram revisados por sintaxe, links, XML/HTML
e consistência cruzada.

## Método

- inventário com rg e contagem por arquivo;
- leitura manual linha a linha de Python, JS, HTML, CSS, YAML e configuração;
- mapeamento de entrada → transformação → persistência → saída;
- análise de fronteiras de confiança e concorrência;
- compilação Python e verificação de sintaxe JavaScript;
- consulta a fontes primárias para versões/advisories;
- revisão independente em três frentes: backend, frontend e DevOps;
- testes unitários adicionados para contratos críticos.

Não havia repositório Git no início, então histórico, branches, remotos e
vazamentos passados não puderam ser auditados.

## Escala

| Nível | Critério |
|---|---|
| P0 crítico | exposição/execução remota, perda ampla ou runtime fundamentalmente incorreto |
| P1 alto | fraude, indisponibilidade recorrente ou estado incorreto relevante |
| P2 médio | robustez, operação, UX ou manutenção com impacto controlado |
| P3 baixo | qualidade e consistência sem falha imediata |

## Achados corrigidos

### FIX-001 — Eventos ZMQ multiplicados

Inicialmente o Compose usava quatro workers; cada processo criava listener e
lifespan próprios. Agora `app.main` não abre ZMQ/RPC e cada `ingestor-*` executa
`python -m app.ingestor` uma única vez por realm.

Status: corrigido arquiteturalmente. A API pode ser escalada sem multiplicar os
listeners. Commits Redis do ingestor são condicionados à lease/token do realm;
uma instância antiga perde o direito de publicar após takeover.

### FIX-002 — Credenciais e portas de dados

bitcoin.conf não contém mais usuário/senha. Redis, RPC, ZMQ e FastAPI não
publicam portas no host; somente Nginx liga 127.0.0.1:8010. Redes e volumes foram
separados.

Status: mitigado. Cada nó aceita credencial própria e a API não recebe segredos,
mas os valores ainda passam por ambiente/argv. A credencial local conhecida
deve ser rotacionada; rpcauth e secret manager ainda não foram implementados.

### FIX-003 — XSS persistente

O ranking construía `innerHTML` com `miner.username`. A implementação atual usa
`replaceChildren`, cria elementos e atribui conteúdo externo apenas com
`textContent`. Palavras do WebSocket seguem a mesma fronteira segura.

Status: corrigido no runtime principal. Protótipos legados não devem ser
publicados.

### FIX-004 — Ranking não atômico e entrada ilimitada

ScoreSubmit limita username/score e `submit_score_for_realm` usa ZADD GT + CH
em uma única operação, informando também se o registro mudou.

Status: corrigida a corrida; autenticidade do score permanece aberta.

### FIX-005 — Fila sem limite e erros invisíveis

A fila de cada NodeIngestor possui maxsize configurável. `put_nowait` descarta e
mede rawtx excedente sem bloquear hashblock; shutdown cancela e aguarda tarefas.

Status: corrigido para limite/descarte. Queue depth e descarte entram no
heartbeat; lag e métricas exportáveis continuam pendentes.

### FIX-006 — Classificação errada de taxa

GameEngine converte fees.base para satoshis e divide por vsize, usando limiar
configurável. O valor é enviado como fee_rate_sat_vb.

Status: corrigido e coberto por teste.

### FIX-007 — Bugs da grade

- palavras não se sobrepõem;
- montagem possui fallback/retry;
- listeners de toque são registrados uma vez;
- seleção mantém vetor reto;
- células respondem à viewport;
- SVG calcula coordenadas no próprio sistema;
- `block_mined` desativa a partida e descarta o buffer antigo.

Status: corrigido no runtime principal.

### FIX-008 — Mixed content e porta fixa

O cliente usa mesma origem e o Nginx encaminha /api e /ws. Isso permite TLS na
borda sem alterar game.js.

Status: corrigido.

### FIX-009 — Persistência e prontidão

Redis ganhou AOF/volume; nós, API, frontend e ingestores têm healthchecks. O
healthcheck do ingestor valida heartbeat recente, token local e lease ativa, e
`depends_on` aguarda saúde.

Status: implementado, ainda sem smoke test local por ausência de Docker.

### FIX-010 — Acessibilidade e responsividade básicas

Zoom foi liberado, contraste aumentado, scroll/restack móvel adicionado, modais
ganharam semântica, foco visível e reduced motion.

Status: parcial; teclado completo e focus trap permanecem.

### FIX-011 — Transições e contratos do cliente

O modo L2 agora entra por uma transição atômica que não inicia a rodada atrás do
modal. Frames WebSocket e respostas do leaderboard são validados antes do uso;
um build pendente é cancelado na desconexão e exige socket aberto.

Status: corrigido no runtime principal; faltam testes E2E para as corridas de
eventos.

### FIX-012 — Isolamento multi-rede e Mainnet opcional

Catálogo, eventos, contador, epoch e leaderboard são namespaced por `realm_id`.
Cada Core possui rede de controle e volume próprios; Signet/Mainnet usam gateway
P2P explícito. Mainnet e seu ingestor compartilham `profiles: [mainnet]`, usam
`prune=10240` por padrão e não são dependência da API.

Status: implementado estaticamente; build/up/smoke reais dependem de Docker/CI.

### FIX-013 — Corridas de epoch, contador e takeover

Metadados RPC são revalidados sob a barreira de epoch. TX, bloco, heartbeat e
shutdown usam scripts Redis que comparam a lease antes do commit. O contador é
reconciliado com `getmempoolinfo.size`, e o token interno não entra no contrato
público. Testes determinísticos cobrem epoch antiga, token obsoleto, shutdown
atômico e healthcheck de outra instância.

Status: corrigido no processo singleton; HA com múltiplos nós continua fora do
escopo atual.

## Achados abertos

### AUD-001 — Score controlado pelo cliente

Severidade: P1 alta.

frontend/game.js calcula saldo/recompensa e POSTa o total. Um cliente pode enviar
qualquer score dentro do limite. Nickname não representa uma identidade.

Impacto: fraude, impersonação e leaderboard sem valor competitivo.

Correção: sessão autenticada, eventos de ação no servidor, regra de pontuação
autoritativa, idempotência e rate limiting.

### AUD-002 — Sem autenticação/rate limit

Severidade: P1 alta se exposto.

REST e WebSocket aceitam qualquer cliente. Não há limite de conexões,
submissões, membros no Sorted Set ou validação explícita de Origin do WebSocket.

Correção: proxy rate limit, autenticação, quotas e retenção.

### AUD-003 — Semântica ZMQ incompleta

Severidade: P1 alta em signet/mainnet.

O listener agora lê o terceiro frame de sequência, identifica a sessão, deduplica
TXID por epoch e invalida backlog ao chegar hashblock. Ainda não interpreta toda
a semântica do tópico `sequence`, detecta saltos nem reconcilia com um log
durável. Pub/Sub não oferece replay.

O contador numérico é reconciliado periodicamente e em cada evento processado,
mas gaps/restart ainda podem perder quais transações viraram itens do jogo,
principalmente sob carga Mainnet.

Correção restante: interpretar eventos A/R e gaps do tópico `sequence`,
reconciliar a lista com `getrawmempool` e adotar stream durável.

### AUD-004 — Throughput artificial

Severidade: P1 alta em mainnet, P2 em regtest.

Regtest/Signet publicam por padrão até uma transação por segundo; Mainnet usa
intervalo de 0,25 s. Backpressure impede RAM ilimitada, mas pode descartar itens
e aumentar latência sob uma mempool movimentada.

Correção: separar ingestão do sampling de UI; consumir em lote, medir lag e
definir descarte/coalescência.

### AUD-005 — RPC ainda usa senha em ambiente/argumento

Severidade: P2 média no Compose privado.

O segredo não está no Git, mas pode aparecer em inspect/processo. rpcallowip
ainda é amplo dentro da rede de dados.

Correção: rpcauth, secrets, subnet exata e rotação.

### AUD-006 — Dependências e supply chain

Severidade: P2 média.

Transitivas não têm lock/hashes, imagens não estão por digest, GitHub Actions
usam tags de versão em vez de SHA e a imagem Bitcoin é de terceiros. FastAPI foi
atualizado por advisory conhecido; demais saltos precisam de matriz de
compatibilidade.

Correção: lock, SBOM, pip-audit/Trivy, assinatura/proveniência e promoção.

### AUD-007 — Reconexão WebSocket

Severidade: P2 média.

O cliente invalida a geração, detecta heartbeat expirado e permite escolher a
rede novamente, mas não reconecta automaticamente e Pub/Sub não reenvia.

Correção restante: backoff com jitter, stream durável e retomada idempotente.

### AUD-007A — HA entre dois nós do mesmo realm

O desenho single-node usava canal, contador e leaderboard globais. Agora
Regtest, Signet e Mainnet possuem `realm_id`, canais/chaves com hash-tag Redis,
filas/epochs, volumes e redes Docker independentes. Todo evento declara
network/node/realm/source e o frontend rejeita realm divergente.

Status: a contaminação foi corrigida para um nó por realm. Lease com commit
condicional impede dois publicadores do mesmo namespace, mas HA com múltiplas
origens, failover, dedupe entre fontes e reorg continuam abertos.

### AUD-008 — Acessibilidade incompleta

Severidade: P2 média.

A grade não possui operação completa por teclado; modais não implementam
focus trap, Escape e restauração de foco. Áudio não possui controle.

Correção: modelo de navegação de grid, gerenciador de diálogo e preferências.

### AUD-009 — Protótipos divergentes

Severidade: P3 baixa enquanto não publicados.

Os protótipos contêm lógica mock antiga, inclusive sobreposição e listeners
repetidos. Podem confundir usuários e não recebem hardening de produção.

Correção: mover para examples/legacy, adicionar aviso visível e bloquear sua
publicação.

### AUD-010 — Ausência de testes de integração

Severidade: P2 média.

Testes unitários cobrem contratos, epoch e lease. Um workflow agora constrói a
stack, prepara Regtest, envia uma transação, observa contador/heartbeat, minera
um bloco e verifica mudança da epoch. Ele ainda não foi executado neste
repositório sem remoto; não há evidência local de WebSocket, carga, mobile ou
E2E.

Correção: stack efêmera em CI, fixtures regtest e Playwright.

### AUD-011 — Hardening operacional incompleto

Severidade: P2 média antes de produção.

`no-new-privileges` e o usuário não-root do backend reduzem a superfície, mas o
Nginx ainda usa o modelo padrão com processo mestre root. Os serviços não usam
filesystem somente leitura nem `cap_drop`; não há rotação explícita de logs. A
aplicação dos limites em `deploy.resources` deve ser confirmada na implementação
de Compose escolhida.

Correção: imagem Nginx não-root/porta alta, capabilities mínimas, `read_only` +
`tmpfs`, driver/rotação de logs e teste dos limites no runtime de destino.

### AUD-012 — Redis Cluster não suportado

Severidade: P3 no Compose atual, que usa Redis standalone.

Os commits fenced e a migração legada usam Lua multi-chave. Algumas chaves
operacionais não compartilham a mesma hash-tag; em Redis Cluster isso resulta em
`CROSSSLOT`. Não habilite Cluster sem redesenhar os slots e preservar a
atomicidade por realm.

## Dependências

O inventário inicial usava FastAPI 0.104.1, afetado por CVE-2024-24762 em
processamento multipart. O caminho não estava ativado, mas a dependência foi
elevada para uma versão corrigida. pip-audit também detectou
PYSEC-2026-2270/CVE-2026-28684 em python-dotenv 1.0.0; a versão foi elevada para
1.2.2. Consulte [DEPENDENCIAS.md](DEPENDENCIAS.md).

## Limitações da validação

- Docker não está instalado neste host; config/build/up/health não puderam ser
  executados localmente;
- sem Git anterior, não foi possível procurar segredos no histórico;
- não houve tráfego Bitcoin real, teste de carga ou navegador automatizado;
- os testes locais rodaram em Python 3.14 e emitiram avisos de depreciação do
  pytest-asyncio; a imagem de runtime usa Python 3.11.

Essas limitações não invalidam achados estáticos, mas impedem declarar a stack
pronta para produção.

## Evidências de validação

- 39 testes pytest aprovados;
- Ruff check e format check aprovados;
- compileall do backend aprovado;
- node --check em game.js e api-page.js aprovado;
- pip-audit 2.10.1: nenhuma vulnerabilidade conhecida no conjunto resolvido;
- parsing básico de 6 HTML, 24 Markdown, 6 SVG e 115 links locais validado;
- 8 arquivos YAML analisados sintaticamente;
- Docker Compose não executado porque o binário Docker está ausente.
