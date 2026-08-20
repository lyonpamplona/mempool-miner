# Structural Redesign Regressions — UI Audit Report

**Date:** 2026-08-19  
**Scope:** `frontend/index.html`, `pixel.css`, `style.css`, `game.js`, `service-worker.js`  
**Method:** Static analysis only (read-only). No edits made.  
**Note:** `prototype-pixel-final-v3.html` not found on disk. `new-design.html` does not exist. `style.css` is **NOT loaded** by `index.html` — it is dead code.

---

## Visual Slop Score: **7.2 / 10** (HIGH)

| Category | Score | Notes |
|----------|-------|-------|
| CSS Architecture | 8/10 | Two full CSS files with overlapping selectors; style.css is dead but still maintained |
| HTML Structure | 6/10 | Compatibility aliases div with 19 hidden elements; valid but bloated |
| JS Architecture | 7/10 | Duplicate `showTab()` definitions; 40+ innerHTML injections; 2 DOMContentLoaded handlers |
| Responsive Design | 8/10 | Only 2 breakpoints (900px, 559px); missing tablet/medium range |
| Theme Consistency | 9/10 | Dark theme throughout, but task direction says light/beige — **theme mismatch** |
| Accessibility | 5/10 | Missing skip-link, visually-hidden class; good ARIA on grid but inconsistent elsewhere |

---

## Confirmed Bugs

### BUG-01: `showTab()` defined twice in game.js
- **File:** `game.js`
- **Lines:** 21-24 and 140-164
- **Evidence:** Two `function showTab()` declarations. Line 21 is a compatibility wrapper that calls `switchTab()`. Line 140 is the original full implementation that operates on `.tab-content` and `.nav-btn` classes (old layout). Both are hoisted, so the second overwrites the first.
- **Impact:** The v2 `showTab()` (line 140) wins. It queries `.tab-content` and `.nav-btn` which don't exist in the new HTML (which uses `.tab-pane` and `.mecha-btn`). **Tab switching via `showTab()` is broken.**
- **Fix:** Remove the duplicate at line 140. Keep only the compatibility wrapper at line 21, or update line 140 to use new class names.

### BUG-02: `querySelector('#btn-sprint-play-again')` references missing ID
- **File:** `game.js`
- **Lines:** 5696, 5703
- **Evidence:** `getElementById('btn-sprint-play-again')` and `querySelector('#btn-sprint-play-again')` called but ID does not exist in `index.html`.
- **Impact:** Sprint "play again" button throws `TypeError: Cannot read properties of null`. Sprint mode cannot be restarted.
- **Fix:** Add `<button id="btn-sprint-play-again">` to HTML or remove the JS references.

### BUG-03: `style.css` is dead code — 4,754 lines never loaded
- **File:** `index.html` (missing `<link>`), `style.css`
- **Evidence:** `index.html` loads only `pixel.css` (line 18). No `<link href="style.css">` exists. `style.css` is 4,754 lines / 105KB of completely unused CSS.
- **Impact:** 105KB of dead code in repo. Maintenance burden — any fix applied to `style.css` has zero effect. Confusing for developers.
- **Fix:** Either load `style.css` as fallback (not recommended given conflicts) or archive/delete it.

### BUG-04: Conflicting CSS variables between pixel.css and style.css
- **File:** `pixel.css:25-55`, `style.css:1-18`
- **Evidence:** 6 variables defined in BOTH files with different values:
  - `--font-mono`: pixel=`var(--f-tech)` vs style=`'JetBrains Mono', ...`
  - `--glass-border`: pixel=`var(--border-dim)` vs style=`rgba(255,255,255,0.1)`
  - `--page-max`: pixel=`1440px` vs style=`1400px`
  - `--success-green`: pixel=`var(--neon-green)` vs style=`#22c55e`
  - `--text-main`: pixel=`#f0f6fc` vs style=`#e2e8f0`
  - `--text-muted`: pixel=`var(--text-dim)` vs style=`#94a3b8`
- **Impact:** If `style.css` were ever loaded, it would override pixel.css variables causing visual inconsistency. Currently no runtime impact since style.css is not loaded, but the divergence is a maintenance trap.
- **Fix:** Consolidate variables into a single source of truth.

### BUG-05: Duplicate `@keyframes spin` and `pulseHint` definitions
- **File:** `pixel.css:540-541`, `style.css:409, 453`
- **Evidence:** Both files define `@keyframes spin` and `@keyframes pulseHint` with different values. `pulseHint` uses different colors (pixel: `rgba(255,204,0,...)` vs style: `rgba(253,224,71,...)`).
- **Impact:** Currently only pixel.css keyframes are active (style.css not loaded). But if both were loaded, the second definition wins — unpredictable animation behavior.
- **Fix:** Remove duplicates from style.css or unify.

### BUG-06: `.hidden` class defined 2× in pixel.css and 8× in style.css
- **File:** `pixel.css:339, 511`, `style.css:398, 721, 2405, 2551, 2965, 3072, 3299, 3576`
- **Evidence:** 10 total definitions of `.hidden`. In style.css line 3299, `.hidden` uses `transform: translateY(-100%)` instead of `display: none` — a different hiding mechanism.
- **Impact:** Only pixel.css definitions are active. But the inconsistency means if style.css were loaded, some `.hidden` elements would use transform instead of display:none, breaking visibility logic.
- **Fix:** Single `.hidden { display: none; }` definition.

### BUG-07: `.grid-overlay` defined in both CSS files with different properties
- **File:** `pixel.css:328`, `style.css:384`
- **Evidence:** pixel.css sets `background: rgba(14,17,23,0.94)` and `z-index: 20`. style.css adds `border-radius: 12px`, `backdrop-filter: blur(4px)`, and `padding: 20px`.
- **Impact:** Only pixel.css version is active. The style.css version has rounded corners and blur that would look different.
- **Fix:** Merge into single definition.

### BUG-08: `.word-grid` and `.cell` defined in both CSS files with conflicting sizing
- **File:** `pixel.css:267-287`, `style.css:422-454`
- **Evidence:** pixel.css uses `width: 100%; height: 100%; gap: 3px` with `font-size: clamp(14px, 3.2vh, 30px)`. style.css uses CSS variables `--cell-size: 20px; --grid-gap: 2px` with `font-size: clamp(9px, calc(var(--cell-size) * 0.48), 18px)`.
- **Impact:** pixel.css version is active. Cells are larger (14-30px vs 9-18px). If style.css were loaded, cells would shrink dramatically.
- **Fix:** Unify cell sizing approach.

### BUG-09: `.cross-line` SVG stroke defined differently in both CSS files
- **File:** `pixel.css:320`, `style.css:420`
- **Evidence:** pixel.css: `stroke: var(--neon-green); stroke-width: clamp(8px, 1.8vh, 18px); opacity: 0.45`. style.css: `stroke: var(--success-green); stroke-width: 18; opacity: 0.35`.
- **Impact:** Different line colors (neon-green vs success-green), widths (responsive clamp vs fixed 18), and opacity (0.45 vs 0.35).
- **Fix:** Single definition.

### BUG-10: Compatibility aliases div — 19 hidden elements polluting DOM
- **File:** `index.html:531-561`
- **Evidence:** `<div hidden aria-hidden="true" class="compatibility-aliases">` contains 19 elements with IDs that game.js references but don't exist in the visible layout: `word-bank-list`, `ui-network-progress`, `ui-hardware`, `btn-buy-lightning`, `tutorial-modal`, `tutorial-form`, `pools-list`, `network-select`, `network-status`, `ui-active-network`, `ui-node-status`, `btn-change-network`, `pool-tag-input`, `btn-achievements`, `btn-cards`, `btn-chat-toggle`, `btn-close-crate`, `btn-friends`, `btn-season`, `btn-skills`.
- **Impact:** These elements exist in DOM but are hidden. `getElementById()` finds them, so JS doesn't crash. But they're invisible placeholders — if JS tries to manipulate their visibility or content, nothing shows. `btn-buy-lightning` is a `<button>` that's hidden — click handlers fire but button is invisible.
- **Fix:** Either wire these to visible UI elements or remove both the aliases and the JS references.

### BUG-11: `DOMContentLoaded` handler registered twice
- **File:** `game.js:2608, 6345`
- **Evidence:** Two `addEventListener('DOMContentLoaded', ...)` calls.
- **Impact:** Both handlers run. If they do overlapping work (e.g., initialization), it runs twice.
- **Fix:** Consolidate into single handler.

### BUG-12: Only 2 breakpoints — no tablet/medium range
- **File:** `pixel.css:544, 2010`
- **Evidence:** Breakpoints at `max-width: 900px` (mobile) and `max-width: 559px` (small mobile). No breakpoint for tablets (768px), medium desktop (1200px), or landscape orientations.
- **Impact:** Devices between 560px and 900px (tablets in portrait) use the desktop layout which may overflow or be too cramped. The 900px breakpoint collapses the sidebar below the grid, but tablets in landscape (1024px) still get the side-by-side layout which may be too wide.
- **Fix:** Add breakpoints at 768px (tablet) and 1200px (large desktop).

### BUG-13: `body` has conflicting layout models between CSS files
- **File:** `pixel.css:76-92`, `style.css:41-63`
- **Evidence:** pixel.css: `height: 100vh; height: 100dvh; overflow: hidden; display: flex; justify-content: center; align-items: center`. style.css: `min-height: 100vh; overflow-y: auto; flex-direction: column; padding-bottom: calc(76px + ...)`.
- **Impact:** pixel.css version is active. `overflow: hidden` on body means the page cannot scroll — if content overflows (e.g., many tabs open), it's clipped. style.css has `overflow-y: auto` which would allow scrolling.
- **Fix:** Consider `overflow-y: auto` on body or `.mecha-frame` for scrollable content.

### BUG-14: `100vh` + `100dvh` dual declaration on body
- **File:** `pixel.css:80-81`
- **Evidence:** `height: 100vh` followed by `height: 100dvh`. Both are set; dvh overrides vh in supporting browsers.
- **Impact:** Correct fallback pattern, but `height: 100dvh` on a flex container with `overflow: hidden` can cause issues on mobile browsers with dynamic toolbars (Safari iOS) — the viewport height changes as address bar shows/hides, but `overflow: hidden` prevents adjustment.
- **Fix:** Use `min-height: 100dvh` instead of `height: 100dvh` to allow growth.

### BUG-15: z-index stacking context conflicts between CSS files
- **File:** `pixel.css`, `style.css`
- **Evidence:** pixel.css z-index values: 1, 4, 5, 10, 20, 25, 300, 500, 1000, 1100, 1400, 9999. style.css z-index values: 1, 5, 7, 10, 20, 25, 50, 155, 160, 170, 180, 200, 250, 300, 1000, 1100, 1200, 1400, 1500, 1600.
- **Impact:** pixel.css uses z-index 9999 for `body::after` (scanlines). style.css uses up to 1600. If both were loaded, the scanlines overlay (9999) would be above everything. Currently only pixel.css is active.
- **Fix:** Document z-index scale. Consider CSS custom properties for z-index layers.

### BUG-16: `user-select: none` on all elements via `*` selector
- **File:** `pixel.css:74`
- **Evidence:** `* { user-select: none; ... }` applied globally.
- **Impact:** Users cannot select text anywhere on the page — including instructions, error messages, and the miner name input. This is a poor UX for an educational game where users may want to copy information.
- **Fix:** Apply `user-select: none` only to interactive game elements (grid cells, buttons), not globally.

### BUG-17: `maximum-scale=1.0, user-scalable=no` in viewport meta
- **File:** `index.html:5`
- **Evidence:** `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">`
- **Impact:** Disables pinch-to-zoom entirely. This violates WCAG 2.1 success criterion 1.4.10 (Reflow) and 1.6.1 (Amplification of Zoom). Users with visual impairments cannot zoom to read content.
- **Fix:** Remove `maximum-scale=1.0, user-scalable=no`.

### BUG-18: Theme direction mismatch — dark vs light/beige
- **File:** `index.html:7-8`, `pixel.css:27-34`
- **Evidence:** Task direction specifies light/beige theme (`#f0deaf`, `#e2c992`, `#faedd0`). Current implementation uses dark theme: `--bg-void: #0e1117`, `color-scheme: dark`, `theme-color: #0e1117`.
- **Impact:** The entire visual identity is opposite to the intended direction. Every color variable, background, and text color is dark-themed.
- **Fix:** This is a strategic decision, not a bug per se, but it's a **major divergence** from the stated design direction.

### BUG-19: 4 CSS classes used in JS but not defined in any CSS
- **File:** `game.js`
- **Evidence:** `skill-branch-desc`, `skill-branch-title`, `skill-node-effect`, `skill-node-info` are added via `classList.add()` in game.js but never defined in `pixel.css` or `style.css`.
- **Impact:** Elements with these classes have no styling — they render with default browser styles, breaking visual consistency in the skills tree panel.
- **Fix:** Add CSS definitions for these 4 classes in pixel.css.

### BUG-20: 63 fixed px dimensions in pixel.css — potential overflow on small screens
- **File:** `pixel.css`
- **Evidence:** 63 declarations use fixed pixel values for width/height. Key offenders: `.hud-header { height: 54px }`, `.hud-footer { height: 38px }`, `.mecha-btn { height: 44px }`, `.race-chute { height: 8px }`, `.grid-hull { padding: 6px }`.
- **Impact:** Fixed heights on header/footer/sidebar buttons don't adapt to content growth. If text wraps or font sizes increase (accessibility), content overflows.
- **Fix:** Use `min-height` instead of `height` where content may grow. Use `clamp()` for responsive sizing.

---

## CSS Dead Code Summary

| Source | Lines | Classes | In HTML? | Status |
|--------|-------|---------|----------|--------|
| `style.css` | 4,754 | ~400 | No (file not loaded) | **DEAD** |
| `pixel.css` aliases | ~1,500 | 389 | Partially | Active but bloated |
| `pixel.css` core | ~550 | ~80 | Yes | Active |

**154 classes** defined in `style.css` are never referenced in `index.html` or `pixel.css`. These include: `achievement-card`, `achievement-icon`, `block-card`, `boss-defeat-content`, `boss-loot-text`, `boss-points`, and 149 more.

---

## Service Worker Analysis

- **Cache version:** v5
- **Cached assets:** `./`, `./pixel.css`, `./game.js`, `manifest.webmanifest`, 3 fonts, 2 icons
- **Not cached:** `style.css` (correct — it's not loaded)
- **Strategy:** Cache-first for shell assets, network-only for API/WS
- **Update flow:** SKIP_WAITING message → reload. Correct pattern.
- **No issues found.**

---

## Dockerfile

- `frontend/Dockerfile`, `backend/Dockerfile`, `docs/Dockerfile` exist.
- Root `Dockerfile` does not exist (not in scope for this audit).

---

## Recommendations (Priority Order)

1. **CRITICAL:** Fix duplicate `showTab()` — tab navigation is broken (BUG-01)
2. **CRITICAL:** Add `btn-sprint-play-again` to HTML or remove JS references (BUG-02)
3. **HIGH:** Remove or archive `style.css` — it's 105KB of dead code (BUG-03)
4. **HIGH:** Add missing CSS for 4 skill-tree classes (BUG-19)
5. **HIGH:** Remove `user-scalable=no` from viewport meta for accessibility (BUG-17)
6. **MEDIUM:** Add tablet breakpoint at 768px (BUG-12)
7. **MEDIUM:** Consolidate compatibility aliases into proper UI elements (BUG-10)
8. **MEDIUM:** Change `user-select: none` from global `*` to targeted elements (BUG-16)
9. **LOW:** Consolidate duplicate `@keyframes` definitions (BUG-05)
10. **LOW:** Document z-index scale with CSS custom properties (BUG-15)
11. **STRATEGIC:** Align theme with light/beige direction or update task spec (BUG-18)

---

## Files Analyzed

| File | Lines | Size | Status |
|------|-------|------|--------|
| `frontend/index.html` | 565 | 30KB | Active, valid HTML5 |
| `frontend/pixel.css` | 2,086 | 61KB | Active, loaded |
| `frontend/style.css` | 4,754 | 106KB | **NOT LOADED** — dead code |
| `frontend/game.js` | 6,345 | 229KB | Active, loaded |
| `frontend/service-worker.js` | 84 | 2.4KB | Active, registered |
