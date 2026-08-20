# Pesquisa: Componentes UI Pixel Art para Mempool Miner

> **Data:** 2026-08-17
> **Projeto:** Mempool Miner — Interface web com estilo pixel art / 8-bit
> **Objetivo:** Identificar componentes UI pixel art aplicáveis, técnicas CSS e frameworks prontos

---

## 1. Componentes UI Pixel Art Encontrados

### 1.1 Frameworks e Bibliotecas Prontas

| Framework | Tipo | Descrição | Link |
|-----------|------|-----------|------|
| **NES.css** | CSS puro | Framework NES-style com botões, containers, progress bars, inputs, tabelas, diálogos, listas, badges, ícones | https://nostalgic-css.github.io/NES.css/ |
| **8bitcn/ui** | React + Tailwind | 105+ componentes 8-bit baseados em shadcn/ui. Botões, cards, modais, tabelas, forms, badges, avatares | https://8bitcn.com/ |
| **PxlKit UI Kit** | React + Tailwind | 111 componentes pixel art. PixelButton, PixelCard, PixelProgress, PixelInput, PixelSelect, PixelTable, PixelModal, PixelBadge, PixelStatCard, PixelBento, PixelScrollArea, PixelTabs, PixelAccordion, PixelAlert, PixelPagination, PixelStepper, PixelSpinner, PixelBarChart, PixelAreaChart, PixelSparkline, PixelColorInput, PixelDatePicker, PixelCombobox, PixelMultiSelect, PixelOTPInput, PixelFileUpload, PixelForm, PixelDataTable, PixelSidebar, PixelCarousel, PixelTimeline, PixelStatGroup, PixelAvatarGroup, PixelBadgeGroup, PixelChipGroup, PixelInputGroup, PixelToggleGroup, PixelDateRangePicker, PixelCalendarGrid, PixelPopover, PixelDrawer, PixelCommand, PixelAlertDialog, PixelSheet, PixelToast, PixelTypewriter, PixelGlitch, PixelFloat, PixelShake, PixelRotate, PixelZoomIn, PixelFlicker, PixelParallax, PixelFadeIn, PixelSlideIn, PixelPulse, PixelBounce, PixelDivider, PixelSection, PixelBox, PixelStack, PixelCluster, PixelGrid, PixelEqualHeightGrid, PixelCenter, PixelContainer, PixelTwoColumn, PixelSectionHeader, PixelRibbon, PixelFeatureCard, PixelPricingCard, PixelTestimonialCard, PixelStarRating, PixelIconFrame, PixelHeroSection, PixelHeroMedia, PixelBentoCell, PixelPortal, PixelBreadcrumb, PixelKbd, PixelColorSwatch, PixelPasswordInput, PixelTextarea, PixelCodeInline, PixelTextLink, PixelCollapsible, PixelBareButton, PixelBareInput, PixelBareTextarea, PixelEmptyState, PixelSkeleton | https://pxlkit.xyz/ui-kit |
| **Pixelact UI** | React (shadcn) | Biblioteca pixel art sobre shadcn/ui | https://www.pixelactui.com |
| **Retro UI** | React | Componentes pixel-perfect retro com TypeScript e Tailwind | https://retroui.io/ |
| **NeoBrutalism** | React | 50+ componentes retro (não pixel art, mas estilo similar) | https://neobrutalism.com/ |
| **Phaser PixUI** | JS (Phaser 4) | Biblioteca UI para jogos pixel art no Phaser | https://phaser.io/news/2026/02/phaser-pixel-art-ui-library |

### 1.2 Recursos de Assets Gratuitos

| Recurso | Descrição | Link |
|---------|-----------|------|
| **Itch.io - Pixel Art UI** | Pacotes completos de UI/HUD: health bars, inventory slots, buttons, panels | https://itch.io/game-assets/tag-pixel-art/tag-user-interface |
| **Itch.io - Retro UI** | Assets retro com ícones, menus, painéis | https://itch.io/game-assets/tag-retro/tag-user-interface |
| **CraftPix - Game GUI** | GUIs para platformer, casual, fantasy, cartoon | https://craftpix.net/categorys/gui/ |
| **Pixel Progress Bar Pack** | Barras de progresso pixel art em 14 cores (linear + circular) | https://catshaped.itch.io/pixel-progress-bar-asset-pack |
| **Figma Pixel Art UI Kit** | Kit de design no Figma com componentes pixel art | https://www.figma.com/community/file/1224460064522598216/pixel-art-ui-kit |

### 1.3 Ferramentas Úteis

| Ferramenta | Descrição | Link |
|------------|-----------|------|
| **Pixel Art to CSS** | Editor visual de pixel art que exporta CSS | https://pixelartcss.com/ |
| **CodePen - Pixel Buttons** | Exemplo de botões pixel art com CSS puro | https://codepen.io/ssinya123/pen/GRMBwLM |
| **FreeFrontend CSS Pixel Art** | 20+ exemplos de pixel art em CSS | https://freefrontend.com/css-pixel-art/ |

---

## 2. Como Aplicar no Mempool Miner

O Mempool Miner é uma interface web (HTML/CSS/JS vanilla no diretório `frontend/`). Abaixo estão os componentes mais aplicáveis:

### 2.1 Componentes Prioritários (12 componentes)

| # | Componente | Aplicação no Mempool Miner | Framework/Abordagem |
|---|-----------|---------------------------|---------------------|
| 1 | **Botões Pixel Art** | Botões de ação (Start Mining, Settings, etc.) | NES.css `.nes-btn` ou CSS custom com box-shadow |
| 2 | **Containers/Painéis** | Painéis de status, dashboard, configurações | NES.css `.nes-container` ou CSS custom |
| 3 | **Progress Bars** | Barra de progresso de mineração, hash rate | NES.css `.nes-progress` ou CSS custom |
| 4 | **Inputs de Texto** | Campos de configuração (pool URL, porta) | NES.css `.nes-input` ou CSS custom |
| 5 | **Badges/Labels** | Status (Online, Mining, Error) | NES.css `.nes-badge` ou CSS custom |
| 6 | **Tabelas** | Lista de transações, blocos encontrados | NES.css `.nes-table` ou CSS custom |
| 7 | **Checkboxes/Radios** | Opções de configuração | NES.css `.nes-checkbox`, `.nes-radio` |
| 8 | **Select Dropdowns** | Seleção de pool, rede (mainnet/testnet) | NES.css `.nes-select` ou CSS custom |
| 9 | **Diálogos/Modals** | Confirmações, alertas, ajuda | NES.css `.nes-dialog` ou CSS custom |
| 10 | **Balões/Balloon** | Tooltips, mensagens de status | NES.css `.nes-balloon` |
| 11 | **Ícones Pixel Art** | Ícones de Bitcoin, hash, wallet | NES.css `.nes-icon` ou assets do Itch.io |
| 12 | **Fontes Pixel Art** | Tipografia geral da interface | Google Fonts: "Press Start 2P" |

---

## 3. Exemplos de Código CSS

### 3.1 Fontes Pixel Art

```css
/* Importar fonte Press Start 2P do Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* Aplicar em toda a interface */
body {
  font-family: 'Press Start 2P', system-ui, monospace;
  image-rendering: pixelated; /* Mantém imagens nítidas ao escalar */
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}
```

### 3.2 Botões Pixel Art (CSS Puro — Técnica NES.css)

```css
/* Botão pixel art com borda em bloco (técnica box-shadow) */
.pixel-btn {
  display: inline-block;
  padding: 12px 24px;
  font-family: 'Press Start 2P', system-ui;
  font-size: 12px;
  color: #fff;
  background-color: #6abc3a;
  border: none;
  cursor: pointer;
  /* Borda pixelada usando box-shadow em vez de border-radius */
  box-shadow:
    inset -4px 0 0 0 #000,
    inset 4px 0 0 0 #000,
    inset 0 -4px 0 0 #000,
    inset 0 4px 0 0 #000,
    4px 4px 0 0 #000;
  transition: transform 0.1s, box-shadow 0.1s;
}

.pixel-btn:hover {
  background-color: #7cd147;
}

.pixel-btn:active {
  transform: translate(4px, 4px);
  box-shadow:
    inset -4px 0 0 0 #000,
    inset 4px 0 0 0 #000,
    inset 0 -4px 0 0 #000,
    inset 0 4px 0 0 #000;
}

/* Variantes de cor */
.pixel-btn.primary { background-color: #3068c0; }
.pixel-btn.success { background-color: #6abc3a; }
.pixel-btn.warning { background-color: #d9a066; }
.pixel-btn.error   { background-color: #c03030; }
.pixel-btn.dark    { background-color: #212529; }
```

### 3.3 Containers/Painéis Pixel Art

```css
/* Painel pixel art com borda em bloco */
.pixel-panel {
  background: #fff;
  border: 4px solid #000;
  padding: 20px;
  margin: 16px 0;
  box-shadow: 8px 8px 0 0 rgba(0, 0, 0, 0.15);
  position: relative;
}

/* Painel com título */
.pixel-panel.with-title::before {
  content: attr(data-title);
  position: absolute;
  top: -14px;
  left: 16px;
  background: #fff;
  padding: 0 8px;
  font-family: 'Press Start 2P', system-ui;
  font-size: 10px;
  color: #000;
}

/* Painel escuro */
.pixel-panel.dark {
  background: #212529;
  border-color: #495057;
  color: #fff;
}

.pixel-panel.dark.with-title::before {
  background: #212529;
  color: #fff;
}
```

### 3.4 Progress Bar Pixel Art

```css
/* Barra de progresso pixel art */
.pixel-progress {
  width: 100%;
  height: 24px;
  background: #fff;
  border: 4px solid #000;
  position: relative;
  overflow: hidden;
}

.pixel-progress::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: var(--progress, 0%);
  background: #6abc3a;
  /* Padrão de pixels na barra de progresso */
  background-image:
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 4px,
      rgba(0,0,0,0.1) 4px,
      rgba(0,0,0,0.1) 8px
    );
  transition: width 0.3s steps(10);
}

/* Variantes de cor */
.pixel-progress.success::before { background: #6abc3a; }
.pixel-progress.warning::before { background: #d9a066; }
.pixel-progress.error::before   { background: #c03030; }
.pixel-progress.pattern::before {
  background: repeating-linear-gradient(
    45deg,
    #6abc3a,
    #6abc3a 4px,
    #4a9a2a 4px,
    #4a9a2a 8px
  );
}
```

### 3.5 Inputs Pixel Art

```css
/* Campo de input pixel art */
.pixel-input {
  width: 100%;
  padding: 10px 12px;
  font-family: 'Press Start 2P', system-ui;
  font-size: 10px;
  color: #000;
  background: #fff;
  border: 4px solid #000;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.pixel-input:focus {
  border-color: #3068c0;
}

.pixel-input.success { border-color: #6abc3a; }
.pixel-input.warning { border-color: #d9a066; }
.pixel-input.error   { border-color: #c03030; }
.pixel-input.dark    {
  background: #212529;
  border-color: #495057;
  color: #fff;
}

/* Label do campo */
.pixel-field label {
  display: block;
  font-family: 'Press Start 2P', system-ui;
  font-size: 10px;
  margin-bottom: 8px;
  color: #000;
}

.pixel-field.dark label { color: #fff; }
```

### 3.6 Badges/Labels Pixel Art

```css
/* Badge pixel art */
.pixel-badge {
  display: inline-block;
  padding: 4px 8px;
  font-family: 'Press Start 2P', system-ui;
  font-size: 8px;
  color: #fff;
  background: #3068c0;
  border: 2px solid #000;
  box-shadow: 3px 3px 0 0 rgba(0, 0, 0, 0.2);
}

.pixel-badge.success { background: #6abc3a; }
.pixel-badge.warning { background: #d9a066; }
.pixel-badge.error   { background: #c03030; }
.pixel-badge.dark    { background: #212529; }
```

### 3.7 Tabelas Pixel Art

```css
/* Tabela pixel art */
.pixel-table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Press Start 2P', system-ui;
  font-size: 9px;
}

.pixel-table th,
.pixel-table td {
  padding: 10px 12px;
  border: 3px solid #000;
  text-align: left;
}

.pixel-table th {
  background: #f0f0f0;
  color: #000;
}

.pixel-table tr:nth-child(even) {
  background: #f9f9f9;
}

.pixel-table.dark th {
  background: #343a40;
  color: #fff;
}

.pixel-table.dark td {
  background: #212529;
  color: #fff;
}
```

### 3.8 Diálogos/Modais Pixel Art

```css
/* Modal pixel art */
.pixel-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #fff;
  border: 4px solid #000;
  padding: 24px;
  z-index: 1000;
  min-width: 320px;
  max-width: 90vw;
  box-shadow: 12px 12px 0 0 rgba(0, 0, 0, 0.2);
}

.pixel-dialog .dialog-title {
  font-family: 'Press Start 2P', system-ui;
  font-size: 14px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 3px solid #000;
}

.pixel-dialog .dialog-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  justify-content: flex-end;
}

/* Overlay escuro */
.pixel-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 999;
}
```

### 3.9 Balões/Tooltips Pixel Art

```css
/* Balão pixel art (estilo NES.css) */
.pixel-balloon {
  background: #fff;
  border: 4px solid #000;
  padding: 16px;
  position: relative;
  font-family: 'Press Start 2P', system-ui;
  font-size: 10px;
  line-height: 1.8;
}

/* Seta do balão */
.pixel-balloon::after {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 24px;
  border: 8px solid transparent;
  border-top-color: #000;
}

.pixel-balloon::before {
  content: '';
  position: absolute;
  bottom: -12px;
  left: 26px;
  border: 6px solid transparent;
  border-top-color: #fff;
}

/* Posições */
.pixel-balloon.from-left::before,
.pixel-balloon.from-left::after {
  left: 24px;
}

.pixel-balloon.from-right::before,
.pixel-balloon.from-right::after {
  left: auto;
  right: 24px;
}
```

### 3.10 Switch/Toggle Pixel Art

```css
/* Switch pixel art */
.pixel-switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 32px;
}

.pixel-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.pixel-switch .slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #c03030;
  border: 3px solid #000;
  transition: 0.2s;
}

.pixel-switch .slider::before {
  content: '';
  position: absolute;
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background: #fff;
  border: 2px solid #000;
  transition: 0.2s;
}

.pixel-switch input:checked + .slider {
  background: #6abc3a;
}

.pixel-switch input:checked + .slider::before {
  transform: translateX(28px);
}
```

### 3.11 Scrollbar Pixel Art

```css
/* Scrollbar pixel art */
.pixel-scroll::-webkit-scrollbar {
  width: 16px;
}

.pixel-scroll::-webkit-scrollbar-track {
  background: #f0f0f0;
  border: 2px solid #000;
}

.pixel-scroll::-webkit-scrollbar-thumb {
  background: #6abc3a;
  border: 2px solid #000;
}

.pixel-scroll::-webkit-scrollbar-thumb:hover {
  background: #7cd147;
}
```

### 3.12 Animações Pixel Art

```css
/* Animação de piscar (blink) */
@keyframes pixel-blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

.pixel-blink {
  animation: pixel-blink 1s steps(2) infinite;
}

/* Animação de pulso */
@keyframes pixel-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.pixel-pulse {
  animation: pixel-pulse 2s ease-in-out infinite;
}

/* Animação de shake */
@keyframes pixel-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.pixel-shake {
  animation: pixel-shake 0.3s ease-in-out;
}

/* Animação de digitação (typewriter) */
@keyframes pixel-typewriter {
  from { width: 0; }
  to { width: 100%; }
}

.pixel-typewriter {
  overflow: hidden;
  white-space: nowrap;
  border-right: 3px solid #000;
  animation: pixel-typewriter 2s steps(30) forwards;
}
```

---

## 4. Técnicas Principais para Pixel Art em CSS

### 4.1 Borda Pixelada com Box-Shadow
A técnica mais importante: usar `box-shadow` em vez de `border` para criar bordas em bloco sem anti-aliasing.

```css
/* Bordas pixeladas — sem anti-aliasing do navegador */
.pixel-border {
  box-shadow:
    inset -4px 0 0 0 #000,
    inset 4px 0 0 0 #000,
    inset 0 -4px 0 0 #000,
    inset 0 4px 0 0 #000;
}
```

### 4.2 Manter Imagens Nítidas
```css
/* Impede que o navegador suavize imagens pixel art */
.pixel-image {
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}
```

### 4.3 Animações com Steps
```css
/* Animações frame-a-frame sem suavização */
.pixel-anim {
  animation: my-anim 1s steps(8) infinite;
}
```

### 4.4 Paleta de Cores Retro
```css
:root {
  /* Paleta NES clássica */
  --nes-red:    #c03030;
  --nes-green:  #6abc3a;
  --nes-blue:   #3068c0;
  --nes-yellow: #d9d038;
  --nes-orange: #d9a066;
  --nes-black:  #000000;
  --nes-white:  #ffffff;
  --nes-gray:   #f0f0f0;
  --nes-dark:   #212529;
}
```

---

## 5. Recomendações de Implementação para Mempool Miner

### 5.1 Abordagem Recomendada

Para o Mempool Miner (HTML/CSS/JS vanilla), a melhor abordagem é:

1. **NES.css via CDN** — Para prototipagem rápida e componentes prontos
   ```html
   <link href="https://unpkg.com/nes.css@latest/css/nes.min.css" rel="stylesheet" />
   <link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
   ```

2. **CSS Custom Progressivo** — Substituir gradualmente NES.css por CSS customizado para controle total

3. **Assets do Itch.io** — Para ícones e elementos visuais adicionais (health bars, inventory slots, etc.)

### 5.2 Componentes para Implementar Primeiro

| Prioridade | Componente | Tempo Estimado |
|------------|-----------|----------------|
| P0 | Botões pixel art | 30 min |
| P0 | Fontes + paleta de cores | 15 min |
| P1 | Containers/painéis | 30 min |
| P1 | Progress bars | 30 min |
| P2 | Inputs + selects | 45 min |
| P2 | Tabelas | 30 min |
| P3 | Badges + labels | 15 min |
| P3 | Diálogos/modals | 45 min |
| P4 | Balões/tooltips | 30 min |
| P4 | Animações | 30 min |

### 5.3 Estrutura de Arquivos Sugerida

```
frontend/
├── style.css              # Estilos globais + variáveis CSS
├── style-pixel.css        # Componentes pixel art (novo)
├── index.html
├── game.js
└── icons/
    └── pixel-icons/       # Ícones pixel art (novo)
        ├── bitcoin.png
        ├── hash.png
        ├── wallet.png
        └── ...
```

---

## 6. Referências

### Frameworks e Bibliotecas
1. **NES.css** — https://nostalgic-css.github.io/NES.css/
2. **8bitcn/ui** — https://8bitcn.com/
3. **PxlKit UI Kit** — https://pxlkit.xyz/ui-kit
4. **Pixelact UI** — https://www.pixelactui.com
5. **Retro UI** — https://retroui.io/
6. **NeoBrutalism** — https://neobrutalism.com/

### Tutoriais e Exemplos
7. **CodePen - Simple Pixel Art Buttons** — https://codepen.io/ssinya123/pen/GRMBwLM
8. **DEV.to - Create 8bit-like site with NES.css** — https://dev.to/0xkoji/create-8bit-like-site-with-nes-css-2fjn
9. **FreeFrontend - CSS Pixel Art** — https://freefrontend.com/css-pixel-art/
10. **Pixel Art to CSS** — https://pixelartcss.com/
11. **CSS Pixel Art — Box-Shadow Technique** — https://abduarrahman.com/blog/css-pixel-art-box-shadow-22-effects/
12. **Preserving Pixel Art Look in Web Content** — https://www.kirupa.com/hodgepodge/preserving_pixel_art_aesthetics.htm

### Assets Gratuitos
13. **Itch.io - Pixel Art UI** — https://itch.io/game-assets/tag-pixel-art/tag-user-interface
14. **Itch.io - Retro UI** — https://itch.io/game-assets/tag-retro/tag-user-interface
15. **CraftPix - Game GUI** — https://craftpix.net/categorys/gui/
16. **Pixel Progress Bar Pack** — https://catshaped.itch.io/pixel-progress-bar-asset-pack
17. **Figma Pixel Art UI Kit** — https://www.figma.com/community/file/1224460064522598216/pixel-art-ui-kit

### Fontes
18. **Press Start 2P** (Google Fonts) — https://fonts.google.com/specimen/Press+Start+2P
19. **JetBrains Mono** (Google Fonts) — https://fonts.google.com/specimen/JetBrains+Mono

---

## 7. Resumo Executivo

### O que foi encontrado:
- **6 frameworks** prontos para uso (NES.css, 8bitcn, PxlKit, Pixelact, Retro UI, NeoBrutalism)
- **12+ componentes UI** pixel art identificados e aplicáveis ao Mempool Miner
- **12 exemplos de código CSS** completos e prontos para implementação
- **17 referências** com frameworks, tutoriais, assets e fontes

### Principais técnicas CSS:
1. **Box-shadow para bordas** — Cria bordas em bloco sem anti-aliasing
2. **image-rendering: pixelated** — Mantém imagens nítidas ao escalar
3. **steps() em animações** — Animações frame-a-frame sem suavização
4. **Press Start 2P** — Fonte pixel art padrão da indústria

### Recomendação:
Começar com **NES.css via CDN** para prototipagem rápida, depois migrar para **CSS custom** para controle total. Os 12 componentes listados na seção 2.1 cobrem todas as necessidades do Mempool Miner.
