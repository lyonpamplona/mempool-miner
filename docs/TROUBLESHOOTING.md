# Troubleshooting

## A página não abre

    docker compose ps
    docker compose logs --tail 100 frontend backend

Confirme que a porta 8010 não está ocupada. O bind é somente 127.0.0.1.

## Backend unhealthy

    docker compose logs --tail 200 backend
    docker compose exec redis redis-cli ping
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getblockchaininfo'

Causas frequentes:

- credencial específica da rede (ou fallback RPC_USER/RPC_PASSWORD) ausente;
- ingestor apontando para host/porta diferentes do serviço correspondente;
- Redis/Bitcoin ainda iniciando;
- senha do ingestor diferente da passada ao Bitcoin;
- valor numérico inválido no .env.

## “Aguardando transações” não termina

Em regtest o entrypoint (`bitcoin/entrypoint.sh`) já cria a wallet `miner`,
gera 150 blocos e envia 10 transações ao mempool automaticamente. Se a mempool
estiver vazia, verifique os logs do entrypoint:

    docker compose logs --tail 50 bitcoin-regtest | grep entrypoint

Se o RPC não ficou pronto a tempo (cold start), o script loga o erro mas o
bitcoind segue rodando — execute manualmente os passos do
[TUTORIAL.md](TUTORIAL.md) (loadwallet, generatetoaddress, sendtoaddress).

Outras causas:

- menos de seis palavras únicas;
- listener ZMQ não conectado;
- fila atrasada pelo intervalo de processamento;
- transação já confirmada;
- RPC não encontrou getmempoolentry e houve logs de warning.

Diagnóstico:

    docker compose logs -f backend ingestor-regtest bitcoin-regtest
    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" getrawmempool'
    docker compose exec redis redis-cli GET "mempool_miner:v2:{regtest}:mempool_count"

## WebSocket desconecta

No DevTools, confirme `/ws/v1/game/regtest` com status 101. Revise Nginx:

    docker compose logs --tail 100 frontend

Se houver proxy/TLS externo, ele também precisa encaminhar Upgrade e Connection
e permitir timeout longo.

## Ranking vazio ou não atualiza

    Invoke-RestMethod http://localhost:8010/api/v1/networks/regtest/leaderboard
    docker compose exec redis redis-cli ZCARD "mempool_miner:v2:{regtest}:leaderboard"

HTTP 422 no POST indica nickname/score inválido. Nomes aceitam apenas letras,
números, hífen e sublinhado e têm até 12 caracteres.

## Grade cortada

Recarregue após redimensionar e confirme que pixel.css/game.js não estão em
cache. O código calcula célula por viewport. Em telas muito estreitas o layout
se torna vertical e a página permite rolagem.

## createwallet informa que já existe

    docker compose exec bitcoin-regtest sh -lc 'bitcoin-cli -regtest -rpcuser="$RPC_USER" -rpcpassword="$RPC_PASSWORD" loadwallet miner'

Se já estiver carregada, continue usando -rpcwallet=miner.

## Docker não é reconhecido

Instale/inicie Docker Desktop e abra um novo terminal. Este repositório não
inclui o daemon Docker. Em Windows:

    docker context ls
    docker info

## Erro de imagem Bitcoin

Confirme arquitetura, conectividade com Docker Hub e existência da tag:

    docker pull bitcoin/bitcoin:31.1

A imagem é voltada a laboratório. Não troque a tag em um nó persistente sem
backup e teste de compatibilidade.

## Loop infinito no botão RBF

Sintoma: clicar no botão de RBF dispara múltiplas requisições simultâneas ou
o botão continua respondendo após a ação ser concluída.

Causa: o handler `onclick` não era removido após a execução, permitindo
re-disparo.

Solução: `btn.onclick = null` foi adicionado em ambos os fluxos (sucesso e
erro). Se o problema persistir, force uma limpeza de cache do navegador
(Ctrl+Shift+Delete) e recarregue.

## Sessão perdida ao recarregar a página

Sintoma: ao dar F5 ou navegar para fora e voltar, o progresso da partida é
perdido.

Causa (versões anteriores a 16/08/2026): o estado da sessão não era
persistido entre navegações.

Solução: a partir de 16/08/2026, `sessionStorage` salva o estado em 9 pontos
críticos. Se o problema persistir:

1. Verifique que o navegador não está em modo anônimo (sessionStorage é
   limpo ao fechar a aba em alguns navegadores);
2. Confirme que cookies e dados de site não estão sendo bloqueados;
3. No DevTools → Application → Session Storage, verifique a chave
   `mempool_miner_session`.

## Sincronização de epoch

Sintoma: o frontend mostra transações de uma epoch anterior ao que o backend
está processando.

Solução: o frontend verifica a epoch atual periodicamente e reconecta
automaticamente ao WebSocket quando detecta uma divergência. Se o problema
persistir, force uma reconexão manual recarregando a página.

## Recuperação

Prefira:

    docker compose restart SERVICO
    docker compose up -d --build SERVICO

Não use down --volumes como tentativa genérico: ele remove ranking, carteira e
blockchain local.
