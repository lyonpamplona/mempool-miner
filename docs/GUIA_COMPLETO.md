# Guia Completo do Mempool Miner

> **Jogo educacional em tempo real que transforma transações reais do Bitcoin em palavras dentro de uma grade de caça-palavras.**

---

## Índice

1. [O que é o Mempool Miner?](#1-o-que-e-o-mempool-miner)
2. [Como funciona o sistema](#2-como-funciona-o-sistema)
3. [Arquitetura técnica](#3-arquitetura-tecnica)
4. [Instalação e execução](#4-instalacao-e-execucao)
5. [Mecânicas do jogo](#5-mecanicas-do-jogo)
6. [Mecânicas in-game](#6-mecanicas-in-game)
7. [API e WebSocket](#7-api-e-websocket)
8. [Configuração avançada](#8-configuracao-avancada)
9. [Comandos operacionais](#9-comandos-operacionais)
10. [Perguntas frequentes](#10-perguntas-frequentes)

---

## 1. O que é o Mempool Miner?

O **Mempool Miner** é um jogo educacional que conecta o mundo real do Bitcoin à experiência interativa de um caça-palavras. Ele monitora transações reais da rede Bitcoin (Regtest, Signet ou Mainnet) e transforma cada transação em uma palavra derivada do padrão BIP39, criando uma grade dinâmica onde o jogador precisa encontrar as palavras antes que um novo bloco seja minerado.

### Conceito central

```
Transação Bitcoin → TXID → Hash SHA-256 → 128 bits → Palavra BIP39 → Grade
```

Cada transação que entra no mempool do Bitcoin Core é convertida em uma palavra única. Quando 6 palavras diferentes são coletadas, uma nova rodada de caça-palavras é iniciada. O jogador tem até o próximo bloco para encontrar todas as palavras.

### O que o jogo NÃO faz

- ❌ Não minera Bitcoin real
- ❌ Não abre canais Lightning
- ❌ Não movimenta fundos reais
- ❌ Não conecta carteiras
- ❌ Não calcula hashrate real

Sats, hashrate, carteira, recompensas e modo L2 são **mecânicas simuladas** para fins educacionais e de entretenimento.

---

## 2. Como funciona o sistema

### Fluxo completo de uma transação ao jogo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DO MEMPOOL MINER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Bitcoin Core publica transação via ZMQ                      │
│     ↓                                                           │
│  2. Ingestor recebe e coloca na fila                           │
│     ↓                                                           │
│  3. GameEngine calcula TXID e converte para palavra BIP39       │
│     ↓                                                           │
│  4. RPC consulta vsize e taxa da transação                      │
│     ↓                                                           │
│  5. Evento publicado no Redis Pub/Sub                           │
│     ↓                                                           │
│  6. FastAPI entrega via WebSocket ao navegador                  │
│     ↓                                                           │
│  7. Frontend adiciona palavra à grade                           │
│     ↓                                                           │
│  8. Jogador encontra palavras e ganha pontos                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes do sistema

| Componente | Responsabilidade |
|---|---|
| **Bitcoin Core** | Nó Bitcoin que publica transações e blocos via ZMQ; fornece metadados via RPC |
| **Ingestor** | Processo singleton por rede que consome ZMQ, calcula palavras e publica eventos |
| **Redis** | Pub/Sub para eventos, estado dos nós, leaderboard e deduplicação |
| **FastAPI** | API REST e WebSocket que entrega dados ao frontend |
| **Nginx** | Proxy same-origin que serve o frontend e redireciona para a API |
| **Frontend** | Interface PWA com grade, cronômetro, loja simulada e controles |

---

## 3. Arquitetura técnica

### Diagrama de componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMPOOL MINER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                      │
│  │ Regtest  │    │  Signet   │    │ Mainnet  │ (opcional)           │
│  │ Bitcoin  │    │  Bitcoin  │    │ Bitcoin  │                      │
│  │  Core    │    │  Core     │    │  Core    │                      │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                      │
│       │ ZMQ           │ ZMQ           │ ZMQ                         │
│       ▼               ▼               ▼                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                      │
│  │Ingestor  │    │Ingestor  │    │Ingestor  │                      │
│  │Regtest   │    │ Signet   │    │Mainnet   │                      │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                      │
│       │               │               │                             │
│       └───────────────┼───────────────┘                             │
│                       ▼                                             │
│              ┌────────────────┐                                     │
│              │   Redis        │                                     │
│              │ (Pub/Sub +     │                                     │
│              │  Sorted Sets)  │                                     │
│              └───────┬────────┘                                     │
│                      │                                              │
│              ┌───────▼────────┐                                     │
│              │   FastAPI      │                                     │
│              │ (REST + WS)    │                                     │
│              └───────┬────────┘                                     │
│                      │                                              │
│              ┌───────▼────────┐                                     │
│              │    Nginx       │                                     │
│              │  (Proxy + PWA) │                                     │
│              └───────┬────────┘                                     │
│                      │                                              │
│              ┌───────▼────────┐                                     │
│              │   Navegador    │                                     │
│              │  (Jogo PWA)    │                                     │
│              └────────────────┘                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Redes suportadas

| Rede | Descrição | Uso |
|---|---|---|
| **Regtest** | Rede local de teste | Desenvolvimento e demonstração |
| **Signet** | Rede pública de teste | Transações reais sem valor |
| **Mainnet** | Rede principal (opcional) | Transações reais da mainnet |

---

## 4. Instalação e execução

### Pré-requisitos

- **Docker Engine** ou **Docker Desktop** com Compose 2.33.1+
- **4 GB de RAM** livres (Regtest + Signet)
- **Porta 8010** disponível (jogo)
- **Porta 8020** disponível (documentação, opcional)

### Instalação rápida

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/mempool.miner.git
cd mempool.miner

# 2. Copie o arquivo de configuração
cp .env.example .env

# 3. Edite .env e substitua as senhas RPC de exemplo
#    (IMPORTANTE: use senhas fortes e aleatórias)

# 4. Valide a configuração
docker compose config --quiet

# 5. Inicie o sistema
docker compose up -d --build

# 6. Verifique os serviços
docker compose ps
```

### Acessando o jogo

- **Jogo:** http://localhost:8010
- **Documentação:** http://localhost:8020/ (opcional)
- **API pública:** http://localhost:8020/api/ (opcional)

### Instalando como PWA

No navegador, clique no botão **"Instalar app"** para instalar o jogo como Progressive Web App. O service worker mantém apenas o shell estático em cache; API, WebSocket, health e leaderboard nunca são armazenados offline.

---

## 5. Mecânicas do jogo

### Objetivo

Encontrar **6 palavras** escondidas em uma grade de caça-palavras antes que:
- O **tempo acabe** (20, 60 ou 75 segundos, dependendo da grade)
- Um **novo bloco** seja minerado na rede Bitcoin

### Fluxo de jogo

```
┌─────────────────────────────────────────────────────────────────┐
│                    CICLO DE JOGO                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Coleta de palavras                                          │
│     → Transações chegam via WebSocket                           │
│     → Cada transação vira uma palavra BIP39                     │
│     → 6 palavras únicas = nova rodada                           │
│     ↓                                                           │
│  2. Construção da grade                                         │
│     → Grade 8×8 (modo L2), 12×12 (padrão) ou 15×15 (vsize alto)│
│     → Palavras posicionadas sem sobreposição                    │
│     → Espaços preenchidos com letras aleatórias                 │
│     ↓                                                           │
│  3. Rodada ativa                                                │
│     → Cronômetro inicia                                         │
│     → Jogador seleciona palavras na grade                       │
│     → Pontos calculados por palavra encontrada                  │
│     ↓                                                           │
│  4. Fim da rodada                                               │
│     → Vitória: todas as palavras encontradas                    │
│     → Derrota: tempo esgotado ou novo bloco minerado            │
│     ↓                                                           │
│  5. Nova coleta                                                 │
│     → Buffer limpo, espera próximas transações                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Seleção de palavras

- **Mouse/Toque:** Clique na primeira letra, arraste até a última
- **Teclado:** Use as setas para navegar, Enter para confirmar
- **Direções:** Horizontal, vertical e diagonal (ambos os sentidos)

### Pontuação

```
pontos = (500 + comprimento × 50) × combo
```

| Fator | Valor |
|---|---|
| Base por palavra | 500 pontos |
| Bônus por letra | 50 pontos × comprimento |
| Combo | Cresce 0.5x por acerto em menos de 8s (máx 4x) |

### Multiplicadores especiais

| Multiplicador | Valor | Condição |
|---|---|---|
| **Taxa alta** | ×3 | Transação com taxa acima de 20 sats/vB |
| **Hash dourado** | ×5 | TXID começa com "00" |
| **Modo Lightning** | ×10 | Modo L2 ativado na loja |

---

## 6. Mecânicas in-game

> **Referência completa:** todas as mecânicas, valores e abas estão em
> [MECANICAS.md](MECANICAS.md). Esta seção é um resumo.

### Loja de upgrades

A loja oferece 3 tipos de upgrades simulados:

#### 1. Dica (Hint)
- **Custo:** 5.000 sats fictícios
- **Efeito:** Destaca a primeira célula de uma palavra não encontrada
- **Uso:** Apenas durante a rodada ativa

#### 2. Hardware (Minerador)
- **Custo:** Progressivo (100k, 500k, 2M sats)
- **Efeito:** Adiciona +10 sats ao saldo por transação processada
- **Níveis:** 3 níveis disponíveis (CPU Miner → GPU Rig → ASIC Antminer)

#### 3. Modo Lightning (L2)
- **Custo:** 1.000.000 sats fictícios
- **Efeito:** 
  - Muda o tema visual para azul Lightning
  - Grade reduzida para 8×8 (mais fácil)
  - Multiplicador ×10 em todas as palavras
  - Dificuldade reduzida
- **Restrição:** Só pode ser ativado entre rodadas

### Estados da rede

| Estado | Significado | Ação do jogo |
|---|---|---|
| `starting` | Serviço iniciando | Aguarda |
| `syncing` | Nó sincronizando (IBD) | Não inicia partidas |
| `ready` | Realm disponível | Jogo ativo |
| `disabled` | Profile não iniciado | Não aparece no seletor |
| `unavailable` | Heartbeat indisponível | Retorna ao seletor |
| `stopped` | Ingestor encerrado | Retorna ao seletor |

### Troca de rede

Ao trocar de rede (Regtest → Signet → Mainnet):
1. A sessão atual é invalidada
2. WebSocket é fechado
3. Todos os timeouts e intervals são cancelados
4. Saldo e upgrades **não** atravessam realms
5. Nova conexão é estabelecida com o realm selecionado

### RBF / bloco órfão

Quando um bloco real encerra a rodada com palavras não encontradas, o jogador
pode ativar **RBF** para resgatar o bloco: custa 100.000 sats, dá +15 s e tem
janela de decisão de 3 s.

### Boss block

A cada 50 blocos, uma rodada de boss: grade 15×15, 10 palavras, 45 s,
multiplicador ×5 e loot de 50.000 sats. O HUD mostra a barra de HP; cada
palavra encontrada reduz o HP.

### Eventos globais

O `GlobalEventScheduler` dispara eventos aleatórios com aviso de 120 s:

| Evento | Duração | Efeito |
|---|---|---|
| `fee_spike` | 10 min | todas High Fee (3×) |
| `golden_rush` | 5 min | golden 3× mais frequente (5×) |
| `mempool_flood` | 10 min | 2×; grade 15×15; +15 s |
| `lightning_storm` | 3 min | 10×; grade 8×8; tempo 20 s |

### Conquistas, missões e progressão

- **28 conquistas** em 5 categorias (volume, raridade, velocidade, exploração,
  social) com bônus permanentes.
- **Missões:** 3 diárias rotativas + 1 semanal, com recompensa em sats.
- **Nível/XP/rank:** XP por palavra (`comprimento×10 + combo×5`), curva
  `nível×100`, 10 ranks temáticos e bônus passivos (tempo e desconto de dica).
- **Season pass:** 28 dias, 20 níveis free + 20 premium, 100 XP/nível.
- **Staking:** trava sats por 1/6/24 h (+5%/+15%/+30%), penalidade 10%.
- **Energia:** máx 10, recarga a cada 30 min, compra de 3 por 2.000 sats.
- **Crates:** 5.000 sats (ou 1 grátis a cada 10 blocos); drops de power-ups,
  skins e block cards.
- **Sprint:** 4 palavras em 30 s, recompensa 0,5×, leaderboard próprio.
- **Decoder:** mini-game de 30 s (txid → palavra BIP39).
- **Skill tree:** ramos mining/search/lightning.
- **Social:** chat por realm, amigos (bônus de cooperação) e mercado P2P de
  power-ups.

---

## 7. API e WebSocket

### Endpoints REST

#### GET `/api/v1/health/live`
Verifica se a API está respondendo.
```json
{"status": "ok"}
```

#### GET `/api/v1/networks`
Lista todas as redes disponíveis com seu status.
```json
{
  "schema_version": 2,
  "default_realm_id": "regtest",
  "networks": [
    {
      "realm_id": "regtest",
      "network": "regtest",
      "display_name": "Regtest local",
      "status": "ready",
      "playable": true,
      "initial_block_download": false,
      "verification_progress": 1.0,
      "pruned": false
    }
  ]
}
```

#### GET `/api/v1/networks/{realm_id}/health`
Retorna o heartbeat sanitizado de uma rede específica.

#### GET `/api/v1/networks/{realm_id}/leaderboard`
Lista os 10 maiores recordes de uma rede.
```json
{
  "realm_id": "regtest",
  "leaderboard": [
    {"username": "Miner_42", "score": 12500}
  ]
}
```

#### POST `/api/v1/networks/{realm_id}/leaderboard`
Envia uma pontuação para o leaderboard.
```json
{"username": "Miner_42", "score": 12500}
```

**Regras:**
- Nickname: 1-12 caracteres (letras, números, hífen, sublinhado)
- Score: inteiro entre 0 e 2.147.483.647
- Apenas o maior valor é mantido

### WebSocket

#### Conexão
```
ws://localhost:8010/ws/v1/game/{realm_id}
```

#### Eventos recebidos

**`game_start`** — Início da conexão
```json
{
  "schema_version": 2,
  "action": "game_start",
  "realm_id": "regtest",
  "network": "regtest",
  "status": "ready",
  "playable": true,
  "initial_block_download": false,
  "verification_progress": 1.0,
  "pruned": false
}
```

**`transaction_received`** — Nova transação
```json
{
  "schema_version": 2,
  "action": "transaction_received",
  "realm_id": "regtest",
  "epoch": "opaque-stream-id",
  "word": "ABANDON",
  "tx_stub": "4a5e1e4b",
  "is_golden": false,
  "is_high_fee": true,
  "vsize": 250,
  "fee_rate_sat_vb": 24.5
}
```

**`block_mined`** — Novo bloco minerado
```json
{
  "schema_version": 2,
  "action": "block_mined",
  "realm_id": "regtest",
  "epoch": "new-opaque-stream-id"
}
```

**`network_status`** — Mudança de status da rede
```json
{
  "schema_version": 2,
  "action": "network_status",
  "realm_id": "signet",
  "status": "syncing",
  "playable": false,
  "initial_block_download": true,
  "verification_progress": 0.82
}
```

---

## 8. Configuração avançada

### Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `DEFAULT_REALM_ID` | Realm padrão para aliases legados | `regtest` |
| `REDIS_PASSWORD` | Senha do Redis (obrigatório) | — |
| `RPC_USER` | Usuário RPC do Bitcoin Core | — |
| `RPC_PASSWORD` | Senha RPC do Bitcoin Core | — |
| `RPC_HOST` | Host RPC do Bitcoin Core | `bitcoin-{realm}` |
| `RPC_PORT` | Porta RPC do Bitcoin Core | `18443` (regtest) |
| `ZMQ_HOST` | Host ZMQ do Bitcoin Core | `bitcoin-{realm}` |
| `ZMQ_PORT` | Porta ZMQ do Bitcoin Core | `28332` |
| `HIGH_FEE_RATE_SAT_VB` | Limite para taxa alta | `20` |
| `TX_QUEUE_MAX_SIZE` | Tamanho máximo da fila | `5000` |
| `TX_PROCESS_INTERVAL_SECONDS` | Intervalo entre processamentos | `1.0` |

### Perfis Docker

```bash
# Regtest + Signet (padrão)
docker compose up -d --build

# Com Mainnet (opcional)
docker compose --profile mainnet up -d --build

# Com documentação (opcional)
docker compose --profile docs up -d --build docs
```

### Pruning Mainnet

Para reduzir o espaço em disco do nó Mainnet:
```bash
MAINNET_PRUNE_MIB=10240  # 10 GiB de blocos
```

---

## 9. Comandos operacionais

### Verificar status
```bash
docker compose ps
```

### Ver logs
```bash
# Logs do ingestor Regtest
docker compose logs -f ingestor-regtest

# Logs da API
docker compose logs -f api

# Logs do Redis
docker compose logs -f redis
```

### Reiniciar serviços
```bash
# Reiniciar tudo
docker compose restart

# Reiniciar apenas a API
docker compose restart api

# Reiniciar apenas o ingestor Regtest
docker compose restart ingestor-regtest
```

### Parar e remover
```bash
# Parar todos os containers
docker compose down

# Parar e remover volumes (cuidado: perde dados)
docker compose down -v
```

### Healthcheck do ingestor
```bash
# Executar healthcheck manualmente
docker compose exec ingestor-regtest python -m app.ingestor_healthcheck
```

---

## 10. Perguntas frequentes

### O jogo minera Bitcoin real?
Não. O Mempool Miner é um jogo educacional que simula mecânicas de mineração. Nenhuma transação real é enviada, nenhum hashrate é calculado e nenhum Bitcoin é minerado.

### Por que não há transações aparecendo?
Verifique se:
1. O Bitcoin Core está sincronizado (`playable: true`)
2. Transações estão sendo enviadas ao mempool (em Regtest, use `generatetoaddress` ou envie transações)
3. O ingestor está rodando (`docker compose ps`)
4. O WebSocket está conectado (console do navegador)

### Como gerar transações em Regtest?
```bash
# Obter endereço
docker compose exec bitcoin-regtest bitcoin-cli getnewaddress

# Enviar transação
docker compose exec bitcoin-regtest bitcoin-cli sendtoaddress <endereco> 0.01

# Gerar bloco (para minerar transações pendentes)
docker compose exec bitcoin-regtest bitcoin-cli generatetoaddress 1 <endereco>
```

### O leaderboard é persistente?
Sim, os recordes são armazenados no Redis. Para resetar:
```bash
docker compose exec redis redis-cli FLUSHALL
```

### Como instalar como PWA?
No navegador (Chrome, Edge, Firefox), clique no ícone de instalação na barra de endereço ou no botão **"Instalar app"** dentro do jogo.

### O jogo funciona offline?
O shell do jogo (HTML, CSS, JS) é cacheado pelo service worker, mas as transações e eventos requerem conexão com a API. Offline, o jogo mostra uma mensagem indicando que a conexão é necessária.

### Posso usar minha própria carteira?
Não. O jogo não se conecta a carteiras externas. Sats, hashrate e recompensas são simulados internamente.

### Como contribuir?
Leia [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes de contribuição. O histórico de mudanças está em [CHANGELOG.md](CHANGELOG.md).

---

## Referências

- [Documentação técnica](docs/README.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [API](docs/API.md)
- [Configuração](docs/CONFIGURACAO.md)
- [Tutorial](docs/TUTORIAL.md)
- [Comandos](docs/COMANDOS.md)
- [Segurança](docs/SEGURANCA.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
