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
coordenadas SVG, taxa absoluta e atualização não atômica.

## Escopo revisado

Todos os arquivos executáveis e de configuração existentes no início da
auditoria foram lidos integralmente. A tabela registra o snapshot após as
correções; o hash curto ajuda a identificar a versão analisada.

| Arquivo | Linhas | SHA-256 curto | Resultado |
|---|---:|---|---|
| backend/app/__init__.py | 1 | 12CEC4DDFADD | sem achado |
| backend/app/blockchain.py | 71 | FCE2970C5FB6 | corrigido / dívida ZMQ |
| backend/app/engine.py | 128 | ACC3C6EE5A38 | corrigido |
| backend/app/main.py | 245 | FB9DBAA47E85 | corrigido / risco de score |
| backend/Dockerfile | 19 | 7D9C4A925DC5 | endurecido |
| backend/requirements.txt | 9 | 7C0EDFDF9A8A | atualização parcial |
| bitcoin/bitcoin.conf | 25 | 9ED3CBE53D33 | segredo removido / restrição pendente |
| docker-compose.yaml | 132 | 64865A51D7EF | endurecido, não executado localmente |
| frontend/Dockerfile | 8 | 45D6E1BF6CF2 | ajustado |
| frontend/nginx.conf | 40 | 6A69CCCDAFB8 | novo proxy |
| frontend/index.html | 138 | CDC4B967128F | acessibilidade parcial |
| frontend/style.css | 158 | 065DD3A550FB | responsivo |
| frontend/game.js | 723 | E83CB807F71D | corrigido / score local |
| prototipo-v2.html | 653 | F32CE984D66F | legado sinalizado, fora do runtime |
| prototipo-game-L2.html | 566 | FEFF694FFD66 | legado sinalizado, fora do runtime |
| guia-apresentacao.html | 201 | 8AD67DC45DC0 | substituído e revisado |

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
lifespan próprios. Agora Compose e Dockerfile fixam um worker
(docker-compose.yaml:67, backend/Dockerfile:19).

Status: mitigado. A separação definitiva do ingestor continua no roadmap.

### FIX-002 — Credenciais e portas de dados

bitcoin.conf não contém mais usuário/senha. Redis, RPC, ZMQ e FastAPI não
publicam portas no host; somente Nginx liga 127.0.0.1:8010. Redes e volumes foram
separados.

Status: mitigado. A credencial local conhecida deve ser rotacionada. rpcauth e
secret manager ainda não foram implementados.

### FIX-003 — XSS persistente

O ranking construía innerHTML com miner.username. A implementação atual cria
spans e usa textContent (frontend/game.js:268–278). Palavras do WebSocket também
são renderizadas por nós de texto (frontend/game.js:542–550).

Status: corrigido no runtime principal. Protótipos legados não devem ser
publicados.

### FIX-004 — Ranking não atômico e entrada ilimitada

ScoreSubmit limita username/score (backend/app/main.py:40–62) e ZADD GT + CH faz
a atualização de máximo em uma operação, informando também se o registro mudou
(linhas 163–172).

Status: corrigida a corrida; autenticidade do score permanece aberta.

### FIX-005 — Fila sem limite e erros invisíveis

A fila agora possui maxsize configurável (backend/app/main.py:31–34). RPC,
processamento e ZMQ geram logs; shutdown cancela e aguarda tarefas.

Status: mitigado. Falta política de descarte, sequência e métricas.

### FIX-006 — Classificação errada de taxa

GameEngine converte fees.base para satoshis e divide por vsize, usando limiar
configurável. O valor é enviado como fee_rate_sat_vb.

Status: corrigido e coberto por teste.

### FIX-007 — Bugs da grade

- palavras não se sobrepõem (frontend/game.js:496–502);
- montagem possui fallback/retry;
- listeners de toque são registrados uma vez (linhas 166–167);
- seleção mantém vetor reto (linhas 581–599);
- células respondem à viewport (linhas 101–108);
- SVG calcula coordenadas no próprio sistema (linhas 672–675);
- block_mined desativa a partida e descarta buffer antigo (linhas 234–250).

Status: corrigido no runtime principal.

### FIX-008 — Mixed content e porta fixa

O cliente usa mesma origem e o Nginx encaminha /api e /ws. Isso permite TLS na
borda sem alterar game.js.

Status: corrigido.

### FIX-009 — Persistência e prontidão

Redis ganhou AOF/volume, serviços têm healthchecks e depends_on aguarda saúde.

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

O listener ignora frame de sequência, não deduplica rawtx e não invalida itens
da fila ao chegar hashblock. Pub/Sub não oferece replay.

Impacto: contador e rodadas podem usar evento repetido, perdido ou antigo.

Correção: tópico sequence, época de bloco, reconciliação periódica e stream
durável.

### AUD-004 — Throughput artificial

Severidade: P1 alta em mainnet, P2 em regtest.

Um consumidor publica por padrão uma transação por segundo. Backpressure impede
RAM ilimitada no processo, mas pode acumular no socket e aumentar latência.

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

O cliente exibe perda de conexão, mas não reconecta e Pub/Sub não reenvia. Uma
queda exige reload.

Correção: backoff com jitter, snapshot/epoch e retomada idempotente.

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

Testes unitários cobrem contratos básicos. Um workflow agora constrói a stack e
testa health/Redis, mas ainda não foi executado neste repositório sem remoto; não
há evidência automatizada de transações regtest, WebSocket, concorrência, mobile
ou E2E.

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

- 11 testes pytest aprovados;
- Ruff check e format check aprovados;
- compileall do backend aprovado;
- node --check em game.js e api-page.js aprovado;
- pip-audit 2.10.1: nenhuma vulnerabilidade conhecida no conjunto resolvido;
- parsing básico de 6 HTML, 24 Markdown, 6 SVG e 108 links locais validado;
- 8 arquivos YAML analisados sintaticamente;
- Docker Compose não executado porque o binário Docker está ausente.
