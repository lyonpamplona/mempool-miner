# Game UI Organization Patterns for Mempool Miner

> Research on how to organize many game features without overwhelming players, with patterns applicable to Mempool Miner.

---

## Executive Summary

Mempool Miner is a complex game with many mechanics (mining, upgrades, stats, resources, etc.). This research identified **14 proven UI patterns** from game design literature, strategy games, and UX research that can help organize these features cleanly. The core principle across all sources: **show the minimum relevant info, hide the rest one click away**.

---

## Patterns Found

### Pattern 1: Progressive Disclosure
**What it is:** Reveal information and features gradually, showing only what matters at the current moment. Advanced options are hidden behind toggles, expandable panels, or separate screens.

**How it applies to Mempool Miner:**
- Start with a clean dashboard showing only: current hash rate, balance, active mining status, and next upgrade
- Hide advanced stats (difficulty history, detailed block info, transaction fees) behind expandable panels or a "Details" button
- Unlock UI complexity as the player progresses — early game shows basics, late game reveals advanced analytics

**References:**
- [UXPin: Progressive Disclosure](https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/)
- [Indieklem: Progressive Disclosure in Menus](https://indieklem.substack.com/p/9-creating-an-intuitive-in-game-menu)

---

### Pattern 2: Information Hierarchy (Visual Weight)
**What it is:** Use size, color, contrast, and position to signal importance. The most critical information should be readable at a glance; secondary details require deliberate attention.

**How it applies to Mempool Miner:**
- **Tier 1 (always visible, large):** Balance, hash rate, mining status
- **Tier 2 (visible, medium):** Active upgrades, current block progress
- **Tier 3 (on-demand, small):** Detailed stats, historical data, tooltips
- Use the 60-30-10 color rule: 60% background, 30% primary UI, 10% accent for alerts/important actions

**References:**
- [Game Developer: Balancing Information & Expressiveness](https://www.gamedeveloper.com/design/-ux-design-balancing-information-and-its-expressiveness---analysis-of-ui-information-presentation-of-games)
- [Kyle Kukshtel: Game UI Principles](https://kylekukshtel.com/game-ui-principles)

---

### Pattern 3: Tabbed Organization
**What it is:** Mutually exclusive content organized into labeled tabs. Each tab shows one category at a time, keeping the screen clean while providing access to many features.

**How it applies to Mempool Miner:**
- Top-level tabs: `Mine` | `Upgrades` | `Stats` | `Settings`
- Within `Upgrades`: sub-tabs for `Hardware` | `Software` | `Network`
- Limit to 4-6 tabs max at any level (Miller's Law: 7±2 items)
- Use icons + labels for each tab for quick recognition

**References:**
- [Hedberg Games: Creating UI Tabs in Unity](https://www.hedberggames.com/blog/creating-ui-tabs-in-unity-part-1)
- [UXPin: Tabs for Progressive Disclosure](https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/)

---

### Pattern 4: Centralized Status Bar / Info Pane
**What it is:** A dedicated area (usually bottom or side) that shows contextual information about the currently selected item or the overall game state.

**How it applies to Mempool Miner:**
- Bottom bar: always-visible summary (balance, hash rate, block progress bar)
- Side panel: contextual details when clicking on an upgrade or stat
- This pattern comes from RTS games (Age of Empires, Rise of Nations) where the bottom pane unified all commands and info

**References:**
- [Game Developer: UI Strategy Game Design Dos and Don'ts](https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts)

---

### Pattern 5: Group Related Items (Chunking)
**What it is:** Group related menu items and features together to create clear structure and reduce scanning time. Fewer than 6-7 items per group.

**How it applies to Mempool Miner:**
- Group upgrades by category: GPU upgrades, CPU upgrades, cooling, network
- Group stats: mining stats, financial stats, efficiency stats
- Group settings: game settings, display settings, audio settings
- Each group has a clear visual container (panel, card, section)

**References:**
- [Indieklem: Group Similar Items](https://indieklem.substack.com/p/9-creating-an-intuitive-in-game-menu)
- [Information Architecture in Game Design (UCF Paper)](https://cornet-tarantula-sl2c.squarespace.com/s/InformationArchitecture_GameDesign.pdf)

---

### Pattern 6: Dual Encoding (Show Info Twice)
**What it is:** Encode the same information using two visual dimensions (e.g., number + color, bar + value). This makes data instantly scannable while still precise.

**How it applies to Mempool Miner:**
- Hash rate: show number (45 TH/s) + color-coded bar (green = good, red = below target)
- Balance: show number + trend arrow (↑ green, ↓ red)
- Upgrade progress: show percentage + animated progress bar
- This reduces cognitive load — players can scan colors first, then drill into numbers

**References:**
- [Kyle Kukshtel: Encode All Information Twice](https://kylekukshtel.com/game-ui-principles)
- [Accessible Game Design: HUD Guidelines](https://accessiblegamedesign.com/guidelines/HUD.html)

---

### Pattern 7: Icons Over Text (Symbol-First Design)
**What it is:** Use symbols and icons wherever possible instead of text labels. Icons are faster to scan, work across languages, and save screen space.

**How it applies to Mempool Miner:**
- Mining icon for active mining, pause icon for paused
- Lightning bolt for energy/power upgrades
- Arrow up for hash rate increases
- Dollar sign for financial stats
- Keep a consistent icon style (pixel art or flat) and use tooltips for clarity

**References:**
- [Kyle Kukshtel: Favor Symbols Over Text](https://kylekukshtel.com/game-ui-principles)
- [Indieklem: Use Icons and Visual Cues](https://indieklem.substack.com/p/9-creating-an-intuitive-in-game-menu)

---

### Pattern 8: "Blow It Up" — Size Matches Importance
**What it is:** If information is truly important, it should be large and prominent. Don't bury critical data in small corners of the screen.

**How it applies to Mempool Miner:**
- Balance and hash rate should be the largest numbers on screen
- Mining start/stop button should be prominent and easy to find
- Upgrade purchase buttons should be clearly clickable
- Avoid cramming 10 stats into a tiny panel — if they're important, give them space

**References:**
- [Kyle Kukshtel: "Blow It Up"](https://kylekukshtel.com/game-ui-principles)
- [Zach Gage: Designing for Subway Legibility](http://stfj.net/DesigningForSubwayLegibility/)

---

### Pattern 9: Consistent Color Language
**What it is:** Use a limited color palette (8-10 colors) where each color has a consistent meaning across all UI panels.

**How it applies to Mempool Miner:**
- Green = positive/gain (earnings, upgrades available)
- Red = negative/alert (low balance, mining stopped)
- Blue = neutral/informational (stats, details)
- Yellow/Orange = warning (approaching limits, cooldowns)
- Gray = inactive/disabled (locked upgrades, unavailable features)
- Player learns the color language once and applies it everywhere

**References:**
- [Kyle Kukshtel: Consistent Color Scheme](https://kylekukshtel.com/game-ui-principles)
- [Game Developer: Use Color to Distinguish Information](https://www.gamedeveloper.com/design/-ux-design-balancing-information-and-its-expressiveness---analysis-of-ui-information-presentation-of-games)

---

### Pattern 10: Tooltips and Expandable Details
**What it is:** Keep the main UI clean by hiding detailed information behind hover tooltips or click-to-expand panels.

**How it applies to Mempool Miner:**
- Hover over an upgrade to see: cost, effect, current level, next level
- Click a stat to see: historical chart, breakdown, comparison
- This keeps the dashboard clean while making deep info accessible
- Procedurally generate tooltips from data attributes (not hardcoded strings)

**References:**
- [Kyle Kukshtel: Tooltips Are HUGE](https://kylekukshtel.com/game-ui-principles)
- [UXPin: Dialog Boxes, Popups, and Tooltips](https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/)

---

### Pattern 11: Signal-to-Noise Ratio
**What it is:** Maximize the ratio of useful information (signal) to decorative or redundant elements (noise). Every pixel should serve a purpose.

**How it applies to Mempool Miner:**
- Remove decorative elements that don't convey game state
- If a number doesn't change player decisions, consider hiding it
- Use whitespace and spacing to separate groups instead of heavy borders
- The pixel art aesthetic should enhance readability, not compete with it

**References:**
- [Information Architecture in Game Design: Principle of Disclosure](https://cornet-tarantula-sl2c.squarespace.com/s/InformationArchitecture_GameDesign.pdf)
- [Envy Labs: Interface Information Density](https://envylabs.com/insights/interface-information-density-best-practices)

---

### Pattern 12: Contextual UI (Show What's Relevant Now)
**What it is:** The UI adapts to show information relevant to the current context, rather than showing everything all the time.

**How it applies to Mempool Miner:**
- When mining is active: show block progress, current difficulty, earnings rate
- When mining is paused: show why (cooldown? no funds?) and how to resume
- When browsing upgrades: show which upgrades are available with current balance
- Notifications appear only when something needs attention (idle workers, new block found)

**References:**
- [Nicolas Kraj: Designing Efficient UIs For Games](https://medium.com/@nicolaskraj/designing-efficient-user-interfaces-for-games-be20b516f1c2)
- [Game Developer: Educational UIs](https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts)

---

### Pattern 13: Hotkeys and Keyboard Shortcuts
**What it is:** Power players learn keyboard shortcuts for frequent actions, reducing mouse clicks and speeding up gameplay.

**How it applies to Mempool Miner:**
- `Space` or `M`: Toggle mining on/off
- `1-9`: Quick-buy top upgrades
- `U`: Open upgrades panel
- `S`: Open stats panel
- Show hotkey hints in tooltips so players discover them naturally
- This is critical for idle/incremental games where players make many repetitive actions

**References:**
- [Game Developer: Balancing Visual and Non-Visual Commands](https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts)

---

### Pattern 14: Pixel Art UI Conventions
**What it is:** Pixel art games use specific UI conventions: pixel-perfect borders, limited color palettes, chunky readable fonts (not pixel fonts), and consistent visual language.

**How it applies to Mempool Miner:**
- Use SDF fonts (TextMeshPro) instead of pixel art fonts for readability
- Keep pixel art borders and panels consistent in thickness and style
- Use the same pixel art style for icons, buttons, and panels
- Reference games: Loop Hero, Celeste, Blasphemous for pixel art UI examples
- The UI should feel like part of the game world, not a modern web overlay

**References:**
- [Reddit: Great Examples of Pixel Art UI](https://www.reddit.com/r/gamedev/comments/12j4khb/what_do_you_guys_think_are_great_examples_of/)
- [Phaser PixUI: Open-Source UI Library for Pixel Art Games](https://phaser.io/news/2026/02/phaser-pixel-art-ui-library)
- [80 Level: Game UI History](https://80.lv/articles/a-look-into-games-ui-from-1960s-to-the-present)

---

## Recommended UI Layout for Mempool Miner

Based on the patterns above, here's a proposed layout:

```
┌─────────────────────────────────────────────────────┐
│  [Logo]  Balance: $1,234  │  Hash Rate: 45 TH/s    │  ← Top bar: Tier 1 stats
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌───────────────────────────────────────────┐    │
│   │                                           │    │
│   │          MINING VISUALIZATION             │    │  ← Center: game world / mining animation
│   │          (pixel art blocks, etc.)         │    │
│   │                                           │    │
│   │   [⏸ Pause]  [▶ Start]                    │    │  ← Contextual actions
│   │                                           │    │
│   └───────────────────────────────────────────┘    │
│                                                     │
├─────────────────────────────────────────────────────┤
│  [⛏ Mine] [⬆ Upgrades] [📊 Stats] [⚙ Settings]     │  ← Tab navigation (4 tabs, icons+labels)
├─────────────────────────────────────────────────────┤
│  Block Progress: ████████░░ 80%  │  Next: $50      │  ← Bottom status bar
│  Earnings: $12.5/s  │  Uptime: 2h 15m              │  ← Always-visible summary
└─────────────────────────────────────────────────────┘
```

**Tab Content Examples:**

- **Mine tab:** Mining visualization + start/pause + block progress
- **Upgrades tab:** Sub-tabs (Hardware/Software/Network) + upgrade cards with icons, cost, effect, buy button
- **Stats tab:** Expandable stat groups + historical charts + tooltips
- **Settings tab:** Basic settings visible + "Advanced" expandable section

---

## Key Takeaways

1. **Less is more on the main screen** — show only what the player needs right now
2. **Everything else is one click away** — tooltips, expandable panels, tabs
3. **Consistency is king** — same colors, same icons, same patterns everywhere
4. **Size signals importance** — big numbers for big decisions
5. **Dual encoding** — always pair numbers with visual indicators (bars, colors, icons)
6. **Progressive complexity** — the UI should grow with the player's experience
7. **Pixel art UI needs readable fonts** — use SDF fonts, not pixel fonts for text

---

## References

| Source | URL |
|--------|-----|
| Designing Efficient User Interfaces For Games (Nicolas Kraj, Ubisoft) | https://medium.com/@nicolaskraj/designing-efficient-user-interfaces-for-games-be20b516f1c2 |
| Some Game UI Principles (Kyle Kukshtel) | https://kylekukshtel.com/game-ui-principles |
| UI Strategy Game Design Dos and Don'ts (Josh Bycer) | https://www.gamedeveloper.com/design/ui-strategy-game-design-dos-and-don-ts |
| Creating an Intuitive In-Game Menu (Indieklem) | https://indieklem.substack.com/p/9-creating-an-intuitive-in-game-menu |
| Progressive Disclosure in UX (UXPin) | https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/ |
| Information Architecture in Game Design (UCF Paper) | https://cornet-tarantula-sl2c.squarespace.com/s/InformationArchitecture_GameDesign.pdf |
| Interface Information Density Best Practices (Envy Labs) | https://envylabs.com/insights/interface-information-density-best-practices |
| Balancing Information and Expressiveness in Game UI | https://www.gamedeveloper.com/design/-ux-design-balancing-information-and-its-expressiveness---analysis-of-ui-information-presentation-of-games |
| HUD Guidelines (Accessible Game Design) | https://accessiblegamedesign.com/guidelines/HUD.html |
| A Look Into Game UI: From 1960s to the Present (80 Level) | https://80.lv/articles/a-look-into-games-ui-from-1960s-to-the-present |
| Game UI Database (55,000+ UI screenshots) | https://www.gameuidatabase.com/ |
| Creating UI Tabs in Unity (Hedberg Games) | https://www.hedberggames.com/blog/creating-ui-tabs-in-unity-part-1 |
| Designing for Subway Legibility (Zach Gage) | http://stfj.net/DesigningForSubwayLegibility/ |
| Great Examples of Pixel Art UI (Reddit r/gamedev) | https://www.reddit.com/r/gamedev/comments/12j4khb/what_do_you_guys_think_are_great_examples_of/ |
| Phaser PixUI Library | https://phaser.io/news/2026/02/phaser-pixel-art-ui-library |

---

*Research compiled: August 18, 2026*
