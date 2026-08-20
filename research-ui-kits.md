# Pesquisa de Design Systems, UI Kits e Bibliotecas de Componentes para Interfaces Escuras/CLI

**Projeto:** Mempool Miner  
**Data:** 2026-08-17  
**Escopo:** Design systems, UI kits e bibliotecas de componentes para interfaces escuras, terminais e dashboards de mineração/crypto

---

## 1. Design Systems Analisados

### 1.1 Linear Design System
- **URL:** https://linear.app | https://better-design.com/design-systems/linear
- **GitHub:** https://github.com/voltagent/awesome-design-md (DESIGN.md)
- **Características:**
  - **Dark-first** — o modo escuro é o design primário, não um tema secundário
  - Paleta near-black com acento lavanda/azul (#5e6ad2)
  - Tipografia custom Linear Display/Text/Mono com tracking negativo
  - Cards como painéis de carvão (#0f1011) com bordas hairline
  - Acento lavanda usado de forma escassa: marca, CTAs, foco, links
  - 4 níveis de superfície com ladder de luminosidade
  - Espaçamento: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 96px
  - Bordas arredondadas: 4px (xs) a 24px (xl), pill (9999px)
  - Componentes: botões (primary, secondary, tertiary, inverse, ghost, destructive), inputs, badges, progress bars, tables, kanban boards, date pickers, tooltips, charts
  - **Relevância para Mempool Miner:** Alta — padrão ouro para ferramentas de desenvolvimento com tema escuro

### 1.2 Material Design 3 (Dark Theme)
- **URL:** https://m3.material.io/design/color/dark-theme.html
- **Características:**
  - Superfície base: #121212 (cinza escuro, não preto puro)
  - Princípios: usar cinza escuro (não preto) para expressar elevação; acentos de cor limitados; conservar energia em OLED; acessibilidade WCAG AA
  - Overlay de elevação: 0% (0dp) a 16% (24dp) — superfícies mais elevadas ficam mais claras
  - Cores dessaturadas para acessibilidade (mínimo 4.5:1 de contraste)
  - Paleta tonal: Primary 200 para texto em superfícies escuras
  - Componentes: app bars, cards, FABs, snackbars, dialogs, bottom navigation, backdrop
  - **Relevância:** Média — bom para princípios de elevação e acessibilidade

### 1.3 TUI Design System (Figma)
- **URL:** https://www.figma.com/community/file/1605441651613376418
- **Características:**
  - 40+ componentes para interfaces de terminal
  - Biblioteca de desenho ASCII
  - Inspirado em: lazygit, bottom, yazi, k9s
  - Componentes: painéis, tabelas, menus, barras de progresso, status indicators, forms, logs
  - Padrões modulares para TUIs modernas
  - **Relevância:** Muito Alta — diretamente aplicável ao Mempool Miner

### 1.4 Bubble Tea / Charm Ecosystem
- **URL:** https://github.com/charmbracelet/bubbletea (44.4k stars)
- **Ecossistema:** Bubble Tea (framework TUI), Lipgloss (estilização), Bubbles (componentes), Lipgloss (layout), Bubblewrap (utilitários)
- **Características:**
  - Framework Elm Architecture para Go
  - Componentes: buttons, lists, text inputs, tables, spinners, progress bars, quizes, file filters, viewports, palettes
  - Paleta de cores integrada com suporte a 256 cores e true color
  - Lipgloss: margin, padding, border, border-style, color, align, width, height
  - **Relevância:** Muito Alta — se Mempool Miner usar Go, é a biblioteca padrão da indústria

### 1.5 tview (Terminal UI Library)
- **URL:** https://github.com/rivo/tview (14k stars)
- **Características:**
  - Bibliotecas Go com widgets ricos e interativos
  - Componentes: forms (text input, selections, checkboxes, buttons), text views, text areas, tables, tree views, lists, images, grid/flexbox/page layouts, modals
  - Usado por: k9s (Kubernetes CLI), IRCcloud, DCR DEX
  - Customização completa de cores, bordas, títulos
  - **Relevância:** Alta — alternativa ao Bubble Tea com widgets mais ricos

### 1.6 Monochrome Industrial Design System
- **URL:** https://better-design.com/design-systems/monochrome-industrial
- **Características:**
  - OLED black (#000000), fonte dot-matrix Doto, acento vermelho signal-light, cantos afiados
  - Estilo industrial/utilitário para ferramentas de desenvolvimento
  - Componentes: botões, inputs, badges, progress bars, tables, kanban, charts, tooltips
  - **Relevância:** Alta — estética de terminal autêntica

### 1.7 Crypto Dashboard Design Systems
- **URLs:**
  - https://open-design.ai/plugins/design-system-binance/ (Binance: amarelo bold sobre monocromático)
  - https://open-design.ai/plugins/design-system-coinbase/ (Coinbase: azul clean, institucional)
  - https://open-design.ai/plugins/design-system-trading-terminal/ (Trading Terminal: cyan/coral buy/sell)
  - https://www.figma.com/community/file/1522238618706669989 (Dark Finance & Crypto Dashboard)
- **Características:**
  - Gráficos candlestick, order books, portfolio tracking
  - Cores semânticas: verde (#27a644) para lucro/subida, vermelho para perda/descida
  - Dados em tempo real com alta densidade de informação
  - Tabelas com sorting, filtros, pagination
  - **Relevância:** Muito Alta — diretamente aplicável ao Mempool Miner

### 1.8 bottom (btm) — System Monitor TUI
- **URL:** https://github.com/ClementTsang/bottom (13.9k stars)
- **Características:**
  - Monitor de sistema cross-platform em terminal
  - Temas: gruvbox, tokyonight, nord, monokai, e customizável
  - Gráficos de CPU, memória, disco, rede, processos
  - Layout modular com drag-and-drop de widgets
  - **Relevância:** Alta — referência visual para dashboards de monitoramento

### 1.9 cointop — Crypto Tracker TUI
- **URL:** https://github.com/cointop-sh/cointop (4.4k stars)
- **Características:**
  - Tracker de criptomoedas em terminal
  - Gráficos de preço, rankings, portfolio
  - Temas customizáveis com 24-bit color
  - **Relevância:** Muito Alta — referência direta para dashboard crypto em TUI

### 1.10 Open Design (152 Design Systems)
- **URL:** https://open-design.ai/plugins/systems/
- **Características:**
  - 152+ design systems open-source em formato DESIGN.md
  - Sistemas relevantes: Binance, Coinbase, Trading Terminal, Supabase, Vercel, Linear, Cursor, Discord, Cosmic, Dashboard
  - Cada sistema tem: paleta de cores, tipografia, spacing, componentes, princípios de interação
  - **Relevância:** Alta — fonte centralizada para comparação de múltiplos sistemas

---

## 2. Paletas de Cores Recomendadas

### 2.1 Paleta Principal (Inspirada em Linear + TUI)

| Token | Hex | Uso |
|-------|-----|-----|
| `surface-base` | `#0a0a0b` | Fundo principal (canvas) |
| `surface-raised` | `#141516` | Painéis, cards |
| `surface-overlay` | `#1e1f21` | Modais, dropdowns |
| `surface-highlight` | `#2a2b2d` | Hover, active states |
| `text-primary` | `#e8eaed` | Texto principal (off-white, não #fff) |
| `text-secondary` | `#9aa0a6` | Texto secundário, labels |
| `text-muted` | `#5f6368` | Placeholders, captions |
| `accent-primary` | `#5e6ad2` | Acento principal (lavanda/azul Linear) |
| `accent-secondary` | `#34d399` | Sucesso, positivo, hash rate subindo |
| `accent-danger` | `#f87171` | Erro, desconectado, hash rate caindo |
| `accent-warning` | `#fbbf24` | Alerta, baixa dificuldade |
| `accent-info` | `#60a5fa` | Info, blocos encontrados |
| `border-default` | `#2a2b2d` | Bordas padrão |
| `border-strong` | `#3e3e44` | Bordas de destaque |

### 2.2 Paleta Semântica (Crypto/Mineração)

| Token | Hex | Uso |
|-------|-----|-----|
| `crypto-green` | `#27a644` | Lucro, hash rate positivo, bloco encontrado |
| `crypto-red` | `#dc2626` | Perda, desconexão, erro |
| `crypto-blue` | `#5e6ad2` | Acento primário, links |
| `crypto-yellow` | `#fbbf24` | Alertas, baixa dificuldade |
| `crypto-purple` | `#a78bfa` | Bitcoin, blockchain |
| `crypto-cyan` | `#22d3ee` | Dados técnicos, hashes |
| `crypto-orange` | `#fb923c` | Alertas secundários |

### 2.3 Princípios de Cor para Dark Mode

1. **Nunca usar preto puro (#000000) como fundo** — usar cinza escuro (#0a0a0b ou #121212) para expressar elevação
2. **Textos off-white** — #E0E0E0 a #F0F0F0 (evita fadiga ocular por contraste excessivo)
3. **Cores dessaturadas para legibilidade** — cores saturadas vibram visualmente em fundos escuros
4. **Acentos limitados** — a maioria do espaço é superfície escura, cor usada apenas para ações e status
5. **Contraste mínimo 4.5:1** (WCAG AA) para texto normal
6. **Paleta de elevação** — superfícies mais elevadas são mais claras (luminance hierarchy, não sombras)

---

## 3. Tipografia Recomendada

### 3.1 Fontes

| Uso | Fonte | Tamanho | Peso | Line Height |
|-----|-------|---------|------|-------------|
| Display/Título | Inter / SF Pro Display | 28-40px | 600 | 1.15-1.2 |
| Corpo principal | Inter / SF Pro Text | 14-16px | 400 | 1.5 |
| Mono/Dados | JetBrains Mono / IBM Plex Mono | 13px | 400 | 1.5 |
| Labels/Captions | Inter | 11-12px | 500 | 1.4 |
| Terminal output | JetBrains Mono | 13px | 400 | 1.5 |

### 3.2 Princípios Tipográficos

- **Tracking negativo** em títulos (-0.2px a -3.0px)
- **Line height generoso** em dark mode (1.5 é mínimo)
- **Mono-space para dados** — hashes, endereços, números técnicos
- **Peso 400 para corpo** — não usar bold em texto longo em dark mode
- **Tamanhos mínimos:** 12px para labels, 14px para corpo, 16px para inputs

---

## 4. Espaçamento e Grid

### 4.1 Sistema de Espaçamento (8px base)

| Token | Valor | Uso |
|-------|-------|-----|
| `xxs` | 4px | Ícones pequenos, separadores |
| `xs` | 8px | Padding interno de botões |
| `sm` | 12px | Espaçamento entre elementos relacionados |
| `md` | 16px | Espaçamento padrão entre componentes |
| `lg` | 24px | Espaçamento entre blocos de conteúdo |
| `xl` | 32px | Espaçamento entre seções |
| `xxl` | 48px | Espaçamento entre seções maiores |
| `section` | 96px | Espaçamento entre seções principais |

### 4.2 Bordas e Shapes

| Token | Valor | Uso |
|-------|-------|-----|
| `xs` | 4px | Botões, badges |
| `sm` | 6px | Inputs, selects |
| `md` | 8px | Cards, painéis |
| `lg` | 12px | Modais, containers grandes |
| `xl` | 16px | Containers de seção |
| `pill` | 9999px | Pills, tags, toggles |

---

## 5. Componentes Reutilizáveis

### 5.1 Componentes de Navegação

| Componente | Descrição | Fonte |
|------------|-----------|-------|
| **Sidebar/Nav** | Navegação lateral com ícones + labels | Linear, k9s |
| **Tabs** | Abas horizontais para seções de dados | Linear, Material |
| **Breadcrumbs** | Navegação hierárquica | Linear |
| **Search/Command Palette** | Busca rápida com atalho (Cmd+K) | Linear, Vercel |

### 5.2 Componentes de Dados

| Componente | Descrição | Fonte |
|------------|-----------|-------|
| **Data Table** | Tabelas com sorting, filtering, pagination | Linear, tview, k9s |
| **Status Badge** | Indicadores de status (online/offline/mining) | Linear, cointop |
| **Progress Bar** | Barra de progresso para hash rate, sync | Linear, bottom |
| **Gauge/Meter** | Medidor circular/linear para métricas | bottom, cointop |
| **Sparkline** | Mini-gráfico de tendência | cointop, crypto dashboards |
| **Candlestick Chart** | Gráfico de velas para preços | Binance, crypto dashboards |
| **Live Data Feed** | Atualização em tempo real com animação | cointop, bottom |
| **Log Viewer** | Visualizador de logs com syntax highlighting | tview, lazygit |

### 5.3 Componentes de Interação

| Componente | Descrição | Fonte |
|------------|-----------|-------|
| **Button** | Primary, secondary, ghost, destructive | Linear |
| **Input/Field** | Text input com validação inline | Linear |
| **Toggle/Switch** | Toggle para configurações | Linear, Material |
| **Modal/Dialog** | Diálogo para confirmações | Linear, tview |
| **Tooltip** | Dica contextual | Linear |
| **Dropdown** | Menu suspenso | Linear, tview |
| **Accordion** | Seções expansíveis | Linear |
| **Form** | Formulários com validação | tview, Linear |
| **List** | Lista navegável com keyboard | tview, Bubble Tea |
| **Tree View** | Hierarquia expansível | tview, lazygit |

### 5.4 Componentes Específicos para Mempool Miner

| Componente | Descrição | Fonte |
|------------|-----------|-------|
| **Hash Rate Monitor** | Display de hash rate com gráfico de tendência | bottom, cointop |
| **Block Found Alert** | Notificação visual quando bloco é encontrado | cointop |
| **Pool Connection Status** | Indicador de conexão com pool | k9s, cointop |
| **Difficulty Gauge** | Medidor de dificuldade da rede | cointop |
| **Mempool Visualization** | Visualização do mempool (txs pendentes) | custom |
| **Worker Status** | Status de workers/miners | k9s, bottom |
| **Earnings Tracker** | Tracker de earnings com histórico | cointop |
| **Network Stats** | Stats da rede Bitcoin (height, difficulty, etc.) | cointop |

---

## 6. Padrões de Interação

### 6.1 Navegação por Teclado (TUI)

- **Tab/Shift+Tab** — navegar entre campos
- **Arrow keys** — navegar em listas e tabelas
- **Enter/Space** — selecionar/confirmar
- **Esc** — voltar/cancelar/fechar modal
- **Ctrl+C** — sair da aplicação
- **Cmd+K / Ctrl+K** — command palette
- **F1-F12** — atalhos de função específica
- **Vi-style** — h/j/k/l para navegação (lazygit, k9s)

### 6.2 Feedback Visual

- **Hover states** — highlight de superfície (#2a2b2d)
- **Focus rings** — borda de 2px com cor de acento (#5e6ad2)
- **Loading states** — spinners, skeleton screens, shimmer
- **Success/Error** — verde/vermelho com ícones
- **Toast notifications** — feedback não-intrusivo no canto
- **Animations** — transições suaves (150-300ms), nunca mais que 500ms

### 6.3 Layout Patterns

- **Dashboard grid** — layout modular com widgets arrastáveis (bottom)
- **Split pane** — duas colunas com resize (lazygit, k9s)
- **Full-screen TUI** — ocupa toda a terminal (padrão TUI)
- **Modal overlay** — sobreposição sem sair do contexto (tview)
- **Status bar** — barra inferior com informações globais (htop, bottom)

---

## 7. Como Adaptar ao Mempool Miner

### 7.1 Arquitetura de Interface Sugerida

```
┌─────────────────────────────────────────────────────┐
│  Mempool Miner                    [●] [─] [✕]       │  ← Title Bar
├─────────────────────────────────────────────────────┤
│  ┌──────────┬──────────────────────────────────────┐│
│  │  NAV     │  HASH RATE                           ││
│  │          │  █████████████████  145.2 TH/s       ││
│  │  📊 Dash │  ────────────────────                ││
│  │  ⛏️  Workers│  [████████░░] 85%                  ││
│  │  📦 Blocks │                                      ││
│  │  💰 Earnings│  ────────────────────                ││
│  │  ⚙️  Settings│  Último bloco: há 12 min           ││
│  │          │                                      ││
│  │          │  ────────────────────                ││
│  │          │  MEMPOOL                             ││
│  │          │  Pending: 245,832 txs                ││
│  │          │  Fee rate: 12 sat/vB                 ││
│  │          │  ────────────────────                ││
│  │          │  NETWORK STATS                       ││
│  │          │  Height: 856,432                     ││
│  │          │  Difficulty: 83.93T                  ││
│  │          │  ────────────────────                ││
│  │          │  RECENT BLOCKS                       ││
│  │          │  ┌────┬──────┬──────┬──────┐         ││
│  │          │  │ #  │ Time │ Size │ Reward│        ││
│  │          │  │8564│14:32 │ 1.4MB │ 6.25BTC│       ││
│  │          │  │31   │      │      │        │       ││
│  │          │  └────┴──────┴──────┴──────┘         ││
│  └──────────┴──────────────────────────────────────┘│
├─────────────────────────────────────────────────────┤
│  Pool: stratum+tcp://btc.pool:3333  │  Uptime: 4d  │  ← Status Bar
└─────────────────────────────────────────────────────┘
```

### 7.2 Tecnologias Recomendadas

| Camada | Recomendação | Justificativa |
|--------|-------------|---------------|
| **Framework TUI** | Bubble Tea + Lipgloss (Go) | 44.4k stars, ecossistema maduro, componentes prontos |
| **Alternativa TUI** | tview (Go) | Widgets mais ricos, usado por k9s |
| **Alternativa Python** | Textual (Python) | Se o projeto for em Python |
| **Gráficos** | Bubble Tea Charts / custom ASCII | Para hash rate, mempool, earnings |
| **Ícones** | Bubble Tea Bubbles (emoji) ou Lucide | Lucide tem versão terminal |
| **Cores** | Lipgloss Palette | Suporte a 256 cores + true color |

### 7.3 Adaptação de Design Systems

1. **Linear** → Adotar a filosofia dark-first, ladder de superfícies, tipografia com tracking negativo, acento escasso
2. **TUI Design System (Figma)** → Usar os 40+ componentes como referência para layout de terminal
3. **cointop** → Adaptar padrões de dados crypto (gráficos de preço, rankings, status de conexão)
4. **bottom** → Adaptar dashboard de monitoramento (gráficos de CPU/memória → hash rate/uptime)
5. **Material Design 3** → Usar princípios de elevação (overlay de luminosidade) e acessibilidade (contraste WCAG)
6. **Monochrome Industrial** → Inspirar estética de terminal autêntica (fonte mono, cantos afiados, cores de sinal)

### 7.4 Checklist de Implementação

- [ ] Definir paleta de cores com tokens semânticos
- [ ] Escolher fonte mono para dados e sans-serif para UI
- [ ] Implementar sistema de espaçamento 8px base
- [ ] Criar componentes base: button, badge, progress bar, table
- [ ] Implementar layout com sidebar + content area
- [ ] Adicionar status bar inferior
- [ ] Implementar navegação por teclado
- [ ] Adicionar feedback visual (hover, focus, loading)
- [ ] Testar em terminais com diferentes profundidades de cor
- [ ] Validar contraste WCAG AA

---

## 8. Referências

### Design Systems
- **Linear:** https://linear.app | https://better-design.com/design-systems/linear
- **Material Design 3 Dark:** https://m3.material.io/design/color/dark-theme.html
- **TUI Design System (Figma):** https://www.figma.com/community/file/1605441651613376418
- **Open Design (152 systems):** https://open-design.ai/plugins/systems/
- **Better Design (31 themes):** https://better-design.com/design-systems/
- **Design Systems Repo:** https://designsystemsrepo.com/design-systems/

### TUI Frameworks
- **Bubble Tea:** https://github.com/charmbracelet/bubbletea (44.4k ⭐)
- **tview:** https://github.com/rivo/tview (14k ⭐)
- **Textual (Python):** https://github.com/Textualize/textual
- **Awesome TUIs:** https://github.com/rothgar/awesome-tuis (20.2k ⭐)

### Referências Visuais
- **bottom (btm):** https://github.com/ClementTsang/bottom (13.9k ⭐)
- **cointop:** https://github.com/cointop-sh/cointop (4.4k ⭐)
- **lazygit:** https://github.com/jesseduffield/lazygit
- **k9s:** https://github.com/derailed/k9s
- **yazi:** https://github.com/sxyazi/yazi

### Artigos e Guias
- **Dark Mode Design Systems (Muzli):** https://muz.li/blog/dark-mode-design-systems-a-complete-guide-to-patterns-tokens-and-hierarchy/
- **UI Libraries com Dark Mode (LogRocket):** https://blog.logrocket.com/which-ui-libraries-support-dark-mode/
- **Princípios de Dark UI Design:** https://www.toptal.com/designers/ui/dark-ui-design
- **DESIGN.md (awesome-design-md):** https://github.com/voltagent/awesome-design-md

### Crypto/UI Dashboards
- **Binance Design:** https://open-design.ai/plugins/design-system-binance/
- **Coinbase Design:** https://open-design.ai/plugins/design-system-coinbase/
- **Trading Terminal Design:** https://open-design.ai/plugins/design-system-trading-terminal/
- **Dark Finance Dashboard (Figma):** https://www.figma.com/community/file/1522238618706669989

---

## 9. Resumo Executivo

### O que foi encontrado:
- **10 design systems/UI kits** analisados em detalhe
- **Paleta de cores** recomendada com tokens semânticos para dark mode
- **Sistema tipográfico** com fontes sans-serif + mono
- **15+ componentes** identificáveis para reutilização
- **Padrões de interação** específicos para TUIs (navegação por teclado, feedback visual)

### Recomendações principais:
1. **Adotar Bubble Tea + Lipgloss** como framework TUI principal (Go)
2. **Seguir a filosofia dark-first do Linear** como referência de qualidade visual
3. **Usar o TUI Design System do Figma** como catálogo de componentes para terminal
4. **Inspirar-se no cointop e bottom** para dashboards de dados em tempo real
5. **Implementar paleta semântica crypto** (verde/vermelho para lucro/perda)
6. **Priorizar navegação por teclado** como padrão de interação principal

### Próximos passos sugeridos:
1. Criar um arquivo de tokens de design (cores, tipografia, spacing)
2. Implementar componentes base com Bubble Tea/Lipgloss
3. Prototipar o layout principal do Mempool Miner
4. Validar com usuários em diferentes terminais e configurações de cor
