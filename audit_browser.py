#!/usr/bin/env python3
"""Auditoria UI completa do Mempool Miner via Playwright."""
import subprocess, os, sys, json, time

# Ensure Playwright's browser path
playwright_bin = os.path.expanduser("~/.cache/ms-playwright/chromium-1234/chrome-linux/chrome")
if not os.path.exists(playwright_bin):
    playwright_bin = os.path.expanduser("~/.cache/ms-playwright/chromium-1187/chrome-linux/chrome")
print(f"Chrome binary: {playwright_bin}", file=sys.stderr)
print(f"Exists: {os.path.exists(playwright_bin)}", file=sys.stderr)

# Use npx playwright to run a Python script
script = '''
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
        )
        
        results = {}
        
        # === 1. DESKTOP 1920x1080 ===
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto('http://localhost:8010', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/desktop-full.png', full_page=False)
        print("SCREENSHOT: desktop-full.png", flush=True)
        
        # Get page info
        title = await page.title()
        print(f"TITLE: {title}", flush=True)
        
        # Scroll and screenshot sections
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.25)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/desktop-scroll1.png', full_page=False)
        print("SCREENSHOT: desktop-scroll1.png", flush=True)
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/desktop-scroll2.png', full_page=False)
        print("SCREENSHOT: desktop-scroll2.png", flush=True)
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.75)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/desktop-scroll3.png', full_page=False)
        print("SCREENSHOT: desktop-scroll3.png", flush=True)
        
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/desktop-bottom.png', full_page=False)
        print("SCREENSHOT: desktop-bottom.png", flush=True)
        
        # Extract DOM structure for analysis
        dom_info = await page.evaluate('''() => {
            const elements = document.querySelectorAll('*');
            const info = {
                total_elements: elements.length,
                headings: [],
                buttons: [],
                nav_items: [],
                sections: [],
                images: [],
                inputs: [],
                classes: {},
                overflow_elements: [],
                empty_elements: [],
                fixed_positioned: [],
                z_index_high: []
            };
            
            elements.forEach(el => {
                const tag = el.tagName.toLowerCase();
                const cls = el.className || '';
                const id = el.id || '';
                const text = (el.textContent || '').trim().substring(0, 100);
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                
                if (tag === 'h1' || tag === 'h2' || tag === 'h3' || tag === 'h4') {
                    info.headings.push({tag, text: text.substring(0, 80), id, cls: String(cls).substring(0, 100)});
                }
                if (tag === 'button' || el.getAttribute('role') === 'button') {
                    info.buttons.push({text: text.substring(0, 80), id, cls: String(cls).substring(0, 100)});
                }
                if (tag === 'nav' || (cls.includes('nav') && tag === 'div')) {
                    info.nav_items.push({text: text.substring(0, 80), id, cls: String(cls).substring(0, 100)});
                }
                if (tag === 'section' || tag === 'main' || tag === 'footer' || tag === 'header') {
                    info.sections.push({tag, text: text.substring(0, 80), id, cls: String(cls).substring(0, 100)});
                }
                if (tag === 'img') {
                    info.images.push({src: (el.src || '').substring(0, 100), alt: el.alt || '', id, cls: String(cls).substring(0, 100)});
                }
                if (tag === 'input' || tag === 'select' || tag === 'textarea') {
                    info.inputs.push({type: el.type || 'text', name: el.name || '', placeholder: el.placeholder || '', id, cls: String(cls).substring(0, 100)});
                }
                
                // Check for overflow
                if (style.overflow !== 'visible' && style.overflow !== 'auto') {
                    if (rect.width < 50 || rect.height < 50) {
                        info.overflow_elements.push({tag, text: text.substring(0, 50), width: Math.round(rect.width), height: Math.round(rect.height), overflow: style.overflow});
                    }
                }
                
                // Check for empty elements with significant size
                if (text.length === 0 && !el.querySelector('img') && rect.width > 50 && rect.height > 50) {
                    info.empty_elements.push({tag, id, cls: String(cls).substring(0, 100), width: Math.round(rect.width), height: Math.round(rect.height)});
                }
                
                // Fixed/sticky elements
                if (style.position === 'fixed' || style.position === 'sticky') {
                    info.fixed_positioned.push({tag, position: style.position, text: text.substring(0, 50)});
                }
                
                // High z-index
                const zIndex = parseInt(style.zIndex);
                if (zIndex > 100) {
                    info.z_index_high.push({tag, zIndex, text: text.substring(0, 50)});
                }
                
                // Track classes
                const classList = el.classList;
                for (let c of classList) {
                    info.classes[c] = (info.classes[c] || 0) + 1;
                }
            });
            
            return info;
        }''')
        
        results['desktop_dom'] = dom_info
        
        # Check for specific mechanics sections
        mechanics_check = await page.evaluate('''() => {
            const mechanics = ['Block Card', 'Season Pass', 'PvP', 'Sprint', 'Friend', 'Staking', 'Skill Tree', 'Crate', 'Boss Block', 'Mercado'];
            const results = {};
            const bodyText = document.body.innerText.toLowerCase();
            
            mechanics.forEach(m => {
                const lower = m.toLowerCase();
                results[m] = {
                    found_in_body: bodyText.includes(lower),
                    count: (bodyText.match(new RegExp(lower, 'g')) || []).length
                };
            });
            
            // Check for navigation items
            const navText = document.body.innerText;
            results['nav_items'] = navText.split('\\n').filter(l => l.trim().length > 0 && l.trim().length < 50).slice(0, 50);
            
            return results;
        }''')
        
        results['mechanics'] = mechanics_check
        
        # Check CSS properties for common issues
        css_issues = await page.evaluate('''() => {
            const issues = {
                negative_margins: [],
                huge_elements: [],
                tiny_elements: [],
                transparent_elements: [],
                overlapping_elements: [],
                text_overflow: []
            };
            
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                // Negative margins
                const marginTop = parseFloat(style.marginTop);
                const marginLeft = parseFloat(style.marginLeft);
                if (marginTop < -10 || marginLeft < -10) {
                    issues.negative_margins.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), marginTop, marginLeft});
                }
                
                // Huge elements
                if (rect.width > 1800 || rect.height > 1000) {
                    issues.huge_elements.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), width: Math.round(rect.width), height: Math.round(rect.height)});
                }
                
                // Tiny elements
                if (rect.width > 0 && rect.width < 20 && rect.height > 0 && rect.height < 20) {
                    issues.tiny_elements.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), width: Math.round(rect.width), height: Math.round(rect.height)});
                }
                
                // Very transparent
                const opacity = parseFloat(style.opacity);
                if (opacity > 0 && opacity < 0.15) {
                    issues.transparent_elements.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), opacity});
                }
                
                // Text overflow
                if (style.overflow === 'hidden' && el.scrollWidth > el.clientWidth) {
                    issues.text_overflow.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth});
                }
            });
            
            return issues;
        }''')
        
        results['css_issues'] = css_issues
        
        # Check for broken images
        broken_images = await page.evaluate('''() => {
            const images = document.querySelectorAll('img');
            return Array.from(images).map(img => ({
                src: img.src,
                alt: img.alt,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                complete: img.complete,
                error: img.naturalWidth === 0
            }));
        }''')
        
        results['broken_images'] = broken_images
        
        # Check for 404 resources
        console_errors = await page.evaluate('''() => {
            return [];
        }''')
        
        await page.close()
        
        # === 2. TABLET 768x1024 ===
        page = await browser.new_page(viewport={'width': 768, 'height': 1024})
        await page.goto('http://localhost:8010', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/tablet-full.png', full_page=False)
        print("SCREENSHOT: tablet-full.png", flush=True)
        
        # Scroll tablet
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/tablet-scroll.png', full_page=False)
        print("SCREENSHOT: tablet-scroll.png", flush=True)
        
        # Check layout issues on tablet
        tablet_issues = await page.evaluate('''() => {
            const issues = {
                overflow_x: [],
                tiny_text: [],
                cut_elements: []
            };
            
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                if (style.overflowX === 'auto' || style.overflowX === 'scroll') {
                    issues.overflow_x.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), width: Math.round(rect.width)});
                }
                
                const fontSize = parseFloat(style.fontSize);
                if (fontSize > 0 && fontSize < 8) {
                    issues.tiny_text.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), fontSize});
                }
            });
            
            // Check if any element is cut off
            const bodyRect = document.body.getBoundingClientRect();
            issues.body_height = Math.round(bodyRect.height);
            issues.viewport_height = window.innerHeight;
            
            return issues;
        }''')
        
        results['tablet_issues'] = tablet_issues
        
        await page.close()
        
        # === 3. MOBILE 375x667 ===
        page = await browser.new_page(viewport={'width': 375, 'height': 667})
        await page.goto('http://localhost:8010', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/mobile-full.png', full_page=False)
        print("SCREENSHOT: mobile-full.png", flush=True)
        
        # Scroll mobile
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight * 0.5)')
        await asyncio.sleep(1)
        await page.screenshot(path='/home/developer/mempool.miner/screenshots/mobile-scroll.png', full_page=False)
        print("SCREENSHOT: mobile-scroll.png", flush=True)
        
        # Check layout issues on mobile
        mobile_issues = await page.evaluate('''() => {
            const issues = {
                overflow_x: [],
                tiny_text: [],
                cut_elements: [],
                tap_targets: []
            };
            
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                
                if (style.overflowX === 'auto' || style.overflowX === 'scroll') {
                    issues.overflow_x.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), width: Math.round(rect.width)});
                }
                
                const fontSize = parseFloat(style.fontSize);
                if (fontSize > 0 && fontSize < 10) {
                    issues.tiny_text.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), fontSize});
                }
                
                // Check tap target size (should be at least 44x44)
                if (el.tagName === 'BUTTON' || el.tagName === 'A' || el.getAttribute('role') === 'button') {
                    if (rect.width < 44 || rect.height < 44) {
                        issues.tap_targets.push({tag: el.tagName, text: (el.textContent||'').substring(0,50), width: Math.round(rect.width), height: Math.round(rect.height)});
                    }
                }
            });
            
            const bodyRect = document.body.getBoundingClientRect();
            issues.body_height = Math.round(bodyRect.height);
            issues.viewport_height = window.innerHeight;
            
            return issues;
        }''')
        
        results['mobile_issues'] = mobile_issues
        
        await page.close()
        
        # === 4. INTERACTIVITY TESTS ===
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        await page.goto('http://localhost:8010', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)
        
        # Try clicking buttons and checking for errors
        interactivity = await page.evaluate('''() => {
            const results = {
                buttons_found: 0,
                buttons_clicked: 0,
                errors: [],
                console_messages: []
            };
            
            const buttons = document.querySelectorAll('button, [role="button"], a');
            results.buttons_found = buttons.length;
            
            // Try clicking first few buttons
            buttons.forEach((btn, i) => {
                if (i < 10) {
                    try {
                        btn.click();
                        results.buttons_clicked++;
                    } catch(e) {
                        results.errors.push({button: i, text: (btn.textContent||'').substring(0,50), error: e.message});
                    }
                }
            });
            
            return results;
        }''')
        
        results['interactivity'] = interactivity
        
        # Get all visible text for analysis
        full_text = await page.evaluate('() => document.body.innerText')
        results['full_text_sample'] = full_text[:5000]
        
        # Get CSS classes used
        css_classes = await page.evaluate('''() => {
            const all = document.querySelectorAll('*');
            const classes = new Set();
            all.forEach(el => {
                for (let c of el.classList) {
                    classes.add(c);
                }
            });
            return Array.from(classes).sort();
        }''')
        results['css_classes'] = css_classes
        
        # Get all unique text patterns for mechanics
        mechanics_text = await page.evaluate('''() => {
            const text = document.body.innerText;
            const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
            return lines.slice(0, 200);
        }''')
        results['text_lines'] = mechanics_text
        
        await page.close()
        
        # Save results
        with open('/home/developer/mempool.miner/screenshots/dom_analysis.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print("DOM analysis saved to dom_analysis.json", flush=True)
        
        await browser.close()
        print("AUDIT_COMPLETE", flush=True)

asyncio.run(main())
'''

result = subprocess.run(
    ['npx', 'playwright', 'test', '--config', '/dev/null'],
    input=script,
    capture_output=True,
    text=True,
    timeout=180
)

# Actually, let's use a simpler approach - write the script and run it with node
print("Trying direct approach...", file=sys.stderr)
'''
