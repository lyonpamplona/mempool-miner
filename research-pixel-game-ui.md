# Pixel Art Game UI Research Report for Mempool Miner

> **Data:** 18 de agosto de 2026
> **Objetivo:** Pesquisar padrões de design pixel art para jogos web e dashboards, identificando 10-15 padrões aplicáveis ao Mempool Miner com foco em responsividade e usabilidade em todos os tamanhos de tela.

---

## Executive Summary

This research surveyed pixel art UI design across web games, dashboards, and retro-inspired interfaces. The key finding: **pixel art UI works on all screen sizes when you separate the aesthetic layer from the layout layer**. Pixel art is a visual skin; responsive layout is a structural concern. The best implementations use CSS grid/flexbox for layout and pixel art only for component styling (borders, buttons, panels, typography).

---

## Patterns Found

### Pattern 1: Integer Pixel Grid System

**What it is:** Every spacing, padding, and dimension snaps to a base pixel unit (4px, 8px, or 16px). No fractional pixels anywhere.

**Why it matters:** Pixel art loses its crispness the moment you introduce sub-pixel rendering. A consistent grid keeps everything sharp at every scale.

**How to apply to Mempool Miner:**
- Already implemented in prototypes with `--px: 4px` as base unit
- Extend to ALL spacing: margins, paddings, gaps, font-sizes must be multiples of 4px
- Use CSS custom properties: `--px-1: 4px`, `--px-2: 8px`, `--px-4: 16px`, `--px-8: 32px`
- On mobile, keep the same grid — don't shrink the pixel unit

**References:**
- [Retro Pixel UI Skill — Grid System](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [MDN — Crisp pixel art look](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)

---

### Pattern 2: `image-rendering: pixelated` for Sharp Scaling

**What it is:** CSS property that forces browsers to scale images using nearest-neighbor interpolation instead of smoothing, preserving the blocky pixel look.

**Why it matters:** Without this, browsers anti-alias pixel art and it looks blurry at any scale.

**How to apply to Mempool Miner:**
- Apply to all pixel art images, backgrounds, and even text: `image-rendering: pixelated; image-rendering: crisp-edges;`
- Already in prototypes — ensure it's on the `<body>` and all pixel-art containers
- For SVG icons, use `shape-rendering: crispEdges`

**References:**
- [Retro Pixel UI Skill — CSS Effects](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 3: Fixed-Ratio Viewport with Fluid Surround

**What it is:** The game area maintains a fixed aspect ratio (4:3, 16:9) while the surrounding UI adapts fluidly. The viewport scales as a single unit.

**Why it matters:** This is how retro games handle different screens — the game world stays proportional, and UI elements around it resize independently.

**How to apply to Mempool Miner:**
- The mining dashboard (hash rate, blocks, balance) should be the "fixed viewport" — maintain its proportions
- Navigation tabs, side panels, and overlays use fluid CSS (flexbox/grid) around it
- Use `aspect-ratio` CSS property: `.game-viewport { aspect-ratio: 4/3; max-width: 960px; margin: 0 auto; }`
- On mobile, the viewport fills the screen; on desktop, it centers with letterboxing

**References:**
- [Retro Pixel UI Skill — Layout Patterns](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [AdamCYounis — Pixel Art Class: Intro to Game UI](https://www.youtube.com/watch?v=o3VHJ7g7M08)

---

### Pattern 4: Tile-Based Component Composition

**What it is:** Build UI screens from reusable, tessellating tiles (like game tilesets). Each component is a self-contained tile that snaps to the grid.

**Why it matters:** This is how classic game hardware worked — sprite engines composed screens from 8x8 or 16x16 tiles. It creates visual consistency and makes responsive layout trivial.

**How to apply to Mempool Miner:**
- Each stat card, upgrade item, and progress bar is a "tile" with fixed internal proportions
- Tiles stack vertically on mobile, arrange in grid on desktop
- Empty cells use dithering patterns (subtle repeating gradient) to show "empty space"
- Already partially implemented in prototypes with `.px-box` component

**References:**
- [UX Collective — 8-bit introduction to UX design](https://uxdesign.cc/an-8-bit-introduction-to-ux-design-6f96480432e4)
- [Retro Pixel UI Skill — Component Patterns](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 5: Limited Color Palette with Semantic Roles

**What it is:** Pick 4-8 core colors. Each color has a specific semantic role (success, warning, accent, background). No arbitrary colors.

**Why it matters:** Limited palettes create visual cohesion and reduce cognitive load. Classic consoles (NES: 54 colors, Game Boy: 4 greens) proved this works.

**How to apply to Mempool Miner:**
- Already defined in prototypes: Bitcoin orange (`#f7931a`), green (`#00ff88`), red (`#ff3b3b`), cyan (`#00e5ff`), magenta (`#ff44ff`)
- Map colors to semantics: green = mining active/success, red = stopped/error, orange = Bitcoin/balance, cyan = network/info, magenta = special events
- Use CSS variables so the entire palette can be swapped (e.g., Lightning Mode already swaps orange → cyan)

**References:**
- [NES Style Guide — Eiri Sanada](https://eirifu.wordpress.com/2025/02/21/a-style-guide-for-nes-inspired-pixel-art-in-your-retro-game/)
- [Retro Pixel UI Skill — Color Palettes](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 6: Pixel Borders via `box-shadow` (No `border-radius`)

**What it is:** Create pixel-art-style borders using `box-shadow` with zero blur and pixel-unit offsets. Sharp corners only — no `border-radius`.

**Why it matters:** Rounded corners break the pixel art aesthetic. `box-shadow` creates the illusion of beveled, 3D pixel edges.

**How to apply to Mempool Miner:**
- Already implemented in `.px-box` and `.px-btn` with inset shadows
- Pattern: `box-shadow: inset -2px -2px 0 0 var(--border-hi), inset 2px 2px 0 0 rgba(255,255,255,0.04), 3px 3px 0 0 rgba(0,0,0,0.6)`
- This creates: dark inner shadow (bottom-right), light inner highlight (top-left), and drop shadow
- Apply consistently to ALL panels, buttons, and cards

**References:**
- [Retro Pixel UI Skill — Pixel Borders](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 7: Pixel Font Stack with Fallback Hierarchy

**What it is:** Use a hierarchy of pixel fonts — display font for titles, data font for numbers, UI font for body text. All from Google Fonts.

**Why it matters:** Different contexts need different pixel fonts. Press Start 2P is great for titles but terrible for long text. VT323 is perfect for terminal-style data.

**How to apply to Mempool Miner:**
- Already using 3 fonts: Press Start 2P (titles), VT323 (data/logs), Pixelify Sans (UI body)
- Add `font-smoothing: none` to prevent anti-aliasing
- Scale sizes in pixel steps: 8px, 12px, 16px, 24px, 32px
- On mobile, increase VT323 base size for readability (numbers need to be legible at small sizes)

**References:**
- [Medium — Web Design Style: website with pixels](https://medium.com/design-bootcamp/web-design-style-website-with-pixels-757e41ac447e)
- [Retro Pixel UI Skill — Typography](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 8: CRT Scanline Overlay as Atmospheric Layer

**What it is:** A subtle `::after` pseudo-element with `repeating-linear-gradient` that simulates CRT scanlines over the entire viewport.

**Why it matters:** Scanlines add texture and depth, making flat pixel art feel like it's displayed on a real retro screen. At low opacity (0.03-0.05), they're atmospheric without being distracting.

**How to apply to Mempool Miner:**
- Already implemented in prototypes: `body::after` with scanline gradient
- Keep opacity at 0.03-0.05 for subtlety
- Respect `prefers-reduced-motion`: disable scanlines for users who prefer reduced motion
- Consider making scanline intensity a setting in the game

**References:**
- [Retro Pixel UI Skill — CRT Scanlines](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 9: Segmented Progress Bars (HP/MP Style)

**What it is:** Progress bars divided into discrete pixel blocks, like HP/MP bars in RPGs. Color transitions from green → yellow → red as the bar depletes.

**Why it matters:** Segmented bars communicate progress more viscerally than smooth gradients. Each segment is a "unit" the player can count.

**How to apply to Mempool Miner:**
- Block progress bar: divide into segments (e.g., 10 blocks), fill one per milestone
- Mining efficiency: segmented bar showing current vs. target hash rate
- Upgrade cooldowns: segmented countdown
- Use CSS `steps()` or individual `<div>` blocks for each segment
- Color transitions: green (full) → yellow (half) → red (low)

**References:**
- [Retro Pixel UI Skill — HP/Progress Bars](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [AdamCYounis — Pixel Art Class: Intro to Game UI](https://www.youtube.com/watch?v=o3VHJ7g7M08)

---

### Pattern 10: Sprite Sheet Animation with CSS `steps()`

**What it is:** Animate pixel art using CSS `background-position` with `steps()` timing function, creating frame-by-frame animation from a single sprite sheet image.

**Why it matters:** This is the most performant way to animate pixel art — no JavaScript, no canvas, just CSS. The browser handles it natively.

**How to apply to Mempool Miner:**
- Mining animation: animated pickaxe or spinning gear using sprite sheet
- Loading states: pixel spinner with `steps()` animation
- Status indicators: blinking cursor, pulsing "MINING" text
- Pattern:
```css
.sprite {
  width: 32px; height: 32px;
  background: url('spritesheet.png') 0 0;
  animation: walk 0.6s steps(4) infinite;
}
@keyframes walk { to { background-position: -128px 0; } }
```

**References:**
- [Retro Pixel UI Skill — Sprite Sheets](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 11: RPG Dialog Box for Notifications and Messages

**What it is:** Text boxes styled like RPG dialogue — double-pixel borders, typewriter text animation, blinking "continue" indicator.

**Why it matters:** RPG dialog boxes instantly signal "read this text carefully." Users have deep pattern recognition for this UI element.

**How to apply to Mempool Miner:**
- Block discovery notifications: appear as RPG dialog with typewriter effect
- Achievement unlocks: dialog box with "NEW ACHIEVEMENT" header
- Tutorial messages: step-by-step dialog boxes that guide new players
- Use `::before` for the blinking cursor/continue indicator
- Auto-dismiss with a segmented timer bar at the bottom

**References:**
- [Retro Pixel UI Skill — Dialog Boxes](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [UX Collective — 8-bit introduction to UX design](https://uxdesign.cc/an-8-bit-introduction-to-ux-design-6f96480432e4)

---

### Pattern 12: Pixel Menu with Arrow Cursor and Keyboard Navigation

**What it is:** Navigation menus with a pixel arrow cursor (`::before` pseudo-element), glowing highlight bar on the active item, and full arrow-key navigation.

**Why it matters:** Classic game menus feel deliberate and satisfying. The arrow cursor makes navigation feel like a game, not a website.

**How to apply to Mempool Miner:**
- Tab navigation: pixel arrow cursor that moves between tabs
- Upgrade selection: arrow cursor highlights the selected upgrade
- Settings menu: full keyboard navigation with arrow keys
- Use `:focus-visible` for glowing pixel outline: `outline: 2px solid var(--cyan); box-shadow: 0 0 8px var(--cyan);`
- Implement roving tabindex for screen reader compatibility

**References:**
- [Retro Pixel UI Skill — Menus](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [DEV — Accessible Retro Gamified Portfolio](https://dev.to/mewmewdevart/i-built-a-retro-gamified-portfolio-yes-with-pixel-art-games-windows-95-vibes-589k)

---

### Pattern 13: Responsive Pixel Art via CSS Grid + Media Queries

**What it is:** Use CSS Grid for layout structure and pixel art only for component styling. Media queries change the grid layout, not the pixel art itself.

**Why it matters:** This is the key insight for responsive pixel art UI. The pixel art aesthetic stays constant; the layout adapts. Pixel art is the skin, CSS Grid is the skeleton.

**How to apply to Mempool Miner:**
- Mobile (320px+): Single column, full-width tiles, bottom tab bar
- Tablet (768px+): Two-column grid, side navigation
- Desktop (1024px+): Three-column layout, fixed sidebar, centered game viewport
- The pixel art components (buttons, panels, borders) stay the same at every breakpoint
- Only the grid template changes: `grid-template-columns: 1fr` → `1fr 1fr` → `250px 1fr 300px`

**References:**
- [Retro Pixel UI Skill — Responsive](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [Medium — Web Design Style: website with pixels](https://medium.com/design-bootcamp/web-design-style-website-with-pixels-757e41ac447e)

---

### Pattern 14: Neon Glow Effects for Active States

**What it is:** Multi-layer `text-shadow` or `box-shadow` creating a neon glow effect. 3-5 shadow layers at increasing radii for depth.

**Why it matters:** Neon glow on dark backgrounds provides excellent contrast (WCAG AAA) and creates visual hierarchy. Active mining, special events, and important alerts "glow."

**How to apply to Mempool Miner:**
- Active mining status: glowing green text
- Lightning Mode: cyan glow on all Bitcoin elements
- Special events (halving, difficulty adjustment): magenta glow
- Pattern:
```css
.neon-text {
  color: var(--green);
  text-shadow: 0 0 7px var(--green), 0 0 10px var(--green),
               0 0 21px var(--green), 0 0 42px var(--green);
}
```
- Respect `prefers-reduced-motion`: reduce glow intensity for users who prefer it

**References:**
- [Retro Pixel UI Skill — Neon Glow](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

### Pattern 15: Chiptune Audio Feedback for Interactions

**What it is:** Short 8-bit sound effects generated via Web Audio API for menu navigation, confirmations, and errors. Square wave oscillators create classic chiptune sounds.

**Why it matters:** Audio feedback makes the interface feel alive and game-like. It's the difference between a static dashboard and an interactive experience.

**How to apply to Mempool Miner:**
- Menu navigate: short blip (440Hz, 50ms, square wave)
- Block found: rising tone (523→784Hz sweep, 100ms)
- Upgrade purchased: confirmation chime
- Error: buzz (150Hz, 200ms, sawtooth)
- Always provide a mute toggle
- Pattern:
```javascript
function playBeep(freq = 440, duration = 0.1, type = 'square') {
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type; osc.frequency.value = freq;
  gain.gain.value = 0.1;
  osc.connect(gain).connect(audioCtx.destination);
  osc.start();
  gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
  osc.stop(audioCtx.currentTime + duration);
}
```

**References:**
- [Retro Pixel UI Skill — Audio Cues](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)

---

## How to Apply All Patterns to Mempool Miner

### Architecture: Separate Aesthetic from Layout

```
┌─────────────────────────────────────────┐
│  LAYOUT LAYER (CSS Grid/Flexbox)        │
│  ┌─────────┬──────────┬──────────┐     │
│  │ Sidebar │  Main    │  Stats   │     │
│  │ (fluid) │ (fluid)  │ (fluid)  │     │
│  └─────────┴──────────┴──────────┘     │
│                                         │
│  AESTHETIC LAYER (Pixel Art Skin)       │
│  ┌─────────┬──────────┬──────────┐     │
│  │ px-box  │ px-box   │ px-box   │     │
│  │ px-btn  │ px-btn   │ px-bar   │     │
│  │ px-text │ px-text  │ px-badge │     │
│  └─────────┴──────────┴──────────┘     │
└─────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint | Layout | Navigation | Game Viewport |
|------------|--------|------------|---------------|
| 320px+ (mobile) | 1 column | Bottom tab bar | Full width, letterboxed |
| 768px+ (tablet) | 2 columns | Side icon nav | Centered, max 640px |
| 1024px+ (desktop) | 3 columns | Fixed sidebar | Centered, max 960px |
| 1440px+ (large) | 3 columns + extras | Fixed sidebar | Centered, max 960px, letterboxed |

### Component Checklist

- [x] Pixel grid system (`--px: 4px`)
- [x] Pixel borders via `box-shadow`
- [x] Pixel font stack (Press Start 2P, VT323, Pixelify Sans)
- [x] CRT scanline overlay
- [x] Limited color palette with CSS variables
- [ ] Segmented progress bars
- [ ] Sprite sheet animations
- [ ] RPG dialog notifications
- [ ] Pixel menu with arrow cursor
- [ ] Neon glow active states
- [ ] Chiptune audio feedback
- [ ] `image-rendering: pixelated` on all pixel elements
- [ ] `prefers-reduced-motion` support
- [ ] Keyboard navigation with roving tabindex
- [ ] WCAG AA contrast ratios verified

---

## Key Lessons for Responsive Pixel Art UI

1. **Pixel art is a skin, not a layout engine.** Use CSS Grid/Flexbox for structure; pixel art only for component styling.

2. **Integer scaling is non-negotiable.** `image-rendering: pixelated` and pixel-unit multiples keep everything crisp.

3. **The fixed-ratio viewport pattern** is the most proven approach: the game area maintains proportions while surrounding UI adapts.

4. **Tile-based composition** makes responsive layout trivial — tiles stack on mobile, grid on desktop.

5. **Accessibility is compatible with retro aesthetics.** Neon-on-dark achieves WCAG AAA. Keyboard navigation, ARIA labels, and `prefers-reduced-motion` all work within the pixel art style.

6. **CSS over JavaScript for effects.** Scanlines, glow, borders, and animations are all pure CSS. No JS paint loops needed.

7. **Audio feedback transforms static UI into interactive experience.** Even simple chiptune beeps make the interface feel alive.

---

## References

### Design Systems & Skills
- [Retro Pixel UI Skill — Complete Design System](https://mcpmarket.com/tools/skills/retro-pixel-ui-design)
- [NES.css — Windows 98 CSS Framework](https://jdan.github.io/98.css/)
- [XP.css — Windows XP CSS Framework](https://botoxparty.github.io/XP.css/)

### Articles & Guides
- [An 8-bit introduction to UX design — UX Collective](https://uxdesign.cc/an-8-bit-introduction-to-ux-design-6f96480432e4)
- [Web Design Style: website with pixels — Medium](https://medium.com/design-bootcamp/web-design-style-website-with-pixels-757e41ac447e)
- [A Style Guide for NES-inspired Pixel Art — Eiri Sanada](https://eirifu.wordpress.com/2025/02/21/a-style-guide-for-nes-inspired-pixel-art-in-your-retro-game/)
- [Pixel Art/8-bit Graphics in Modern Games — Logic Simplified](https://logicsimplified.com/newgames/rising-trend-of-pixel-art8-bit-graphic-style-use-in-modern-games/)
- [Accessible Retro Gamified Portfolio — DEV Community](https://dev.to/mewmewdevart/i-built-a-retro-gamified-portfolio-yes-with-pixel-art-games-windows-95-vibes-589k)

### Video Tutorials
- [Pixel Art Class — Intro to Game UI — AdamCYounis](https://www.youtube.com/watch?v=o3VHJ7g7M08)
- [Inventory UX Design — How Zelda, Resident Evil, and Doom Make Great Game Menu UX](https://www.youtube.com/watch?v=5_3BUU9ZmNo)

### Inspiration & Examples
- [Interface In Game — Pixel Art Collection](https://interfaceingame.com/games/?themes=pixel-art)
- [Pixel Art Game UI — Craftpix](https://craftpix.net/categorys/pixel-art-game-ui/)
- [Pixel Gaming Dashboard Design — Figma](https://www.figma.com/community/file/1263743017397717365/pixel-gaming-dashboard-design)
- [8-Bit Retro Menu System — Hakitos](https://hakitos.itch.io/8-bit-retro-menu-system)
- [Free Pixel Art UI Assets — itch.io](https://itch.io/game-assets/free/tag-pixel-art/tag-user-interface)

### Fonts
- [Press Start 2P — Google Fonts](https://fonts.google.com/specimen/Press+Start+2P)
- [VT323 — Google Fonts](https://fonts.google.com/specimen/VT323)
- [Pixelify Sans — Google Fonts](https://fonts.google.com/specimen/Pixelify+Sans)
- [Silkscreen — Google Fonts](https://fonts.google.com/specimen/Silkscreen)

### Technical References
- [MDN — Crisp pixel art look](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)
- [Bisqwit NES Palette Simulator](https://bisqwit.iki.fi/utils/nespalette.php)
- [8-Bit Guy — NES Graphical Limitations](https://www.youtube.com/watch?v=Tfh0ytz8S0k)

---

## Summary

**15 patterns identified**, all applicable to Mempool Miner:

| # | Pattern | Status in Mempool Miner |
|---|---------|------------------------|
| 1 | Integer Pixel Grid | ✅ Implemented |
| 2 | `image-rendering: pixelated` | ✅ Implemented |
| 3 | Fixed-Ratio Viewport | ⚠️ Partial |
| 4 | Tile-Based Composition | ⚠️ Partial |
| 5 | Limited Color Palette | ✅ Implemented |
| 6 | Pixel Borders via `box-shadow` | ✅ Implemented |
| 7 | Pixel Font Stack | ✅ Implemented |
| 8 | CRT Scanline Overlay | ✅ Implemented |
| 9 | Segmented Progress Bars | ❌ Not yet |
| 10 | Sprite Sheet Animation | ❌ Not yet |
| 11 | RPG Dialog Notifications | ❌ Not yet |
| 12 | Pixel Menu + Keyboard Nav | ⚠️ Partial |
| 13 | CSS Grid Responsive Layout | ✅ Implemented |
| 14 | Neon Glow Active States | ⚠️ Partial |
| 15 | Chiptune Audio Feedback | ❌ Not yet |

**Next priorities:** Segmented progress bars, sprite animations, RPG dialogs, and chiptune audio are the highest-impact additions that would transform the current prototype from "pixel-styled dashboard" to "immersive pixel game experience."
