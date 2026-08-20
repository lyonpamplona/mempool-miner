# Pesquisa: Menus e Navegação para Mempool Miner

> Data: 17 de Agosto de 2026
> Objetivo: Identificar padrões de menu e navegação aplicáveis ao projeto Mempool Miner

---

## 1. Padrões de Menu Encontrados

### 1.1 Sidebar Navigation (Menu Lateral)
- **O que é:** Barra vertical fixa no lado esquerdo (ou direito) da tela com acesso persistente às seções principais
- **Melhor para:** Dashboards, painéis administrativos, SaaS, aplicações complexas com hierarquia profunda
- **Vantagens:** Suporta listas longas, categorias aninhadas, sempre visível, fácil de escanear
- **Referência:** [Eleken - UX Navigation Design](https://www.eleken.co/blog-posts/ux-navigation-design)

### 1.2 Bottom Navigation Bar (Barra Inferior)
- **O que é:** Linha de 3-5 ícones com labels na parte inferior da tela
- **Melhor para:** Mobile, apps com conjunto pequeno de tarefas principais
- **Vantagens:** Ergonômico (zona do polegar), sempre visível, alta descobribilidade
- **Regra de ouro:** Máximo 5 itens; nunca esconder ações críticas em "Mais"
- **Referência:** [Material Design - Bottom Navigation](https://m2.material.io/components/bottom-navigation)

### 1.3 Top Navigation Bar (Barra Superior)
- **O que é:** Menu horizontal no topo da tela com seções principais
- **Melhor para:** Websites, blogs, landing pages, apps com poucas seções
- **Vantagens:** Posição esperada pelo usuário, fácil de escanear, alto contraste
- **Referência:** [NN/g - Menu Design Checklist](https://www.nngroup.com/articles/menu-design/)

### 1.4 Hamburger Menu / Drawer Menu
- **O que é:** Ícone de 3 linhas que revela painel lateral com opções de navegação
- **Melhor para:** Mobile com espaço limitado, itens secundários
- **Desvantagens:** "Fora de vista, fora da mente" — baixa descobribilidade, extra tap, sem hierarquia visual
- **Regra:** NÃO usar em desktop (espaço suficiente para mostrar menus). Use apenas para itens secundários
- **Referência:** [UXPin - Mobile Navigation Patterns](https://www.uxpin.com/studio/blog/mobile-navigation-patterns-pros-and-cons/)

### 1.5 Mega Menu
- **O que é:** Menu expandido que mostra múltiplas categorias e subcategorias de uma vez
- **Melhor para:** Sites com muitas categorias, e-commerce
- **Vantagens:** Visibilidade total, agrupamento contextual, sem necessidade de scroll
- **Referência:** [Justinmind - Navigation Design](https://www.justinmind.com/blog/navigation-design-almost-everything-you-need-to-know/)

### 1.6 Breadcrumbs (Pão Quebrado)
- **O que é:** Indicador de caminho hierárquico (ex: Home > Dashboard > Miners > Active)
- **Melhor para:** Hierarquias profundas, orientação do usuário
- **Vantagens:** Mostra localização atual, permite voltar níveis, contexto visual
- **Referência:** [NN/g - Breadcrumb Navigation](https://www.nngroup.com/articles/breadcrumb-navigation-useful/)

### 1.7 Tabs (Aba)
- **O que é:** Linha de abas horizontais para alternar entre views relacionadas
- **Melhor para:** Conteúdo relacionado na mesma página, filtros, modos de visualização
- **Vantagens:** Alternância rápida, estado visível, sem reload
- **Referência:** [IxDF - Navigation in UX](https://ixdf.org/literature/topics/navigation)

### 1.8 Accordion Menu (Acordeão)
- **O que é:** Lista colapsável onde cada item expande para revelar sub-opções
- **Melhor para:** Mobile, configurações, menus com seções que abrem/fecham
- **Vantagens:** Economiza espaço, organiza conteúdo em seções
- **Referência:** [Justinmind - Navigation Design](https://www.justinmind.com/blog/navigation-design-almost-everything-you-need-to-know/)

### 1.9 Off-Canvas Navigation
- **O que é:** Menu escondido que desliza da lateral ao clicar/tocar
- **Melhor para:** Mobile, menus secundários, configurações
- **Vantagens:** Não ocupa espaço, animação suave
- **Referência:** [Design Studio UI/UX - Mobile Navigation](https://www.designstudiouiux.com/blog/mobile-navigation-ux/)

### 1.10 Gesture-Based Navigation (Navegação por Gestos)
- **O que é:** Swipe, pull-to-refresh, edge-swipe para voltar
- **Melhor para:** Complemento a navegação visível, power users
- **Regra:** NUNCA depender apenas de gestos — sempre ter alternativa visível
- **Referência:** [Design Studio UI/UX - Mobile Navigation](https://www.designstudiouiux.com/blog/mobile-navigation-ux/)

### 1.11 Command Palette (Paleta de Comandos)
- **O que é:** Busca rápida ativada por atalho (Ctrl+K / Cmd+K) com ações e navegação
- **Melhor para:** Dashboards complexos, power users, acesso rápido
- **Vantagens:** Navegação ultra-rápida, descoberta de features, sem mouse
- **Referência:** [OneThing Design - Top 12 Patterns](https://www.onething.design/post/top-website-navigation-design-patterns)

### 1.12 Mixed Pattern (Padrão Misto)
- **O que é:** Combinação de Bottom Nav + FAB (Floating Action Button) ou Bottom Nav + Hamburger
- **Melhor para:** Apps com ação principal frequente + navegação secundária
- **Exemplo:** Instagram (bottom tabs + FAB central para criar)
- **Referência:** [UX StackExchange - Bottom Nav vs Hamburger](https://ux.stackexchange.com/questions/105661/when-bottom-navigation-isnt-best)

---

## 2. Como Organizar Menus e Submenus

### Princípios Fundamentais (NN/g - 17 Guidelines)

1. **Mostre a navegação em telas grandes** — Hamburger não é adequado para desktop
2. **Coloque menus onde o usuário espera** — Header para web, esquerda para apps
3. **Use cores com contraste** — Links devem ser imediatamente distinguíveis do fundo
4. **Não cubra a tela inteira com menus** — Megamenus não devem obscurecer o conteúdo
5. **Indique a localização atual** — Destaque o item ativo no menu
6. **Forneça navegação local** — Para conteúdo relacionado, use submenus laterais
7. **Use labels fáceis de escanear** — Alinhe à esquerda, use termos-chave primeiro
8. **Mostre múltiplos níveis em submenus** — Para sites grandes, use menus sequenciais

### Hierarquia de Navegação

| Nível | Tipo | Localização | Exemplo |
|-------|------|-------------|---------|
| Global | Sidebar / Top Bar | Esquerda ou topo | Dashboard, Miners, Wallet, Settings |
| Local | Submenu / Tabs | Dentro da seção | Active, Inactive, Archived |
| Contextual | Breadcrumbs / Action Bar | Topo do conteúdo | Home > Miners > Active |
| Utilitário | Topo direito | Header | Search, Notifications, Profile |

### Regras de Organização

- **Máximo 7±2 itens** no menu principal (lei da psicologia cognitiva)
- **Ações frequentes primeiro** — ordene por frequência de uso, não alfabeticamente
- **Agrupamento lógico** — itens relacionados juntos (ex: todos os settings em uma seção)
- **Labels claros e consistentes** — use o mesmo termo em todo o app
- **Ícones + texto** — ícones sozinhos são ambíguos; combine com labels
- **Estado ativo visível** — destaque a seção atual com cor, fundo, ou ícone
- **Submenus com no máximo 2 níveis** — mais que isso confunde o usuário

---

## 3. Como Aplicar no Mempool Miner

### Estrutura Proposta

```
┌─────────────────────────────────────────────────────────┐
│  LOGO    Mempool Miner          [🔍] [🔔] [👤 Profile]  │  ← Header
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ 📊       │  Home > Dashboard > Overview                 │  ← Breadcrumb
│ Dashboard│                                              │
│          │  ┌─────────────────────────────────────────┐ │
│ ⛏️       │  │                                         │ │
│ Miners   │  │           Conteúdo Principal            │ │
│          │  │                                         │ │
│ 📈       │  └─────────────────────────────────────────┘ │
│ Analytics│                                              │
│          │                                              │
│ 💰       │                                              │
│ Wallet   │                                              │
│          │                                              │
│ 📋       │                                              │
│ Tasks    │                                              │
│          │                                              │
│ ⚙️       │                                              │
│ Settings │                                              │
│          │                                              │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### Padrões Recomendados por Tela

#### Desktop (≥1024px)
- **Sidebar fixa à esquerda** com ícones + labels
- **Breadcrumb** no topo do conteúdo
- **Tabs** para sub-seções (ex: Miners > Active | Inactive | Archived)
- **Command Palette** (Ctrl+K) para navegação rápida
- **Header** com search, notificações, perfil

#### Tablet (768px–1023px)
- **Sidebar colapsável** (ícones apenas, expande ao hover/click)
- **Tabs** mantidos para sub-seções
- **Mega menu** se necessário para configurações

#### Mobile (<768px)
- **Bottom Navigation Bar** com 4-5 itens principais:
  - 📊 Dashboard
  - ⛏️ Miners
  - 💰 Wallet
  - 📋 Tasks
  - ⚙️ Settings (ou em hamburger)
- **Hamburger menu** para itens secundários
- **Bottom Sheet** para ações contextuais

### 12 Padrões Aplicáveis ao Mempool Miner

| # | Padrão | Onde Aplicar | Prioridade |
|---|--------|-------------|------------|
| 1 | Sidebar Navigation | Menu principal desktop | 🔴 Alta |
| 2 | Bottom Navigation | Menu principal mobile | 🔴 Alta |
| 3 | Breadcrumbs | Todas as páginas internas | 🔴 Alta |
| 4 | Tabs | Sub-seções (Active/Inactive) | 🔴 Alta |
| 5 | Active State Indicator | Item selecionado no menu | 🔴 Alta |
| 6 | Icons + Labels | Todos os itens de menu | 🔴 Alta |
| 7 | Hamburger Menu | Itens secundários mobile | 🟡 Média |
| 8 | Command Palette | Atalho rápido (Ctrl+K) | 🟡 Média |
| 9 | Accordion Menu | Settings com categorias | 🟡 Média |
| 10 | Off-Canvas Navigation | Menu mobile expandido | 🟡 Média |
| 11 | Mixed Pattern (Bottom + FAB) | Ação principal (ex: Add Miner) | 🟢 Baixa |
| 12 | Gesture Navigation | Swipe para voltar mobile | 🟢 Baixa |

### Lições-Chave

1. **Visibilidade > Esconder** — Menus ocultos reduzem descobribilidade. Mostre o que importa.
2. **Consistência é rei** — Mesmo padrão de navegação em todas as telas e dispositivos.
3. **Menos é mais** — Máximo 5-7 itens no menu principal. Agrupe o resto em submenus.
4. **Teste com usuários reais** — Prototipe e teste antes de implementar.
5. **Adapte por dispositivo** — Sidebar no desktop, bottom nav no mobile. Não force o mesmo padrão.
6. **Feedback visual** — Hover states, active states, e transições suaves reduzem confusão.
7. **Hierarquia clara** — Global → Local → Contextual. Cada nível serve um propósito diferente.
8. **Labels > Ícones** — Ícones sozinhos são ambíguos. Sempre combine com texto.

---

## 4. Referências

| Fonte | URL |
|-------|-----|
| NN/g - Menu Design Checklist (17 Guidelines) | https://www.nngroup.com/articles/menu-design/ |
| NN/g - Mobile Navigation Patterns | https://www.nngroup.com/articles/mobile-navigation-patterns/ |
| Eleken - UX Navigation Design | https://www.eleken.co/blog-posts/ux-navigation-design |
| UXPin - Mobile Navigation Patterns Pros & Cons | https://www.uxpin.com/studio/blog/mobile-navigation-patterns-pros-and-cons/ |
| Justinmind - Navigation Design Guide | https://www.justinmind.com/blog/navigation-design-almost-everything-you-need-to-know/ |
| Justinmind - Mobile Navigation Examples | https://www.justinmind.com/blog/mobile-navigation/ |
| Design Studio UI/UX - Mobile Navigation 2026 | https://www.designstudiouiux.com/blog/mobile-navigation-ux/ |
| IxDF - Navigation in UX Design | https://ixdf.org/literature/topics/navigation |
| Material Design - Bottom Navigation | https://m2.material.io/components/bottom-navigation |
| OneThing Design - Top 12 Navigation Patterns | https://www.onething.design/post/top-website-navigation-design-patterns |
| UX StackExchange - Bottom Nav vs Hamburger | https://ux.stackexchange.com/questions/105661/when-bottom-navigation-isnt-best |
| LukeW - Hamburger Menus Research | http://www.lukew.com/ff/entry.asp?1945 |
| Smashing Magazine - Responsive Navigation | https://www.smashingmagazine.com/2017/04/overview-responsive-navigation-patterns/ |
| Vanseo Design - 7 Responsive Navigation Patterns | https://vanseodesign.com/web-design/responsive-navigation-patterns/ |
| Lollypop - Hamburger Menu Design Tips | https://lollypop.design/blog/2025/december/hamburger-menu-design/ |

---

*Relatório gerado em 17/08/2026 para o projeto Mempool Miner.*
