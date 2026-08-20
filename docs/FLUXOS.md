# Fluxos do sistema

## 1. Inicialização

~~~mermaid
sequenceDiagram
    participant C as Docker Compose
    participant B as Cores por realm
    participant I as Ingestores
    participant R as Redis
    participant A as FastAPI
    participant N as Nginx
    C->>B: inicia Regtest + Signet (Mainnet é profile)
    C->>R: inicia AOF e aguarda PING
    C->>I: inicia um processo por nó healthy
    I->>B: valida chain, RPC e abre ZMQ
    I->>R: lease + estado/heartbeat por realm
    C->>A: inicia API independente dos nós
    A->>R: PING
    A->>R: migra leaderboard legado para Regtest
    C->>N: inicia após healthcheck da API
~~~

Falha de um Core mantém somente seu ingestor aguardando. API e outros realms
continuam disponíveis. IBD produz `syncing/playable=false`, não health failure.

## 2. Transação Bitcoin → navegador

~~~mermaid
sequenceDiagram
    participant B as Bitcoin Core
    participant Z as BitcoinZMQListener
    participant Q as asyncio.Queue
    participant E as GameEngine
    participant R as Redis
    participant W as WebSocket
    participant U as Browser
    B-->>Z: rawtx + bytes
    Z->>Q: transação hexadecimal
    Q->>E: item da fila limitada
    E->>E: double SHA-256 + endian reverse
    E->>B: getmempoolentry(txid)
    B-->>E: vsize + fees.base
    E->>E: BIP39 + sats/vB + flags
    E->>R: lock de epoch + dedupe + INCR + PUBLISH do realm
    R-->>W: transaction_received
    W-->>U: JSON
    U->>U: deduplica por palavra até 6
~~~

Depois do RPC, a epoch é validada novamente sob o mesmo lock usado por blocos;
assim uma resposta antiga não pode ser publicada depois de `block_mined`. Se o
RPC falhar, a palavra continua com vsize padrão 250 e taxa zero. A fila limita
memória; quando cheia, rawtx é descartada/medida sem bloquear hashblock. O
heartbeat reconcilia o contador com `getmempoolinfo`. Eventos em IBD não viram
partidas.

## 3. Construção da rodada

Quando seis palavras únicas chegam:

1. o browser escolhe 8×8 em modo L2, 15×15 se algum vsize exceder 1000, ou
   12×12 no caso padrão;
2. calcula o tamanho responsivo da célula;
3. posiciona palavras sem sobreposição, com tentativas e fallback;
4. preenche espaços com letras aleatórias;
5. inicia o cronômetro de 20, 60 ou 75 segundos mais bônus elegíveis.

Se a grade não puder ser montada após novas tentativas, a rodada não inicia e a
interface informa a falha.

## 4. Seleção e recompensa

~~~mermaid
stateDiagram-v2
    [*] --> Coletando
    Coletando --> Jogando: 6 palavras
    Jogando --> Selecionando: mouse/toque
    Selecionando --> Jogando: palavra inválida
    Selecionando --> Jogando: palavra válida
    Jogando --> Vitoria: todas encontradas
    Jogando --> Derrota: timeout
    Jogando --> Derrota: hashblock
    Vitoria --> Coletando: próximo bloco
    Derrota --> Coletando: tentar novamente
~~~

A segunda célula fixa o vetor; as próximas devem continuar na mesma linha. Uma
palavra também pode ser selecionada ao contrário.

Pontuação local:

    pontos = (500 + comprimento × 50) × combo

Multiplicadores:

- taxa alta: ×3;
- hash dourado: ×5;
- modo Lightning simulado: ×10;
- combo: cresce 0,5 por acerto em menos de 8 s, limitado a 4.

## 5. Novo bloco

~~~mermaid
sequenceDiagram
    participant B as Bitcoin Core
    participant I as Ingestor do realm
    participant R as Redis
    participant U as Browser
    B-->>I: hashblock + sequence
    I->>I: avança epoch e drena backlog antigo
    I->>B: getmempoolinfo
    I->>R: SET contador/epoch do realm
    I->>R: PUBLISH block_mined do realm
    R-->>U: evento via WebSocket
    alt partida ativa
      U->>U: para cronômetro e marca derrota
    else coleta
      U->>U: descarta buffer antigo e reinicia coleta
    end
~~~

Um bloco só afeta stream, contador, epoch e rodada da mesma arena; o leaderboard
não é alterado. Notices com epoch anterior são descartados.

## 6. Leaderboard

### Envio

O navegador envia nickname e saldo fictício ao endpoint do realm ativo.
Pydantic normaliza o nome, rejeita
caracteres fora de letras/números/hífen/sublinhado e limita score. Redis ZADD GT
mantém atomicamente apenas o maior valor.

### Consulta

ZRANGE reverso retorna os dez maiores. O frontend cria nós de texto, sem
interpretar nickname como HTML.

Limite: autenticação e cálculo autoritativo ainda não existem. Qualquer cliente
pode enviar um score dentro do intervalo permitido.

## 7. Loja

- Dica: custa 5.000 sats fictícios e destaca a primeira célula de uma palavra.
- Hardware: compra o próximo nível e soma 10 s fora do modo L2.
- Lightning: só pode ser ativado entre rodadas, custa 1.000.000 sats fictícios,
  muda o tema e altera dificuldade/recompensa das próximas rodadas.

Nenhuma dessas ações chama uma carteira, LND ou protocolo Lightning.

## 8. Descoberta, troca e desconexão

O browser consulta o catálogo, habilita apenas `playable=true` e espera um
`game_start` coerente. Toda sessão tem uma geração: ao trocar realm ou perder o
heartbeat, socket, fetches, intervals e timeouts da geração anterior são
invalidados antes de limpar a UI. Um callback antigo não pode encerrar a nova
rodada. Pub/Sub ainda não oferece replay; o usuário escolhe novamente a rede.
