# Pesquisa: Pixel Art UI Design para Mempool Miner

> Data: 17 de agosto de 2026
> Objetivo: Identificar padrões de design pixel art aplicáveis ao Mempool Miner — jogo web de mineração Bitcoin com estética retro/8-bit.

---

## 1. Padrões de Design Pixel Art Encontrados

### 1.1 Grid System e Escala de Pixels

**Princípio:** Todo elemento deve "snap" a uma grade de pixels inteiros (8px, 16px, 32px como unidades base). Sem pixels fracionários.

- **Unidade base:** 4px ou 8px como `--pixel-unit`
- **Espaçamento:** Múltiplos inteiros da unidade base (4px, 8px, 16px, 32px)
- **Escalamento:** Sempre usar fatores inteiros (2x, 3x, 4x) para preservar bordas nítidas
- **CSS crítico:** `image-rendering: pixelated;` e `image-rendering: crisp-edges;`

```css
:root {
  --pixel-unit: 4px;
  --px-1: 4px;
  --px-2: 8px;
  --px-4: 16px;
  --px-8: 32px;
}
```

**Referência:** [MDN — Crisp pixel art look](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)

---

### 1.2 Paletas de Cores Limitadas

**Princípio:** Escolher 4-8 cores principais. Cada cor deve "merecer" seu lugar.

**Paleta Cyberpunk Neon (recomendada para Mempool Miner):**
| Cor | Hex | Uso |
|-----|-----|-----|
| Magenta | `#ff00ff` | Acento principal, links, estados ativos |
| Ciano | `#00ffff` | Destaques, informações |
| Verde neon | `#39ff14` | Sucesso, terminal, dados |
| Rosa quente | `#ff1493` | Alertas, ênfase, hover |
| Azul elétrico | `#0066ff` | Botões, interativos |
| Fundo void | `#0a0a0a` | Background da página |
| Painel | `#1a1a2e` | Cards/panels |
| Superfície | `#16213e` | Superfícies elevadas |

**Paleta Bitcoin (alternativa temática):**
- Ouro Bitcoin: `#f7931a`
- Ouro escuro: `#c2780e`
- Fundo escuro: `#0d1117`
- Verde mineração: `#00ff88`
- Vermelho alerta: `#ff4444`

**Paleta Game Boy (nostalgia pura):**
- `#0f380f`, `#306230`, `#8bac0f`, `#9bbc0f`

**Referência:** [Retro Pixel UI Skill — Palettes](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### 1.3 Tipografia Pixel

**Fontes recomendadas (todas gratuitas via Google Fonts):**

| Fonte | Estilo | Melhor para |
|-------|--------|-------------|
| **Press Start 2P** | 8-bit NES | Títulos, logos, CTAs |
| **Silkscreen** | Pixel limpo | Labels de UI, botões |
| **Pixelify Sans** | Pixel moderno | Texto corpo, legível |
| **VT323** | Terminal CRT | Texto de terminal, logs |
| **IBM Plex Mono** | Terminal | Código, texto de terminal |

**Renderização pixel-perfect:**
```css
.pixel-text {
  font-family: 'Press Start 2P', monospace;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: unset;
  font-smooth: never;
  image-rendering: pixelated;
  text-rendering: optimizeSpeed;
}
```

**Escala de tamanhos:**
```css
.text-xs  { font-size: 8px;  line-height: 12px; }
.text-sm  { font-size: 12px; line-height: 16px; }
.text-md  { font-size: 16px; line-height: 24px; }
.text-lg  { font-size: 24px; line-height: 32px; }
.text-xl  { font-size: 32px; line-height: 40px; }
```

**Referência:** [Medium — Web Design Style: website with pixels](https://medium.com/design-bootcamp/web-design-style-website-with-pixels-757e41ac447e)

---

### 1.4 Efeitos CRT e Scanlines

**Scanlines (linhas de varredura CRT):**
```css
.scanlines::after {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    to y,
    transparent 0px,
    transparent 2px,
    rgba(0, 0, 0, 0.15) 2px,
    rgba(0, 0, 0, 0.15) 4px
  );
  pointer-events: none;
  z-index: 9999;
}
```

**Neon Glow (texto brilhante):**
```css
.neon-text {
  color: var(--neon-primary);
  text-shadow:
    0 0 7px var(--neon-primary),
    0 0 10px var(--neon-primary),
    0 0 21px var(--neon-primary),
    0 0 42px var(--neon-primary);
}
```

**Pixel Borders (bordas pixeladas):**
```css
.pixel-border {
  border: none;
  box-shadow:
    inset 2px 2px 0 0 #5B9BD5,
    inset -2px -2px 0 0 #1a1a2e,
    2px 2px 0 0 #334455;
}
```

**Referência:** [CSS-Tricks — Fun Times With CSS Pixel Art](https://css-tricks.com/fun-times-css-pixel-art/)

---

### 1.5 Componentes Estilo RPG/Game

**HP/Progress Bars (segmentadas):**
- Blocos pixelados segmentados
- Transição de cor: verde → amarelo → vermelho
- Animação frame-a-frame com `steps()`

**Dialog Boxes (caixas de diálogo RPG):**
- Bordas duplas pixeladas
- Texto estilo "máquina de escrever"
- Indicador piscante de "continuar"

**Botões:**
- Sem `border-radius` (cantos retos)
- Bordas pixel via `box-shadow`
- `:active` com translate de 2px para baixo (efeito "pressionar")

**Menus:**
- Cursor de seta pixel (`::before`)
- Barra de destaque brilhante
- Navegação por teclado (setas)

**Cards/Painéis:**
- Cantos pixelados
- Barra de título estilo OS dos anos 90
- Padding consistente na grade de pixels

**Referência:** [Pxlkit — 111 Retro Pixel-Art React Components](https://pxlkit.xyz/ui-kit)

---

### 1.6 Animações Pixel

**Sprite Sheets com CSS:**
```css
.sprite {
  width: 32px;
  height: 32px;
  background: url('spritesheet.png') 0 0;
  animation: walk 0.6s steps(4) infinite;
}
@keyframes walk {
  to { background-position: -128px 0; }
}
```

**Transições de tela:**
- **Fade:** Opacidade simples
- **Wipe:** `clip-path` da esquerda para direita
- **Pixelate dissolve:** Escalar para baixo + filtro pixelate
- **Iris:** `clip-path` circular expandindo do centro

**Pixel Mask (transição estilo 8-bit):**
- Matriz Bayer 4x4 para dithering ordenado
- Blocos de pixels aparecem/desaparecem em grade

**Referência:** [Codrops — Building a Nostalgic 8-bit Universe](https://tympanus.net/codrops/2025/12/23/building-a-nostalgic-8-bit-universe-with-modern-tech-a-vibe-coding-journey/)

---

### 1.7 Layout e Composição

**Tile-based composition:** Construir telas a partir de tiles reutilizáveis (como sprite engines de hardware).

**HUD-style layouts:** Layouts densos com dados, estilo cockpit/HUD de jogos.

**Bento Grid:** Layout em grade com células de tamanhos variados (1x1, 2x1, 2x2).

**Fixed-ratio viewport:** Manter proporção fixa do jogo, centralizado na tela.

**Referência:** [80 Level — A Look Into Game UI](https://80.lv/articles/a-look-into-games-ui-from-1960s-to-the-present)

---

### 1.8 Audio Feedback (Opcional)

**Chiptune SFX com Web Audio API:**
```javascript
const audioCtx = new AudioContext();
function playBeep(freq = 440, duration = 0.1, type = 'square') {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;  // 'square' para 8-bit clássico
  osc.frequency.value = freq;
  gain.gain.value = 0.1;
  osc.connect(gain).connect(audioCtx.destination);
  osc.start();
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  osc.stop(audioCtx.currentTime + duration);
}
```

| Ação | Som | Frequência |
|------|-----|------------|
| Navegar menu | Blip curto | 440Hz, 50ms, square |
| Confirmar | Tom ascendente | 523-784Hz, 100ms |
| Erro | Buzz | 150Hz, 200ms, sawtooth |

**Referência:** [Retro Pixel UI Skill — Audio Cues](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### 1.9 Canvas Pixel Art

**Técnica de upscale com canvas:**
1. Criar canvas com resolução baixa (ex: 128x128)
2. CSS width/height maior (ex: 512x512)
3. `image-rendering: pixelated` no CSS
4. `imageSmoothingEnabled = false` no contexto

**PixelationManager (Singleton):**
- Offscreen canvas para sample/downscale
- Upscale com `imageSmoothingEnabled = false`
- Preserva bordas nítidas em qualquer escala

**Referência:** [MDN — Crisp pixel art look](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)

---

### 1.10 Acessibilidade e Performance

**Acessibilidade:**
- Neon sobre escuro atinge WCAG AAA na maioria dos casos
- `#00ffff` sobre `#0a0a0a` = 16.3:1 (AAA)
- Fontes pixel apenas para headers/CTAs; usar fontes padrão para corpo
- `@media (prefers-reduced-motion: no-preference)` para animações
- Foco visível com outline brilhante pixelado

**Performance:**
- Efeitos em CSS puro (scanlines, glow, noise) — sem loops JS
- Fontes pixel subsetadas (Press Start 2P = ~8KB woff2)
- `will-change` apenas em elementos animando ativamente
- Opacity-based overlays têm custo mínimo de paint

**Referência:** [Retro Pixel UI Skill — Accessibility](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

## 2. Como Aplicar no Mempool Miner

### 2.1 Estrutura de Design Tokens

```css
:root {
  /* Bitcoin Mining Theme */
  --bitcoin-gold: #f7931a;
  --bitcoin-gold-dark: #c2780e;
  --bitcoin-gold-light: #ffb347;
  --mining-green: #00ff88;
  --mining-green-dim: #00cc6a;
  --alert-red: #ff4444;
  --info-cyan: #00ffff;
  --bg-void: #0a0a0a;
  --bg-panel: #1a1a2e;
  --bg-surface: #16213e;
  --text-primary: #e0e0ff;
  --text-secondary: #8888aa;
  --pixel-unit: 4px;
}
```

### 2.2 Componentes Específicos do Jogo

| Componente | Estilo Pixel Art |
|------------|-----------------|
| **Hash Rate Display** | Fonte Press Start 2P, cor ouro Bitcoin, glow neon |
| **Mining Progress Bar** | Barra segmentada estilo HP, blocos pixelados |
| **Block Discovery** | Animação de sprite + efeito de partículas pixel |
| **Mempool Queue** | Grid estilo inventário RPG, tiles 32x32 |
| **Transaction Feed** | Terminal com fonte VT323, scroll estilo CRT |
| **Upgrade Menu** | Dialog box RPG com bordas duplas pixel |
| **Stats Dashboard** | Bento grid com cards pixelados |
| **Achievement Badges** | Ícones pixel art 16x16 com glow |
| **Loading States** | Spinner pixelado + "MINING..." com dots animados |
| **Notifications** | Toast com slide pixelado + barra de tempo segmentada |

### 2.3 Layout do Jogo

```
┌─────────────────────────────────────────────┐
│  MEMPOOL MINER v1.0    [HASH: 0xABC...]    │  ← Header pixel
├──────────────────┬──────────────────────────┤
│                  │                          │
│  ⛏️ Mining Area  │   📊 Stats Panel         │  ← Área principal
│  [Canvas Game]   │   ├─ Hash Rate           │     (2 colunas)
│                  │   ├─ Blocks Mined        │
│                  │   ├─ BTC Balance         │
│                  │   └─ Uptime              │
├──────────────────┴──────────────────────────┤
│  📋 Mempool Queue  │  ⚡ Upgrades  │  🏆 Achievements │  ← Bottom bar
└─────────────────────────────────────────────┘
```

### 2.4 Stack Tecnológico Sugerido

- **CSS Custom Properties** para design tokens
- **Google Fonts:** Press Start 2P (títulos) + VT323 (terminal) + Inter (corpo)
- **Canvas API** para área de mineração com `image-rendering: pixelated`
- **CSS `steps()`** para animações de sprite
- **Web Audio API** para efeitos sonoros chiptune
- **Pxlkit** (`@pxlkit/ui-kit`) como referência para componentes prontos

---

## 3. Referências

### Artigos e Tutoriais
1. [Medium — Web Design Style: website with pixels](https://medium.com/design-bootcamp/web-design-style-website-with-pixels-757e41ac447e)
2. [CSS-Tricks — Fun Times With CSS Pixel Art](https://css-tricks.com/fun-times-css-pixel-art/)
3. [MDN — Crisp pixel art look with image-rendering](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)
4. [Codrops — Building a Nostalgic 8-bit Universe with Modern Tech](https://tympanus.net/codrops/2025/12/23/building-a-nostalgic-8-bit-universe-with-modern-tech-a-vibe-coding-journey/)
5. [80 Level — A Look Into Game UI: From 1960s to the Present](https://80.lv/articles/a-look-into-games-ui-from-1960s-to-the-present)
6. [Josh Comeau — Chasing the Pixel-Perfect Dream](https://www.joshwcomeau.com/css/pixel-perfection/)
7. [DEV Community — Creating Pixel Art with CSS](https://dev.to/jnschrag/creating-pixel-art-with-css-3451)
8. [LogRocket — Designing pixel art using CSS only](https://blog.logrocket.com/designing-pixel-art-css-only/)

### Bibliotecas e Kits
9. [Pxlkit — 111 Retro Pixel-Art React Components](https://pxlkit.xyz/ui-kit)
10. [Retro Pixel UI Skill (MCP Market)](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
11. [Google Fonts — Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P)
12. [Google Fonts — Silkscreen](https://fonts.google.com/specimen/Silkscreen)
13. [Google Fonts — Pixelify Sans](https://fonts.google.com/specimen/Pixelify+Sans)
14. [Google Fonts — VT323](https://fonts.google.com/specimen/VT323)

### Inspiração Visual
15. [One Page Love — Pixel Art Website Design Examples](https://onepagelove.com/style/pixel-art)
16. [Dribbble — Pixel Art UI](https://dribbble.com/search/pixel-art-ui)
17. [Webflow — Best Pixelart Websites](https://webflow.com/made-in-webflow/pixelart)
18. [Game UI Database](https://www.gameuidatabase.com/)
19. [Interface In Game](https://interfaceingame.com/)
20. [TBD — Decentralized Finance Platform (pixel art)](https://www.tbd.website/)

---

## 4. Resumo dos 15 Padrões Identificados

| # | Padrão | Aplicação no Mempool Miner |
|---|--------|---------------------------|
| 1 | **Grid de pixels inteiros** | Layout do jogo, espaçamento, padding |
| 2 | **Paleta limitada (4-8 cores)** | Tema Bitcoin + neon |
| 3 | **Fontes pixel (Press Start 2P)** | Títulos, displays de hash rate |
| 4 | **Scanlines CRT** | Overlay sutil na tela inteira |
| 5 | **Neon glow text** | Valores de BTC, hash rate |
| 6 | **Pixel borders (box-shadow)** | Cards, painéis, botões |
| 7 | **HP/Progress bars segmentadas** | Progresso de mineração de blocos |
| 8 | **Dialog boxes estilo RPG** | Menus de upgrade, configurações |
| 9 | **Sprite animation com steps()** | Animações de mineração, partículas |
| 10 | **Tile-based composition** | Mempool queue, inventário |
| 11 | **Bento grid layout** | Dashboard de estatísticas |
| 12 | **Canvas pixelated** | Área principal do jogo |
| 13 | **Terminal aesthetic** | Transaction feed, logs |
| 14 | **Chiptune audio feedback** | Sons de bloco minerado, upgrades |
| 15 | **Pixel mask transitions** | Transições entre telas/modos |
