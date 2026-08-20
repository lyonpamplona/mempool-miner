"""Mempool Miner Visual Audit - Automated screenshot capture"""
import asyncio
import os
import json
from pathlib import Path

OUTPUT_DIR = Path("/home/developer/mempool.miner/audit-screenshots")
OUTPUT_DIR.mkdir(exist_ok=True)

CHROME_PATH = "/home/developer/.cache/ms-playwright/chromium-1187/chrome-linux/chrome"
LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
]

async def main():
    from playwright.async_api import async_playwright
    
    screenshots = []
    issues = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=CHROME_PATH,
            headless=True,
            args=LAUNCH_ARGS
        )
        
        # Desktop context
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            color_scheme="dark"
        )
        page = await context.new_page()
        
        try:
            await page.goto("http://localhost:8010", wait_until="networkidle", timeout=15000)
        except Exception as e:
            print(f"Navigation error: {e}")
            await page.goto("http://localhost:8010", wait_until="domcontentloaded", timeout=10000)
        
        await page.wait_for_timeout(2000)
        
        # 1. Initial screen
        await page.screenshot(path=str(OUTPUT_DIR / "01_initial_screen.png"), full_page=True)
        title = await page.title()
        print(f"Page title: {title}")
        print(f"URL: {page.url}")
        
        # Get page summary
        body_text = await page.inner_text("body") if await page.is_visible("body") else "body not visible"
        print(f"Body text length: {len(body_text)}")
        print(f"First 500 chars: {body_text[:500]}")
        
        screenshots.append(("01_initial_screen.png", "Tela inicial"))
        
        # 2. Check for login/nickname screen
        login_elements = await page.query_selector_all("input, [placeholder*='nick'], [placeholder*='name'], [placeholder*='user']")
        print(f"Input elements found: {len(login_elements)}")
        for el in login_elements:
            placeholder = await el.get_attribute("placeholder") or ""
            el_type = await el.get_attribute("type") or ""
            print(f"  Input: type={el_type}, placeholder={placeholder}")
        
        # 3. Take screenshot of main game area
        await page.screenshot(path=str(OUTPUT_DIR / "02_main_game.png"), full_page=True)
        screenshots.append(("02_main_game.png", "Tela de jogo principal"))
        
        # 4. Check for sidebar/leaderboard
        sidebar = await page.query_selector("[class*='sidebar'], [class*='leaderboard'], nav, aside")
        if sidebar:
            await page.screenshot(path=str(OUTPUT_DIR / "03_sidebar_leaderboard.png"), full_page=True)
            screenshots.append(("03_sidebar_leaderboard.png", "Sidebar com leaderboard"))
        
        # 5. Click through all navigation buttons/links
        nav_items = await page.query_selector_all("button, a, [role='button'], [role='tab'], [role='navigation'] a")
        print(f"\nNavigation elements: {len(nav_items)}")
        
        for i, item in enumerate(nav_items[:30]):  # First 30 interactive elements
            try:
                if await item.is_visible():
                    text = await item.inner_text()
                    aria_label = await item.get_attribute("aria-label") or ""
                    class_attr = await item.get_attribute("class") or ""
                    tag = await item.evaluate("el => el.tagName.toLowerCase()")
                    print(f"  [{i}] <{tag}> text='{text.strip()[:50]}' aria='{aria_label[:30]}' class='{class_attr[:50]}'")
            except:
                pass
        
        # 6. Click all buttons and take screenshots
        buttons = await page.query_selector_all("button, [role='button']")
        print(f"\nButtons: {len(buttons)}")
        
        btn_count = 0
        for btn in buttons:
            try:
                if await btn.is_visible():
                    text = (await btn.inner_text()).strip() or await btn.get_attribute("aria-label") or "icon"
                    print(f"  Clicking: '{text}'")
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    btn_count += 1
                    await page.screenshot(path=str(OUTPUT_DIR / f"04_btn_{btn_count:02d}_{text[:20].replace(' ','_')}.png"), full_page=True)
                    screenshots.append((f"04_btn_{btn_count:02d}_{text[:20].replace(' ','_')}.png", f"Botão: {text}"))
                    # Go back to main
                    await page.go_back()
                    await page.wait_for_timeout(1000)
            except Exception as e:
                print(f"  Error clicking '{text}': {e}")
        
        # 7. Check for modals/dialogs
        modals = await page.query_selector_all("[role='dialog'], [class*='modal'], [class*='overlay'], [class*='popup']")
        print(f"\nModals/dialogs: {len(modals)}")
        
        # 8. Check for tooltips
        tooltips = await page.query_selector_all("[data-tooltip], [title], [class*='tooltip']")
        print(f"Tooltip elements: {len(tooltips)}")
        
        # 9. Check for panels
        panels = await page.query_selector_all("[class*='panel'], [class*='card'], [class*='section']")
        print(f"Panel/card elements: {len(panels)}")
        
        # 10. Full page screenshot with all visible content
        await page.screenshot(path=str(OUTPUT_DIR / "05_full_page.png"), full_page=True)
        screenshots.append(("05_full_page.png", "Página completa"))
        
        # 11. Check CSS for visual issues
        css_issues = await page.evaluate("""() => {
            const issues = [];
            const allElements = document.querySelectorAll('*');
            
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Check for overflow
                if (el.scrollHeight > el.clientHeight && el.clientHeight > 0) {
                    issues.push({
                        type: 'overflow',
                        tag: el.tagName,
                        class: el.className.substring(0, 50),
                        text: el.textContent.substring(0, 50),
                        height: el.clientHeight,
                        scrollHeight: el.scrollHeight
                    });
                }
                
                // Check for zero-size elements that have content
                if (rect.width === 0 && rect.height === 0 && el.textContent.trim()) {
                    issues.push({
                        type: 'invisible',
                        tag: el.tagName,
                        class: el.className.substring(0, 50),
                        text: el.textContent.substring(0, 50)
                    });
                }
                
                // Check for text overflow
                if (style.textOverflow === 'ellipsis' || (style.overflow === 'hidden' && el.scrollWidth > el.clientWidth)) {
                    issues.push({
                        type: 'text_overflow',
                        tag: el.tagName,
                        class: el.className.substring(0, 50),
                        text: el.textContent.substring(0, 50)
                    });
                }
            });
            
            return issues.slice(0, 50);
        }}""")
        print(f"\nCSS issues found: {len(css_issues)}")
        for issue in css_issues[:20]:
            print(f"  {issue['type']}: <{issue['tag']}> class='{issue.get('class','')}' text='{issue.get('text','')}'")
        
        # 12. Check for console errors
        console_msgs = []
        page.on("console", lambda msg: console_msgs.append(msg.text) if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda err: console_msgs.append(f"PAGE ERROR: {err}"))
        
        # Reload to catch errors
        await page.reload(wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(3000)
        
        print(f"\nConsole errors/warnings: {len(console_msgs)}")
        for msg in console_msgs[:20]:
            print(f"  {msg[:100]}")
        
        # 13. Mobile viewport test
        mobile_context = await browser.new_context(
            viewport={"width": 375, "height": 812},
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
        )
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto("http://localhost:8010", wait_until="networkidle", timeout=15000)
        await mobile_page.wait_for_timeout(2000)
        await mobile_page.screenshot(path=str(OUTPUT_DIR / "06_mobile_viewport.png"), full_page=True)
        screenshots.append(("06_mobile_viewport.png", "Viewport mobile (375x812)"))
        
        # Check mobile layout issues
        mobile_issues = await mobile_page.evaluate("""() => {
            const issues = [];
            const allElements = document.querySelectorAll('*');
            const vw = window.innerWidth;
            
            allElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                
                // Elements wider than viewport
                if (rect.width > vw && el.children.length === 0) {
                    issues.push({
                        type: 'wider_than_viewport',
                        tag: el.tagName,
                        class: el.className.substring(0, 50),
                        width: rect.width,
                        viewport: vw
                    });
                }
                
                // Elements with horizontal overflow
                if (el.scrollWidth > el.clientWidth && el.clientWidth > 0) {
                    issues.push({
                        type: 'horizontal_overflow',
                        tag: el.tagName,
                        class: el.className.substring(0, 50),
                        scrollWidth: el.scrollWidth,
                        clientWidth: el.clientWidth
                    });
                }
            });
            
            return issues.slice(0, 30);
        }}""")
        print(f"\nMobile layout issues: {len(mobile_issues)}")
        for issue in mobile_issues[:15]:
            print(f"  {issue['type']}: <{issue['tag']}> class='{issue.get('class','')}'")
        
        # 14. Get page structure
        structure = await page.evaluate("""() => {
            const sections = [];
            const allElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, section, article, nav, main, aside, header, footer');
            allElements.forEach(el => {
                sections.push({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.substring(0, 80).trim(),
                    class: el.className.substring(0, 50)
                });
            });
            return sections;
        }}""")
        print(f"\nPage structure ({len(structure)} sections):")
        for s in structure[:30]:
            print(f"  <{s['tag']}> '{s['text']}' class='{s['class']}'")
        
        # 15. Get all interactive elements with their states
        interactive = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="tab"], [role="menuitem"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                items.push({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.substring(0, 50).trim() || el.getAttribute('aria-label') || '',
                    visible: rect.width > 0 && rect.height > 0,
                    width: rect.width,
                    height: rect.height,
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    pointer_events: style.pointerEvents,
                    class: el.className.substring(0, 50)
                });
            });
            return items;
        }}""")
        print(f"\nInteractive elements: {len(interactive)}")
        hidden = [i for i in interactive if not i['visible'] or i['display'] == 'none' or i['visibility'] == 'hidden']
        print(f"  Hidden/invisible: {len(hidden)}")
        no_pointer = [i for i in interactive if i['pointer_events'] == 'none' and i['visible']]
        print(f"  No pointer events: {len(no_pointer)}")
        for item in hidden[:10]:
            print(f"    Hidden: <{item['tag']}> '{item['text']}' display={item['display']} visibility={item['visibility']}")
        
        # 16. Save all findings as JSON
        findings = {
            "screenshots": screenshots,
            "css_issues": css_issues,
            "mobile_issues": mobile_issues,
            "console_errors": console_msgs[:30],
            "page_structure": structure[:30],
            "interactive_elements": {
                "total": len(interactive),
                "hidden": len(hidden),
                "no_pointer": len(no_pointer),
                "hidden_details": hidden[:10],
                "no_pointer_details": no_pointer[:10]
            },
            "title": title,
            "url": page.url
        }
        
        with open(OUTPUT_DIR / "findings.json", "w") as f:
            json.dump(findings, f, indent=2, default=str)
        
        print(f"\nFindings saved to {OUTPUT_DIR / 'findings.json'}")
        
        await browser.close()
    
    print(f"\nAudit complete. Screenshots saved to {OUTPUT_DIR}")

asyncio.run(main())
