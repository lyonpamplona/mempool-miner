# Research: Design Patterns para Mempool Miner

> Pesquisa sobre design patterns para organizar informações em dashboards e jogos, aplicáveis ao projeto Mempool Miner.

---

## 1. Padrões de Design Encontrados

### 1.1 Hierarquia Visual (Visual Hierarchy)

**O que é:** Organização de elementos por tamanho, peso, cor e espaçamento para guiar o olhar do usuário para o que é mais importante primeiro.

**Princípios-chave:**
- Elementos maiores atraem atenção primeiro — priorize informações críticas
- Contraste ajuda a priorizar calls-to-action
- Proximidade (Lei de Gestalt): itens próximos são percebidos como relacionados
- Espaçamento cria grupos visuais e reduz carga cognitiva
- Tipografia hierárquica (H1-H6) guia o scanning

**Referências:**
- https://ixdf.org/literature/topics/visual-hierarchy
- https://tubikstudio.com/blog/visual-hierarchy-effective-ui-content-organization/
- https://www.figma.com/resource-library/ui-design-principles/

---

### 1.2 Progressive Disclosure (Revelação Progressiva)

**O que é:** Mostrar apenas o mínimo necessário para a tarefa atual, revelando informações complexas sob demanda.

**Padrões de UI:**
- **Accordions:** Seções expansíveis/colapsáveis para otimizar espaço
- **Tabs:** Dividem conteúdo em painéis, mostrando um por vez
- **Modals/Pop-ups:** Informações extras sem sair do contexto
- **Tooltips/Popovers:** Contexto adicional ao passar o mouse
- **Toggles:** Revelam/escondem configurações avançadas
- **Menus colapsáveis e sidebars:** Recursos avançados dentro da UI primária

**Regra de ouro:** Apresente apenas os dados mínimos necessários para a tarefa em mãos. Mova opções complexas e pouco usadas para fora da interface principal.

**Referências:**
- https://ixdf.org/literature/topics/progressive-disclosure
- https://www.nngroup.com/articles/progressive-disclosure/
- https://ui-patterns.com/patterns/ProgressiveDisclosure
- https://primer.style/product/ui-patterns/progressive-disclosure/

---

### 1.3 Card-Based Layout (Layout Baseado em Cards)

**O que é:** Agrupamento de informações em retângulos ("cards") contendo dados, ações e contexto relacionados.

**Melhores práticas:**
- Use grids para layouts baseados em cards — consistência é fundamental
- Cards devem ser altamente consistentes entre si
- Agrupe informações relacionadas dentro do mesmo card
- Use auto-layout para redimensionamento responsivo
- Skeleton loading states que imitam o layout do conteúdo

**Referências:**
- https://baymard.com/blog/cards-dashboard-layout
- https://m2.material.io/components/cards
- https://uxdesign.cc/8-best-practices-for-ui-card-design-898f45bb60cc
- https://www.eleken.co/blog-posts/card-ui-examples-and-best-practices-for-product-owners

---

### 1.4 Bento Grid Layout

**O que é:** Layout em grid assimétrico com caixas de tamanhos variados, popularizado pela Apple. Cada caixa contém uma feature ou métrica, e o tamanho do box sinaliza importância.

**Princípios:**
- Caixas maiores = informações mais importantes
- Uniformidade visual mantém a digestibilidade
- Grid flexível com CSS Grid
- Cada "compartimento" conta uma parte da história
- Tipografia compacta, fundo escuro, texto claro

**Referências:**
- https://bentogrids.com/
- https://medium.com/@jefyjery10/apples-bento-grid-secret-how-a-lunchbox-layout-sells-premium-tech-7c118ce898aa
- https://www.banani.co/definitions/bento-grid
- https://senorit.de/en/blog/bento-grid-design-trend-2025

---

### 1.5 Densidade de Informação (Information Density)

**O que é:** A densidade de informação deve seguir o valor da informação — zonas de alto valor merecem densidade, zonas de baixo valor merecem espaço.

**Regras concretas:**
- **Razão 3:1** entre densidade de zonas primárias e secundárias
- **KPI strip primário:** 4-6 tiles, gutters de 8-12px
- **Painel secundário:** 24-32px de padding, máximo 2 elementos
- **Modos de densidade:** Comfortable (48-52px) vs Compact (28-32px)
- Limite de **6-8 charts por view**
- Tabelas densas com alinhamento consistente leem mais rápido que tabelas esparsas

**Referências:**
- https://www.setproduct.com/blog/effective-dashboard-design-principles
- https://fuselabcreative.com/dashboard-design-system/
- https://artofstyleframe.com/blog/dashboard-data-density-patterns/

---

### 1.6 Tab Navigation (Navegação por Abas)

**O que é:** Elementos de navegação que organizam conteúdo em views separadas sem recarregar a página.

**Melhores práticas:**
- Use apenas **uma linha de tabs**
- Tabs devem ter o mesmo comportamento visual e funcional
- Não misture navigation tabs com in-page tabs
- Design para escalabilidade — cada tab deve refletir um objetivo do usuário
- Indicadores de seleção claros (underline, bold, outline)
- Tabs scrolláveis com snap points para mobile

**Referências:**
- https://www.nngroup.com/articles/tabs-used-right/
- https://www.setproduct.com/blog/tabs-ui-design
- https://ui-patterns.com/patterns/NavigationTabs
- https://www.eleken.co/blog-posts/tabs-ux

---

### 1.7 Accordion Menu Design

**O que é:** Menu vertical com headers colapsáveis que revelam detalhes ao serem clicados.

**Quando usar:**
- Quando há mais de 2 seções principais com 2+ subseções cada
- Quando há menos de 10 seções principais
- Quando há apenas 2 níveis de navegação
- Quando o espaço lateral é limitado

**Melhores práticas:**
- Animação sutil para feedback visual
- Apenas um painel aberto por vez (padrão)
- Headers claros e descritivos
- Use para filtros, propriedades, e FAQ

**Referências:**
- https://www.nngroup.com/articles/accordions-on-desktop/
- https://ui-patterns.com/patterns/AccordionMenu
- https://blog.prototypr.io/designing-the-accordion-best-practices-3c1bd54bf26e
- https://www.shopify.com/blog/accordion-ui-design

---

### 1.8 Game HUD Design Principles

**O que é:** Princípios de design de interface para jogos que lidam com alta densidade de informação em tempo real.

**Princípios-chave (Kyle Kukshtel):**
1. **Fontes legíveis:** Sem pixel art fonts — use SDF fonts
2. **Indicação consistente de botões:** Todos os botões devem parecer similares
3. **Esquema de cores consistente:** ~8 cores totais na UI
4. **Encode informação duas vezes:** Número + cor (ex: health em verde/vermelho)
5. **Prefira símbolos sobre texto:** Eficiência e localização
6. **"Blow it up":** Se algo é importante, dê espaço proporcional
7. **Pense em consoles:** Navegação por controller desde o início

**Princípios gerais de Game UI:**
- Hierarquia clara de informação e legibilidade
- Consistência entre menus, sistemas e plataformas
- Design centrado no jogador
- Imersão através de integração temática
- Acessibilidade como feature central
- Feedback, responsividade e confiança do jogador
- Escalabilidade para jogos em evolução

**Referências:**
- https://kylekukshtel.com/game-ui-principles
- https://hickmandesign.co.uk/blog/other/the-core-principles-behind-successful-game-ui-ux-design/
- https://www.reddit.com/r/gamedev/comments/ng4287/7_obvious_beginner_mistakes_with_your_games_hud/
- https://www.toptal.com/designers/ui/game-ui

---

### 1.9 Dashboard Information Architecture

**O que é:** Estrutura lógica e visual de como a informação é distribuída em dashboards.

**6 Princípios (GoodData):**
1. **Structure:** Divisão entre dashboards segue áreas lógicas
2. **Navigation:** Global (entre dashboards) e local (tooltips, drills)
3. **Hierarchy:** Visual e lógica trabalhando juntas
4. **Grouping:** Informações similares juntas para comparação
5. **Labeling:** Claro, conciso e consistente
6. **Filtering:** Filtros para focar no relevante

**8 Princípios (Setproduct):**
1. Comece pela pergunta do usuário
2. Uma tela, uma decisão
3. Mostre mudança, não snapshots
4. Arredonde agressivamente (1.2M, não 1,234,567)
5. Cor codifica significado, não decoração
6. Densidade segue valor da informação
7. Filtragem reversível e visível
8. Frequência de atualização alinhada à necessidade

**Referências:**
- https://medium.com/gooddata-developers/six-principles-of-dashboards-information-architecture-5487d84c20c4
- https://www.setproduct.com/blog/effective-dashboard-design-principles
- https://dashboarddesignpatterns.github.io/
- https://uxpilot.ai/blogs/dashboard-design-principles

---

### 1.10 Data Visualization Best Practices

**O que é:** Escolha e uso correto de visualizações de dados.

**Regras:**
- **Bar charts:** Comparação entre categorias
- **Line charts:** Mudança ao longo do tempo
- **Bullet charts:** Progresso vs. meta
- **Histograms/Box plots:** Distribuição e outliers
- **Sparklines:** Tendência compacta dentro de KPIs
- Use cor para destacar, não decorar
- Coloque a informação mais importante no topo ou canto superior esquerdo
- Agrupe filtros com bordas visuais
- Evite dual-axis charts (correlação falsa)
- Limite a 7 categorias por cor

**Referências:**
- https://www.tableau.com/visualization/data-visualization-best-practices
- https://www.datacamp.com/tutorial/dashboard-design-tutorial
- https://www.sisense.com/blog/4-design-principles-creating-better-dashboards/
- https://www.rib-software.com/en/blogs/bi-dashboard-design-principles-best-practices

---

## 2. Como Organizar Informações de Forma Clara

### Princípios Fundamentais

1. **Comece pela pergunta:** Cada tela deve responder a uma pergunta específica do usuário. Se não consegue escrever a pergunta em 12 palavras, o design não está pronto.

2. **Uma tela, uma decisão:** Dashboards que suportam 5 decisões não suportam nenhuma bem. O usuário deve saber em 2 segundos qual ação a tela sugere.

3. **Hierarquia visual clara:**
   - Maior = mais importante
   - Mais denso = mais valor
   - Cor = significado (status), não decoração
   - Espaçamento = agrupamento lógico

4. **Progressive disclosure:**
   - Mostre o essencial na tela principal
   - Detalhes sob demanda (click, hover, drill-down)
   - Reduz carga cognitiva sem perder informação

5. **Consistência:**
   - Mesma cor = mesmo significado em toda a UI
   - Mesma estrutura de cards
   - Mesma tipografia hierárquica
   - Mesma lógica de navegação

6. **Densidade inteligente:**
   - Zonas primárias: densas (KPIs, charts principais)
   - Zonas secundárias: espaçadas (filtros, contexto)
   - Razão 3:1 entre primário e secundário

7. **Feedback imediato:**
   - Visual (animações, mudanças de cor)
   - Auditivo (quando aplicável)
   - Confirmação de ações

8. **Acessibilidade:**
   - Legível em escala de cinza
   - Contraste adequado
   - Texto redimensionável
   - Navegação por teclado

---

## 3. Como Aplicar no Mempool Miner

### 3.1 Layout Geral — Bento Grid

**Aplicação:** Use Bento Grid como estrutura principal do dashboard, com caixas de tamanhos variados:
- **Caixa grande (topo):** KPIs principais (hashrate, blocks found, revenue)
- **Caixas médias:** Charts de tendência (mempool size, fee rates, difficulty)
- **Caixas pequenas:** Status indicators, alerts, quick actions

**Por que funciona:** O tamanho do box comunica importância — o jogador/minerador vê o que importa primeiro.

---

### 3.2 Cards para Métricas — Card-Based Layout

**Aplicação:** Cada métrica do Mempool Miner em seu próprio card:
- **KPI Card:** Número grande + delta (▲ 8.2% vs ontem) + sparkline
- **Status Card:** Ícone + label + cor de status (verde/amarelo/vermelho)
- **Action Card:** Botão + descrição + progresso

**Padrão de KPI Card:**
```
┌─────────────────────────┐
│  Hashrate               │
│  ████████████░░  145 TH/s│
│  ▲ 12.3% vs 24h ago     │
│  ━━╱╲━━╱╲━━╱╲━━╱╲━━  │
└─────────────────────────┘
```

---

### 3.3 Progressive Disclosure para Dados Complexos

**Aplicação:**
- **Nível 1 (Dashboard):** KPIs agregados, status geral, alerts
- **Nível 2 (Click no card):** Detalhes da métrica, histórico, comparação
- **Nível 3 (Drill-down):** Dados brutos, configurações, logs

**Exemplo:**
- Dashboard mostra "Mempool: 45 MB"
- Click abre gráfico de tamanho do mempool ao longo do tempo
- Click no gráfico mostra transações individuais e fee distribution

---

### 3.4 Tabs para Navegação Principal

**Aplicação:** Tabs horizontais no topo para seções principais:
- **Overview:** Dashboard principal com KPIs
- **Mining:** Detalhes de mineração (pools, workers, hashrate)
- **Mempool:** Análise do mempool (fees, tamanho, transações)
- **Network:** Status da rede (difficulty, blocks, peers)
- **Settings:** Configurações

**Regra:** Máximo 5-7 tabs visíveis, com scroll se necessário.

---

### 3.5 Accordion para Detalhes Expansíveis

**Aplicação:**
- Lista de workers/miners com detalhes expansíveis
- Configurações agrupadas por categoria
- Logs com seções colapsáveis
- Filtros avançados

**Exemplo:**
```
▼ Worker 1 (Active) — 45 TH/s
  ├─ Uptime: 14d 6h
  ├─ Shares: 12,847
  └─ Temperature: 68°C

▶ Worker 2 (Idle)
▶ Worker 3 (Error)
```

---

### 3.6 Hierarquia Visual — Game HUD Style

**Aplicação:** Inspirado em HUDs de jogos:
- **Info crítica sempre visível:** Hashrate, revenue, status
- **Info secundária sob demanda:** Detalhes de pools, histórico
- **Encode duas vezes:** Número + cor (ex: hashrate verde se estável, vermelho se caiu)
- **Símbolos sobre texto:** Ícones para status, tendências, alertas
- **"Blow it up":** Métricas importantes merecem espaço proporcional

**Esquema de cores (máx. 8 cores):**
- Verde: Status bom / acima da meta
- Vermelho: Alerta / abaixo da meta / erro
- Amarelo: Atenção / warning
- Azul: Info / link / ação
- Cinza: Background / texto secundário
- Branco: Texto primário
- Roxo/Laranja: Brand accent / destaque

---

### 3.7 Densidade de Informação

**Aplicação:**
- **Zona primária (topo):** KPIs densos, gutters de 8-12px, 4-6 tiles
- **Zona secundária (meio):** Charts com padding de 16-24px
- **Zona terciária (fundo):** Logs, configurações com padding de 24-32px

**Modos de densidade:**
- **Comfortable:** Default para novos usuários
- **Compact:** Para power users que querem mais dados na tela

---

### 3.8 Data Visualization — Escolha de Charts

**Aplicação no Mempool Miner:**
- **Line chart:** Tendência de hashrate, fees, difficulty ao longo do tempo
- **Bar chart:** Comparação entre workers, pools, períodos
- **Bullet chart:** Progresso de blocks encontrados vs. meta
- **Sparkline:** Tendência compacta dentro de cada KPI card
- **Gauge:** Utilização de recursos (CPU, GPU, memória)
- **Table:** Lista de transações, workers, pools com sparklines inline

---

### 3.9 Feedback e Responsividade

**Aplicação:**
- **Visual:** Mudança de cor em tempo real quando métricas mudam
- **Animação:** Transições suaves entre estados (accordion, tabs)
- **Alertas:** Notificações visuais para eventos importantes (block found, difficulty change)
- **Tooltips:** Informações adicionais ao hover em qualquer métrica

---

### 3.10 Acessibilidade

**Aplicação:**
- Dashboard legível em escala de cinza (cor codifica significado, não é o único canal)
- Contraste mínimo 4.5:1 para texto
- Fontes legíveis (sem pixel art fonts)
- Navegação completa por teclado
- Textos alternativos para ícones e gráficos

---

## 4. Resumo dos 15 Padrões Aplicáveis

| # | Padrão | Aplicação no Mempool Miner |
|---|--------|---------------------------|
| 1 | **Hierarquia Visual** | KPIs maiores no topo, info secundária menor |
| 2 | **Progressive Disclosure** | Dashboard → Detalhes → Dados brutos |
| 3 | **Card-Based Layout** | Cada métrica em seu próprio card consistente |
| 4 | **Bento Grid** | Layout assimétrico com boxes de tamanhos variados |
| 5 | **Information Density** | Zonas primárias densas, secundárias espaçadas (3:1) |
| 6 | **Tab Navigation** | Seções principais (Overview, Mining, Mempool, Network) |
| 7 | **Accordion Menu** | Detalhes expansíveis de workers, configs, logs |
| 8 | **Game HUD Principles** | Info crítica sempre visível, encode duplo (número + cor) |
| 9 | **Dashboard IA** | Structure, Navigation, Hierarchy, Grouping, Labeling, Filtering |
| 10 | **Data Visualization** | Charts adequados ao tipo de dado (line, bar, bullet, sparkline) |
| 11 | **Color Encoding** | Cor = significado (status), não decoração; legível em grayscale |
| 12 | **Consistency** | Mesma cor, mesma estrutura, mesma tipografia em toda a UI |
| 13 | **Feedback Visual** | Mudanças em tempo real, animações, alertas |
| 14 | **Density Modes** | Comfortable vs Compact para diferentes tipos de usuário |
| 15 | **Accessibility** | Contraste, fontes legíveis, navegação por teclado |

---

## 5. Referências Completas

### Dashboard Information Architecture
- https://medium.com/gooddata-developers/six-principles-of-dashboards-information-architecture-5487d84c20c4
- https://www.setproduct.com/blog/effective-dashboard-design-principles
- https://dashboarddesignpatterns.github.io/
- https://uxpilot.ai/blogs/dashboard-design-principles
- https://www.pencilandpaper.io/articles/ux-pattern-analysis-data-dashboards

### Data Visualization
- https://www.tableau.com/visualization/data-visualization-best-practices
- https://www.datacamp.com/tutorial/dashboard-design-tutorial
- https://www.sisense.com/blog/4-design-principles-creating-better-dashboards/
- https://www.rib-software.com/en/blogs/bi-dashboard-design-principles-best-practices
- https://www.sigmacomputing.com/blog/best-practices-dashboard-design-examples
- https://omni.co/articles/data-visualization-best-practices-for-better-decision-making

### Game UI/HUD Design
- https://kylekukshtel.com/game-ui-principles
- https://hickmandesign.co.uk/blog/other/the-core-principles-behind-successful-game-ui-ux-design/
- https://www.reddit.com/r/gamedev/comments/ng4287/7_obvious_beginner_mistakes_with_your_games_hud/
- https://www.toptal.com/designers/ui/game-ui
- https://www.sketch.com/blog/game-ui-design/
- https://medium.com/@nicolaskraj/designing-efficient-user-interfaces-for-games-be20b516f1c2

### Progressive Disclosure
- https://ixdf.org/literature/topics/progressive-disclosure
- https://www.nngroup.com/articles/progressive-disclosure/
- https://ui-patterns.com/patterns/ProgressiveDisclosure
- https://primer.style/product/ui-patterns/progressive-disclosure/

### Card-Based Layout & Bento Grid
- https://baymard.com/blog/cards-dashboard-layout
- https://m2.material.io/components/cards
- https://uxdesign.cc/8-best-practices-for-ui-card-design-898f45bb60cc
- https://bentogrids.com/
- https://medium.com/@jefyjery10/apples-bento-grid-secret-how-a-lunchbox-layout-sells-premium-tech-7c118ce898aa
- https://www.banani.co/definitions/bento-grid

### Tab Navigation & Accordion
- https://www.nngroup.com/articles/tabs-used-right/
- https://www.setproduct.com/blog/tabs-ui-design
- https://ui-patterns.com/patterns/NavigationTabs
- https://www.nngroup.com/articles/accordions-on-desktop/
- https://ui-patterns.com/patterns/AccordionMenu
- https://www.shopify.com/blog/accordion-ui-design

### Information Density
- https://fuselabcreative.com/dashboard-design-system/
- https://artofstyleframe.com/blog/dashboard-data-density-patterns/
- https://www.setproduct.com/blog/effective-dashboard-design-principles

### Visual Hierarchy
- https://ixdf.org/literature/topics/visual-hierarchy
- https://tubikstudio.com/blog/visual-hierarchy-effective-ui-content-organization/
- https://www.figma.com/resource-library/ui-design-principles/

---

*Relatório gerado em 17 de Agosto de 2026*
*Pesquisa para o projeto Mempool Miner*
