const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = '/home/developer/mempool.miner/.hermes/reports/ui-audit/screenshots-agent-visual';
const BREAKPOINTS = [320, 768, 1024, 1440, 2560];
const FINDINGS = [];

function addFinding(severity, bp, element, expected, actual, selector, fileLine) {
  FINDINGS.push({ severity, bp, element, expected, actual, selector, fileLine });
}

(async () => {
  const browser = await chromium.launch({
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
  });

  for (const bp of BREAKPOINTS) {
    console.log(`\n=== AUDITING BREAKPOINT ${bp}px ===`);
    const context = await browser.newContext({ viewport: { width: bp, height: 900 } });
    const page = await context.newPage();
    await page.goto('http://localhost:8010/', { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1000);

    // Screenshot: initial auth modal
    await page.screenshot({ path: `${OUT}/bp${bp}_01_auth_modal.png`, fullPage: true });

    // Measure auth modal
    const authModal = page.locator('#auth-modal');
    const authModalVisible = await authModal.isVisible();
    console.log(`  Auth modal visible: ${authModalVisible}`);

    // Fill in temp username and login
    await page.fill('#miner-input', '[AUDIT]Bot');
    await page.click('#btn-start-session');
    await page.waitForTimeout(3000);

    // Screenshot: main game view
    await page.screenshot({ path: `${OUT}/bp${bp}_02_main_view.png`, fullPage: true });

    // === MEASUREMENTS ===
    const measurements = await page.evaluate(() => {
      const results = {};

      // Viewport
      results.viewportWidth = window.innerWidth;
      results.viewportHeight = window.innerHeight;
      results.scrollWidth = document.documentElement.scrollWidth;
      results.scrollHeight = document.documentElement.scrollHeight;
      results.clientWidth = document.documentElement.clientWidth;
      results.clientHeight = document.documentElement.clientHeight;
      results.hasHorizontalScroll = document.documentElement.scrollWidth > document.documentElement.clientWidth;
      results.hasVerticalScroll = document.documentElement.scrollHeight > document.documentElement.clientHeight;

      // Body overflow
      const bodyStyle = window.getComputedStyle(document.body);
      results.bodyOverflow = bodyStyle.overflow;
      results.bodyHeight = bodyStyle.height;

      // Mecha frame
      const frame = document.querySelector('.mecha-frame');
      if (frame) {
        const fr = frame.getBoundingClientRect();
        results.frameWidth = fr.width;
        results.frameHeight = fr.height;
        results.frameLeft = fr.left;
        results.frameTop = fr.top;
        results.frameOverflow = window.getComputedStyle(frame).overflow;
      }

      // HUD Header
      const header = document.querySelector('.hud-header');
      if (header) {
        const hr = header.getBoundingClientRect();
        results.headerHeight = hr.height;
        results.headerWidth = hr.width;
        results.headerOverflow = window.getComputedStyle(header).overflow;
      }

      // HUD Metrics
      const metrics = document.querySelector('.hud-metrics');
      if (metrics) {
        const mr = metrics.getBoundingClientRect();
        results.metricsWidth = mr.width;
        results.metricsOverflow = window.getComputedStyle(metrics).overflow;
      }

      // Metric units
      const metricUnits = document.querySelectorAll('.metric-unit');
      results.metricUnits = [];
      metricUnits.forEach((mu, i) => {
        const r = mu.getBoundingClientRect();
        results.metricUnits.push({ index: i, width: r.width, height: r.height, overflow: window.getComputedStyle(mu).overflow });
      });

      // HUD Body (grid layout)
      const hudBody = document.querySelector('.hud-body');
      if (hudBody) {
        const br = hudBody.getBoundingClientRect();
        results.hudBodyWidth = br.width;
        results.hudBodyHeight = br.height;
        results.hudBodyDisplay = window.getComputedStyle(hudBody).display;
        results.hudBodyGridTemplate = window.getComputedStyle(hudBody).gridTemplateColumns;
      }

      // Stage center
      const stage = document.querySelector('.stage-center');
      if (stage) {
        const sr = stage.getBoundingClientRect();
        results.stageWidth = sr.width;
        results.stageHeight = sr.height;
        results.stageOverflow = window.getComputedStyle(stage).overflow;
      }

      // Grid hull
      const gridHull = document.querySelector('.grid-hull');
      if (gridHull) {
        const gr = gridHull.getBoundingClientRect();
        results.gridHullWidth = gr.width;
        results.gridHullHeight = gr.height;
        results.gridHullAspectRatio = gr.width / gr.height;
      }

      // Sidebar
      const sidebar = document.querySelector('.sidebar-right');
      if (sidebar) {
        const sbr = sidebar.getBoundingClientRect();
        results.sidebarWidth = sbr.width;
        results.sidebarHeight = sbr.height;
        results.sidebarOverflow = window.getComputedStyle(sidebar).overflowY;
      }

      // Nav buttons
      const navBtns = document.querySelectorAll('.mecha-nav-group .mecha-btn');
      results.navButtons = [];
      navBtns.forEach((btn, i) => {
        const r = btn.getBoundingClientRect();
        const style = window.getComputedStyle(btn);
        results.navButtons.push({
          index: i,
          height: r.height,
          width: r.width,
          minHeight: parseInt(style.minHeight) || 0,
          textOverflow: style.textOverflow,
          whiteSpace: style.whiteSpace
        });
      });

      // Touch targets (buttons)
      const buttons = document.querySelectorAll('button, .btn-action-small, .mecha-btn');
      results.touchTargets = [];
      buttons.forEach((btn, i) => {
        if (btn.offsetParent === null) return; // skip hidden
        const r = btn.getBoundingClientRect();
        if (r.width < 44 || r.height < 44) {
          results.touchTargets.push({
            index: i,
            id: btn.id || btn.className,
            width: r.width,
            height: r.height,
            text: btn.textContent.trim().substring(0, 30)
          });
        }
      });

      // Footer
      const footer = document.querySelector('.hud-footer');
      if (footer) {
        const fr2 = footer.getBoundingClientRect();
        results.footerHeight = fr2.height;
        results.footerWidth = fr2.width;
      }

      // Energy bar
      const energyBar = document.querySelector('.energy-bar-container');
      if (energyBar) {
        const er = energyBar.getBoundingClientRect();
        results.energyBarWidth = er.width;
        results.energyBarHeight = er.height;
      }

      // Level bar
      const levelBar = document.querySelector('.level-bar-container');
      if (levelBar) {
        const lr = levelBar.getBoundingClientRect();
        results.levelBarVisible = !levelBar.hidden;
        results.levelBarWidth = lr.width;
      }

      // Race box
      const raceBox = document.querySelector('.race-box');
      if (raceBox) {
        const rr = raceBox.getBoundingClientRect();
        results.raceBoxWidth = rr.width;
        results.raceBoxHeight = rr.height;
      }

      // Modals
      const modals = document.querySelectorAll('.modal-wrap');
      results.modals = [];
      modals.forEach((m, i) => {
        const r = m.getBoundingClientRect();
        const style = window.getComputedStyle(m);
        results.modals.push({
          id: m.id,
          display: style.display,
          zIndex: style.zIndex,
          width: r.width,
          height: r.height
        });
      });

      // Text truncation check
      const textElements = document.querySelectorAll('.metric-lbl, .hud-sys-tag, .u-inline-013, .u-inline-015, .u-inline-026, .u-inline-028');
      results.truncatedText = [];
      textElements.forEach(el => {
        if (el.scrollWidth > el.clientWidth) {
          results.truncatedText.push({
            selector: el.className || el.id,
            scrollWidth: el.scrollWidth,
            clientWidth: el.clientWidth,
            text: el.textContent.trim().substring(0, 30)
          });
        }
      });

      // Clip-path check
      const frameStyle = window.getComputedStyle(document.querySelector('.mecha-frame'));
      results.clipPath = frameStyle.clipPath;

      // Safe area insets
      results.safeAreaTop = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--safe-area-inset-top')) || 0;

      // Check for elements extending beyond viewport
      const allElements = document.querySelectorAll('*');
      results.elementsBeyondViewport = [];
      allElements.forEach(el => {
        if (el.offsetParent === null) return;
        const r = el.getBoundingClientRect();
        if (r.right > window.innerWidth || r.bottom > window.innerHeight || r.left < 0 || r.top < 0) {
          if (r.width > 0 && r.height > 0) {
            results.elementsBeyondViewport.push({
              tag: el.tagName,
              id: el.id || '',
              className: (el.className || '').substring(0, 40),
              right: r.right,
              bottom: r.bottom,
              left: r.left,
              top: r.top
            });
          }
        }
      });

      // Tab panes
      const tabPanes = document.querySelectorAll('.tab-pane');
      results.tabPanes = [];
      tabPanes.forEach(tp => {
        const r = tp.getBoundingClientRect();
        const style = window.getComputedStyle(tp);
        results.tabPanes.push({
          id: tp.id,
          active: tp.classList.contains('active'),
          display: style.display,
          height: r.height,
          overflowY: style.overflowY
        });
      });

      return results;
    });

    console.log(`  Measurements for ${bp}px:`);
    console.log(`    Viewport: ${measurements.viewportWidth}x${measurements.viewportHeight}`);
    console.log(`    Scroll: ${measurements.scrollWidth}x${measurements.scrollHeight}`);
    console.log(`    Has H-scroll: ${measurements.hasHorizontalScroll}`);
    console.log(`    Has V-scroll: ${measurements.hasVerticalScroll}`);
    console.log(`    Frame: ${measurements.frameWidth}x${measurements.frameHeight}`);
    console.log(`    Header: ${measurements.headerWidth}x${measurements.headerHeight}`);
    console.log(`    HUD Body grid: ${measurements.hudBodyGridTemplate}`);
    console.log(`    Stage: ${measurements.stageWidth}x${measurements.stageHeight}`);
    console.log(`    Grid Hull: ${measurements.gridHullWidth}x${measurements.gridHullHeight}`);
    console.log(`    Sidebar: ${measurements.sidebarWidth}x${measurements.sidebarHeight}`);
    console.log(`    Footer: ${measurements.footerWidth}x${measurements.footerHeight}`);
    console.log(`    Clip-path: ${measurements.clipPath}`);
    console.log(`    Truncated text elements: ${measurements.truncatedText.length}`);
    console.log(`    Elements beyond viewport: ${measurements.elementsBeyondViewport.length}`);
    console.log(`    Small touch targets: ${measurements.touchTargets.length}`);

    // === FINDINGS ===
    // Check horizontal scroll
    if (measurements.hasHorizontalScroll) {
      addFinding('HIGH', bp, 'Page', 'No horizontal scroll', `scrollWidth(${measurements.scrollWidth}) > clientWidth(${measurements.clientWidth})`, 'body', 'pixel.css:76-92');
    }

    // Check frame exceeds viewport
    if (measurements.frameWidth > measurements.viewportWidth) {
      addFinding('HIGH', bp, 'Mecha Frame', 'Frame fits within viewport', `Frame width ${measurements.frameWidth} > viewport ${measurements.viewportWidth}`, '.mecha-frame', 'pixel.css:109-126');
    }

    // Check sidebar width at narrow breakpoints
    if (bp <= 768 && measurements.hudBodyGridTemplate.includes('340px')) {
      addFinding('HIGH', bp, 'Sidebar', 'Sidebar should collapse or become full-width on mobile', `Grid still uses 340px sidebar column at ${bp}px`, '.hud-body', 'pixel.css:190-197');
    }

    // Check touch targets
    for (const tt of measurements.touchTargets) {
      if (tt.height < 44 || tt.width < 44) {
        addFinding('MEDIUM', bp, `Touch target: ${tt.text}`, 'Min 44x44px touch target (WCAG)', `${tt.width}x${tt.height}`, tt.id || tt.className, 'pixel.css:469-484');
      }
    }

    // Check truncated text
    for (const tt of measurements.truncatedText) {
      addFinding('MEDIUM', bp, `Text: ${tt.text}`, 'Text should not be truncated', `scrollWidth(${tt.scrollWidth}) > clientWidth(${tt.clientWidth})`, tt.selector, 'pixel.css');
    }

    // Check elements beyond viewport
    for (const eb of measurements.elementsBeyondViewport) {
      addFinding('LOW', bp, `${eb.tag}#${eb.id}`, 'Element should be within viewport', `Element extends beyond viewport: right=${eb.right}, bottom=${eb.bottom}`, eb.className, 'pixel.css');
    }

    // Check clip-path at mobile
    if (bp <= 559 && measurements.clipPath !== 'none') {
      addFinding('MEDIUM', bp, 'Mecha Frame', 'clip-path should be none on mobile (<559px)', `clip-path is ${measurements.clipPath}`, '.mecha-frame', 'pixel.css:544-545');
    }

    // Check grid hull aspect ratio
    if (measurements.gridHullAspectRatio && Math.abs(measurements.gridHullAspectRatio - 1) > 0.05) {
      addFinding('MEDIUM', bp, 'Grid Hull', 'Grid should be square (aspect-ratio: 1/1)', `Aspect ratio is ${measurements.gridHullAspectRatio}`, '.grid-hull', 'pixel.css:257-265');
    }

    // Check header height on mobile
    if (bp <= 559 && measurements.headerHeight > 120) {
      addFinding('LOW', bp, 'HUD Header', 'Header should be compact on mobile', `Header height is ${measurements.headerHeight}px`, '.hud-header', 'pixel.css:2019-2026');
    }

    // === NAVIGATE TABS ===
    // Click each tab and screenshot
    const tabs = [
      { id: 'tab-btn-tx', name: 'tx' },
      { id: 'tab-btn-shop', name: 'shop' },
      { id: 'tab-btn-rank', name: 'rank' },
      { id: 'tab-btn-info', name: 'info' }
    ];

    for (const tab of tabs) {
      const btn = page.locator(`#${tab.id}`);
      if (await btn.isVisible().catch(() => false)) {
        await btn.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: `${OUT}/bp${bp}_tab_${tab.name}.png`, fullPage: true });

        // Measure tab content
        const tabMeasurements = await page.evaluate((tabId) => {
          const tab = document.getElementById(tabId);
          if (!tab) return null;
          const r = tab.getBoundingClientRect();
          const style = window.getComputedStyle(tab);
          return {
            height: r.height,
            overflowY: style.overflowY,
            scrollHeight: tab.scrollHeight,
            clientHeight: tab.clientHeight,
            hasScroll: tab.scrollHeight > tab.clientHeight
          };
        }, `tab-${tab.name}`);

        if (tabMeasurements) {
          console.log(`  Tab ${tab.name}: height=${tabMeasurements.height}, scroll=${tabMeasurements.hasScroll}, overflow=${tabMeasurements.overflowY}`);
          if (tabMeasurements.hasScroll && bp <= 768) {
            addFinding('LOW', bp, `Tab ${tab.name}`, 'Tab content should fit without scroll on mobile', `Tab has scroll at ${bp}px (scrollHeight=${tabMeasurements.scrollHeight}, clientHeight=${tabMeasurements.clientHeight})`, `#tab-${tab.name}`, 'pixel.css:428-435');
          }
        }
      }
    }

    // === CHECK MODALS ===
    // Auth modal is already visible, check its dimensions
    const authModalDims = await page.evaluate(() => {
      const modal = document.querySelector('#auth-modal .modal-mecha-box');
      if (!modal) return null;
      const r = modal.getBoundingClientRect();
      return { width: r.width, height: r.height, left: r.left, top: r.top };
    });

    if (authModalDims) {
      console.log(`  Auth modal box: ${authModalDims.width}x${authModalDims.height}`);
      if (authModalDims.width > measurements.viewportWidth - 20) {
        addFinding('MEDIUM', bp, 'Auth Modal', 'Modal should have padding from viewport edges', `Modal width ${authModalDims.width} is too close to viewport ${measurements.viewportWidth}`, '.modal-mecha-box', 'pixel.css:513-521');
      }
    }

    // === CHECK RESPONSIVE MEDIA QUERIES ===
    const mediaQueryResults = await page.evaluate((bp) => {
      const results = {};
      results.mq900 = window.matchMedia('(max-width: 900px)').matches;
      results.mq559 = window.matchMedia('(max-width: 559px)').matches;
      results.mq320 = window.matchMedia('(max-width: 320px)').matches;

      // Check computed styles at this breakpoint
      const bodyStyle = window.getComputedStyle(document.body);
      results.bodyPadding = bodyStyle.padding;

      const frameStyle = window.getComputedStyle(document.querySelector('.mecha-frame'));
      results.frameClipPath = frameStyle.clipPath;
      results.frameBorderRadius = frameStyle.borderRadius;

      const hudBodyStyle = window.getComputedStyle(document.querySelector('.hud-body'));
      results.hudBodyGrid = hudBodyStyle.gridTemplateColumns;

      const stageStyle = window.getComputedStyle(document.querySelector('.stage-center'));
      results.stageBorderRight = stageStyle.borderRightWidth;
      results.stageBorderBottom = stageStyle.borderBottomWidth;

      const sidebarStyle = window.getComputedStyle(document.querySelector('.sidebar-right'));
      results.sidebarWidth = sidebarStyle.width;

      const gridHullStyle = window.getComputedStyle(document.querySelector('.grid-hull'));
      results.gridHullWidth = gridHullStyle.width;

      return results;
    }, bp);

    console.log(`  Media queries: 900px=${mediaQueryResults.mq900}, 559px=${mediaQueryResults.mq559}`);
    console.log(`  Frame clip-path: ${mediaQueryResults.frameClipPath}`);
    console.log(`  HUD Body grid: ${mediaQueryResults.hudBodyGrid}`);

    // Check if 900px media query is applied correctly
    if (bp <= 900 && mediaQueryResults.hudBodyGrid !== '1fr') {
      addFinding('HIGH', bp, 'HUD Body Grid', 'Should be single column (1fr) at <=900px', `Grid is ${mediaQueryResults.hudBodyGrid}`, '.hud-body', 'pixel.css:547');
    }

    if (bp <= 900 && mediaQueryResults.frameClipPath !== 'none') {
      addFinding('MEDIUM', bp, 'Frame Clip-path', 'Should be none at <=900px', `clip-path is ${mediaQueryResults.frameClipPath}`, '.mecha-frame', 'pixel.css:545');
    }

    if (bp <= 900 && mediaQueryResults.stageBorderRight !== '0px') {
      addFinding('LOW', bp, 'Stage Border', 'Right border should be removed at <=900px', `border-right is ${mediaQueryResults.stageBorderRight}`, '.stage-center', 'pixel.css:548');
    }

    // Check for missing breakpoints
    if (bp === 2560) {
      // Ultra-wide: check if content is too narrow
      if (measurements.frameWidth < 2000) {
        addFinding('LOW', bp, 'Mecha Frame', 'Content should utilize more screen space on ultrawide', `Frame max-width is ${measurements.frameWidth}px on 2560px viewport`, '.mecha-frame', 'pixel.css:111');
      }
    }

    if (bp === 320) {
      // Phone: check critical elements
      if (measurements.gridHullWidth < 200) {
        addFinding('HIGH', bp, 'Grid Hull', 'Grid should be usable on 320px screens', `Grid width is only ${measurements.gridHullWidth}px`, '.grid-hull', 'pixel.css:259');
      }

      if (measurements.headerHeight > 150) {
        addFinding('MEDIUM', bp, 'HUD Header', 'Header should be compact on 320px', `Header height is ${measurements.headerHeight}px`, '.hud-header', 'pixel.css:150-160');
      }
    }

    await context.close();
  }

  // === CROSS-BREAKPOINT ANALYSIS ===
  console.log('\n\n=== CROSS-BREAKPOINT ANALYSIS ===');

  // Check breakpoint coverage
  const cssBreakpoints = [900, 559]; // From CSS media queries
  const requiredBreakpoints = [320, 768, 1024, 1440, 2560];

  console.log('CSS media query breakpoints:', cssBreakpoints);
  console.log('Required audit breakpoints:', requiredBreakpoints);

  // Gap analysis
  for (const bp of requiredBreakpoints) {
    const coveredBy900 = bp <= 900;
    const coveredBy559 = bp <= 559;
    console.log(`  ${bp}px: covered by 900px MQ=${coveredBy900}, 559px MQ=${coveredBy559}`);
  }

  // Missing: no media query for 768-900 range specifically
  // 768px falls under 900px MQ but not 559px MQ
  // 1024px is above both MQs (desktop layout)
  // 2560px is above both MQs (desktop layout, max-width: 1440px)

  console.log('\n  MISSING BREAKPOINT COVERAGE:');
  console.log('  - No specific MQ for 768px (tablet portrait)');
  console.log('  - No specific MQ for 1024px (tablet landscape)');
  console.log('  - No specific MQ for 2560px (ultrawide)');
  console.log('  - CSS only has max-width: 900px and max-width: 559px');

  // === SAVE FINDINGS ===
  const findingsBySeverity = { HIGH: [], MEDIUM: [], LOW: [] };
  FINDINGS.forEach(f => findingsBySeverity[f.severity].push(f));

  console.log(`\n\n=== FINDINGS SUMMARY ===`);
  console.log(`HIGH: ${findingsBySeverity.HIGH.length}`);
  console.log(`MEDIUM: ${findingsBySeverity.MEDIUM.length}`);
  console.log(`LOW: ${findingsBySeverity.LOW.length}`);

  // Save findings to JSON
  fs.writeFileSync(`${OUT}/findings.json`, JSON.stringify(FINDINGS, null, 2));

  console.log('\nAudit complete. Findings saved to findings.json');
  console.log(JSON.stringify(FINDINGS, null, 2));

  await browser.close();
})();
