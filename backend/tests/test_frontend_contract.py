"""Contratos estáticos do frontend servido sob a CSP de produção."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = ROOT / "frontend" / "index.html"
GAME_JS = ROOT / "frontend" / "game.js"
NGINX_CONF = ROOT / "frontend" / "nginx.conf"
PIXEL_CSS = ROOT / "frontend" / "pixel.css"
SERVICE_WORKER = ROOT / "frontend" / "service-worker.js"


def test_frontend_bootstrap_contract_is_compatible_with_strict_csp() -> None:
    """O fluxo inicial não pode depender de handlers inline nem abortar no bootstrap."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    nginx = NGINX_CONF.read_text(encoding="utf-8")

    assert "script-src 'self'" in nginx
    assert not re.search(r"\son[a-z]+\s*=", html, flags=re.IGNORECASE)

    auth_form = re.search(
        r'<form[^>]+id="auth-form"[^>]*>(?P<body>.*?)</form>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert auth_form is not None
    assert re.search(
        r'<button[^>]+id="btn-start-session"[^>]+type="submit"',
        auth_form.group("body"),
        flags=re.IGNORECASE,
    )
    assert "getElementById('auth-form').addEventListener('submit'" in javascript

    assert "const originalHandleWebSocketMessage = handleWebSocketMessage;" not in javascript


def test_frontend_uses_only_canonical_network_api_paths() -> None:
    """Mecânicas REST devem usar o namespace multi-rede canônico."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "/api/${activeRealmId}/" not in javascript
    assert "function activeNetworkApiUrl(" in javascript


def test_session_mechanics_use_registered_initializers_without_stubs() -> None:
    """Módulos opcionais não podem monkey-patchar o login nem usar funções vazias."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert not re.search(r"^startSession\s*=", javascript, flags=re.MULTILINE)
    assert "function registerSessionInitializer(" in javascript
    assert "await runSessionInitializers();" in javascript
    assert "return loadMarketInventory();" in javascript
    assert "currentRoundWords.forEach" in javascript


def test_sprint_and_result_flow_have_deterministic_actions() -> None:
    """Quatro palavras Sprint e a ação do modal devem ser sempre acionáveis."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const rowIndex = index % currentGridSize;" in javascript
    assert "setNextButtonAction(prepareNextBlock);" in javascript
    assert "btn.onclick = rbfHandler;" not in javascript


def test_websocket_reconnect_uses_the_post_teardown_generation() -> None:
    """Uma queda transitória deve reconectar sem acessar elementos ausentes."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const reconnectGeneration = sessionGeneration;" in javascript
    assert "reconnectGeneration === sessionGeneration && !ws" in javascript
    assert 'if (loaderText) loaderText.innerText = "Falha na reconexão.' in javascript


def test_mission_progress_uses_persisted_game_counters() -> None:
    """Missões devem receber os stats reais, incluindo RBF e ganhos da rodada."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "rbf_used: rbfUsedTotal" in javascript
    assert "max_round_earnings: maxRoundEarningsTotal" in javascript
    assert "currentRoundEarnings += Math.floor(points);" in javascript


def test_frontend_assets_are_strict_csp_and_offline_compatible() -> None:
    """O shell não deve depender de inline CSS nem de fontes externas."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    stylesheet = PIXEL_CSS.read_text(encoding="utf-8")
    service_worker = SERVICE_WORKER.read_text(encoding="utf-8")
    nginx = NGINX_CONF.read_text(encoding="utf-8")
    shell_assets = service_worker.split("const SHELL_ASSETS = [", 1)[1].split("];", 1)[0]

    assert not re.search(r'\sstyle\s*=\s*"', html, flags=re.IGNORECASE)
    assert not re.search(r'\sstyle\s*=\s*"', javascript, flags=re.IGNORECASE)
    assert "fonts.googleapis.com" not in html
    assert "@font-face" in stylesheet
    assert "fonts/jetbrains-mono-latin.woff2" in stylesheet
    assert "const CACHE_VERSION =" in service_worker
    assert "./pixel.css" in service_worker
    assert "./fonts/jetbrains-mono-latin.woff2" in service_worker
    assert "'./index.html'," not in shell_assets
    assert "return cache.match('./');" in service_worker
    assert "pixel\\.css" in nginx
    assert "location ^~ /fonts/" in nginx
    assert "absolute_redirect off;" in nginx
    assert "@media (max-width: 559px)" in stylesheet
    assert ".grid-hull { width: min(100%, 380px); }" in stylesheet
    assert "--glass-border:" in stylesheet
    assert "--page-max:" in stylesheet


def test_frontend_exposes_the_five_approved_mechanics_tabs() -> None:
    """A UI deve manter a arquitetura aprovada sem tabs Mecha legadas."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")

    approved_tabs = ["jogo", "upgrades", "competir", "perfil", "social"]
    assert re.findall(r'data-tab="([^"]+)"', html) == approved_tabs
    for tab_name in approved_tabs:
        assert f'id="tab-{tab_name}"' in html

    assert len(re.findall(r"function\s+showTab\s*\(", javascript)) == 1
    assert "function switchTab(" not in javascript
    assert "compatibility-aliases" not in html
    for legacy_button_id in (
        "btn-cards",
        "btn-chat-toggle",
        "btn-friends",
        "btn-season",
        "btn-skills",
    ):
        assert f"getElementById('{legacy_button_id}')" not in javascript


def test_mechanics_are_grouped_under_the_approved_tabs() -> None:
    """Cada mecânica deve existir dentro da área correspondente, não em aliases."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    tab_positions = {
        name: html.index(f'id="tab-{name}"')
        for name in ("jogo", "upgrades", "competir", "perfil", "social")
    }
    ordered_tabs = list(tab_positions)

    def tab_markup(name: str) -> str:
        start = tab_positions[name]
        index = ordered_tabs.index(name)
        if index + 1 == len(ordered_tabs):
            return html[start:html.index("</aside>", start)]
        return html[start:tab_positions[ordered_tabs[index + 1]]]

    expected_ids = {
        "jogo": ("tx-list-container",),
        "upgrades": (
            "btn-buy-hint",
            "btn-buy-hw",
            "btn-buy-ln",
            "btn-buy-energy",
            "btn-open-crate-free",
            "btn-decoder-launch",
        ),
        "competir": (
            "leaderboard-list",
            "pool-list",
            "missions-panel",
            "sprint-timer-display",
        ),
        "perfil": (
            "staking-panel",
            "skills-panel",
            "season-panel",
            "cards-panel",
        ),
        "social": ("chat-panel", "friends-panel", "market-panel"),
    }
    for tab_name, element_ids in expected_ids.items():
        markup = tab_markup(tab_name)
        for element_id in element_ids:
            assert f'id="{element_id}"' in markup, (tab_name, element_id)


def test_responsive_layout_covers_all_supported_screen_classes() -> None:
    """O layout não pode recortar jogo/tabs nem desperdiçar telas ultrawide."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert "--page-max: 2560px;" in css
    assert "grid-template-columns: minmax(0, 1fr) clamp(320px, 28vw, 520px);" in css
    assert "@media (max-width: 1023px)" in css
    assert "@media (max-width: 767px)" in css
    assert "@media (min-width: 1920px)" in css
    assert "width: min(58dvh, calc(100vw - clamp(320px, 28vw, 520px) - 64px), 1040px);" in css
    assert "width: min(50dvh, calc(100vw - clamp(320px, 32vw, 400px) - 48px), 720px);" in css
    assert ".stage-center {\n            display: flex;\n            flex-direction: column;\n            align-items: center;\n            justify-content: center;\n            padding: 12px;" in css

    tablet_rules = css[css.index("@media (max-width: 1023px)"):]
    assert "overflow-y: auto;" in tablet_rules
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in tablet_rules
    assert "min-height: 44px;" in tablet_rules
    assert "overflow: visible;" in tablet_rules


def test_interactive_targets_are_large_enough_for_pointer_and_touch() -> None:
    """Ações internas precisam respeitar alvos mínimos no desktop e touch."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert ".btn-action-small {\n            min-height: 28px;" in css
    assert ".tab-pane :is(button, input, select)," in css
    assert "#btn-powerups-toggle," in css
    assert "#btn-dismiss-event {\n        min-height: 44px;\n        min-width: 44px;" in css


def test_service_worker_cache_version_tracks_phase4_assets() -> None:
    """O navegador não pode continuar servindo o CSS anterior ao redesign."""
    service_worker = SERVICE_WORKER.read_text(encoding="utf-8")

    assert "const CACHE_VERSION = 'v17';" in service_worker


def test_ui_uses_local_svg_icons_instead_of_emoji_glyphs() -> None:
    """Ícones visuais devem ser SVGs próprios, previsíveis e offline."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    service_worker = SERVICE_WORKER.read_text(encoding="utf-8")
    sprite = ROOT / "frontend" / "icons" / "ui-sprite.svg"
    emoji_pattern = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]")

    assert not emoji_pattern.search(html)
    assert not emoji_pattern.search(javascript)
    assert sprite.is_file()
    assert "./icons/ui-sprite.svg" in service_worker
    assert "function iconSvg(" in javascript
    assert "function setSvgIcon(" in javascript


def test_achievement_icon_catalog_is_shared_by_grid_and_toast() -> None:
    """Grid e toast não podem depender de uma variável local fora de escopo."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const ACHIEVEMENT_CATEGORIES = [" in javascript
    assert "function achievementIconName(" in javascript
    assert "categories.find(" not in javascript


def test_dynamic_crate_modal_does_not_duplicate_static_dom_id() -> None:
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert 'id="crate-icon"' not in javascript
    assert "overlay.querySelector('.crate-icon')" in javascript


def test_modal_state_synchronizes_all_visibility_mechanisms() -> None:
    """Abrir/fechar modal deve manter CSS, atributo nativo e ARIA coerentes."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    modal_helper = javascript.split("function setModalState(", 1)[1].split("\n}", 1)[0]
    assert "modal.classList.toggle('hidden', !isActive);" in modal_helper
    assert "modal.hidden = !isActive;" in modal_helper
    assert "modal.classList.toggle('active', isActive);" in modal_helper
    assert "modal.setAttribute('aria-hidden', String(!isActive));" in modal_helper


def test_pwa_update_banner_uses_the_shared_modal_visibility_contract() -> None:
    """Banner PWA não pode manter classe hidden ao anunciar atualização."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "setModalState(updateBannerEl, Boolean(registration.waiting));" in javascript
    assert "setModalState(updateBannerEl, false);" in javascript
    assert "updateBannerEl.hidden = !registration.waiting;" not in javascript
    assert "updateBannerEl.hidden = true;" not in javascript


def test_decoder_start_matches_the_backend_post_contract() -> None:
    """Decoder deve enviar o payload no método aceito pelo endpoint FastAPI."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    decoder_start = javascript.split("async function startDecoderGame()", 1)[1].split(
        "function updateDecoderTimer()", 1
    )[0]

    assert "method: 'POST'" in decoder_start
    assert "'Content-Type': 'application/json'" in decoder_start
    assert "body: JSON.stringify({ username: minerName })" in decoder_start
    assert "method: 'GET'" not in decoder_start


def test_staking_status_does_not_destroy_duration_select_options() -> None:
    """Renderizar stake ativo não pode substituir os filhos do select de duração."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert 'id="staking-active-duration"' in html
    assert (
        "const stakingActiveDurationEl = "
        "document.getElementById('staking-active-duration');"
    ) in javascript
    assert "stakingActiveDurationEl.textContent = `${stakeState.duration_hours}h`;" in javascript
    assert "stakingDurationEl.textContent" not in javascript


def test_market_uses_single_static_filter_and_refresh_controls() -> None:
    """Renderer de listings não pode duplicar os controles persistentes do Market."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    render_market = javascript.split("function renderMarketList()", 1)[1].split(
        "function renderMarketHistory()", 1
    )[0]

    assert '<select class="input-mecha u-inline-035" id="market-filter-powerup"' in html
    assert html.count('id="market-filter-powerup"') == 1
    assert html.count('id="btn-refresh-market"') == 1
    assert 'id="market-filter-powerup"' not in render_market
    assert 'id="btn-refresh-market"' not in render_market
    assert "marketBrowseEl.querySelector('#market-filter-powerup')" not in render_market
    assert "marketBrowseEl.querySelector('#btn-refresh-market')" not in render_market
    assert "marketFilterPowerupEl.addEventListener('change', renderMarketList);" in javascript
    assert "btnRefreshMarketEl.addEventListener('click', loadMarketList);" in javascript


def test_pool_metadata_stays_separate_from_backend_username() -> None:
    """Pool aparece no HUD e score sem produzir username inválido nos demais endpoints."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    start_session = javascript.split("async function startSession", 1)[1].split(
        "socket.onopen", 1
    )[0]
    submit_score = javascript.split("async function submitScore()", 1)[1].split(
        "async function syncPlayerState()", 1
    )[0]

    assert "let poolName = '';" in javascript
    assert "poolName," in javascript
    assert "poolName = saved.poolName ?? '';" in javascript
    assert "poolName = safePoolTag;" in start_session
    assert "minerName = `[${safePoolTag}] ${minerName}`;" not in start_session
    assert "operatorDisplayName()" in start_session
    assert "pool_name: poolName || null" in submit_score


def test_teardown_resets_session_scoped_mechanics_and_renderings() -> None:
    """Trocar jogador/rede não pode exibir estado das mecânicas anteriores."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    teardown = javascript.split("function teardownSession(", 1)[1].split(
        "function setModalState(", 1
    )[0]
    assert "function resetSessionModules()" in javascript
    module_reset = javascript.split("function resetSessionModules()", 1)[1].split(
        "function teardownSession(", 1
    )[0]

    assert "resetSessionModules();" in teardown
    for expected in (
        "resetBossState();",
        "decoderActive = false;",
        "hideGlobalEventBanner();",
        "achievementsData = null;",
        "missionsData = null;",
        "skillTreeData = null;",
        "seasonData = null;",
        "cardsData = null;",
        "marketData = null;",
        "marketHistoryData = null;",
        "marketInventory = null;",
        "friendsData = null;",
        "chatHistoryLoaded = false;",
        "stakeState = createEmptyStakeState();",
        "energyState = createInitialEnergyState();",
        "crateState = createInitialCrateState();",
        "levelState = createInitialLevelState();",
    ):
        assert expected in module_reset


def test_main_tablist_supports_wai_aria_keyboard_navigation() -> None:
    """As cinco áreas principais devem ser operáveis sem mouse."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "function handleMainTabKeydown(event)" in javascript
    handler = javascript.split("function handleMainTabKeydown(event)", 1)[1].split(
        "\ndocument.querySelectorAll('.mecha-nav-group .mecha-btn[data-tab]').forEach", 1
    )[0]
    for key in ("ArrowRight", "ArrowLeft", "Home", "End"):
        assert key in handler
    assert "target.focus();" in handler
    assert "target.click();" in handler
    assert "button.addEventListener('keydown', handleMainTabKeydown);" in javascript


def test_modals_are_not_nested_inside_hidden_tabpanels() -> None:
    """Um modal global não pode herdar o atributo hidden de uma tab inativa."""

    class ModalAncestorParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.div_stack: list[set[str]] = []
            self.nested_modals: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag != "div":
                return
            attributes = dict(attrs)
            classes = set((attributes.get("class") or "").split())
            if "modal-wrap" in classes and any(
                "tab-pane" in parent for parent in self.div_stack
            ):
                self.nested_modals.append(attributes.get("id") or "sem-id")
            self.div_stack.append(classes)

        def handle_endtag(self, tag: str) -> None:
            if tag == "div" and self.div_stack:
                self.div_stack.pop()

    parser = ModalAncestorParser()
    parser.feed(INDEX_HTML.read_text(encoding="utf-8"))

    assert parser.nested_modals == []


def test_mechanics_are_grouped_in_keyboard_accessible_secondary_sections() -> None:
    """Mecânicas densas devem ter um único caminho organizado dentro de cada tab."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    expected_sections = {
        "upgrades": ("shop", "inventory", "tools"),
        "competir": ("ranking", "missions", "sprint"),
        "perfil": ("overview", "progression", "collection", "economy"),
        "social": ("chat", "team", "market"),
    }

    for group, sections in expected_sections.items():
        assert f'data-section-nav="{group}"' in html
        for section in sections:
            panel_id = f"section-{group}-{section}"
            assert f'id="{panel_id}"' in html
            assert f'aria-controls="{panel_id}"' in html
            assert f'data-section-group="{group}"' in html
            assert f'data-section="{section}"' in html

    assert "function activateMechanicSection(groupName, sectionName" in javascript
    assert "function handleMechanicSectionKeydown(event)" in javascript
    assert "button.addEventListener('keydown', handleMechanicSectionKeydown);" in javascript
    assert "panel.hidden = !active;" in javascript
    assert "button.setAttribute('aria-selected', String(active));" in javascript


def test_secondary_navigation_uses_mecha_tokens_and_touch_safe_targets() -> None:
    """Subnavegação mantém o redesign pixel/mecha e alvos adequados ao toque."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert ".mechanic-subnav {" in css
    assert ".mechanic-subnav-btn {" in css
    assert "min-height: 44px;" in css
    assert ".mechanic-subnav-btn.active" in css
    assert ".mechanic-subnav-btn:focus-visible" in css
    assert ".mechanic-section[hidden]" in css


def test_powerups_toggle_is_visible_when_its_content_is_collapsed() -> None:
    """O controle de Power-ups não pode ficar preso dentro do próprio hidden."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")

    container_tag = re.search(r'<div[^>]+id="powerups-bar-container"[^>]*>', html)
    content_tag = re.search(r'<div[^>]+id="powerups-active"[^>]*>', html)
    assert container_tag is not None and "hidden" not in container_tag.group(0)
    assert content_tag is not None and "hidden" in content_tag.group(0)
    assert 'aria-expanded="false"' in html
    assert "const powerupsActiveEl = document.getElementById('powerups-active');" in javascript
    powerups_handler = javascript.split(
        "powerupsToggleBtn.addEventListener('click', () => {", 1
    )[1].split("// Carrega crates ao iniciar sessão", 1)[0]
    assert "if (!sessionReady || !activeRealmId)" in powerups_handler
    assert "announceGameStatus('Inicie uma sessão para acessar os Power-ups.');" in powerups_handler
    assert "powerupsActiveEl.hidden = !isHidden;" in javascript
    assert "powerupsToggleBtn.setAttribute('aria-expanded', String(isHidden));" in javascript


def test_mobile_social_controls_wrap_without_horizontal_overflow() -> None:
    """Chat e Equipe devem caber no painel de 320 px sem ampliar o documento."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert 'class="chat-emoji-bar u-inline-032" id="chat-emoji-bar"' in html
    assert 'class="friends-add-row u-inline-034"' in html
    assert ".chat-emoji-bar {" in css
    assert "flex-wrap: wrap;" in css
    assert ".friends-add-row .input-mecha {" in css
    assert "min-width: 0;" in css
    assert "width: auto;" in css


def test_ultrawide_breakpoint_scales_fixed_pixel_controls_and_labels() -> None:
    """O layout de 42 polegadas não pode manter controles e rótulos de notebook."""
    css = PIXEL_CSS.read_text(encoding="utf-8")
    ultrawide = css.split("@media (min-width: 1920px)", 1)[1]

    assert ".sidebar-right :is(" in ultrawide
    assert "font-size: 8px;" in ultrawide
    assert ".sidebar-right .btn-action-small" in ultrawide
    assert ".sidebar-right .input-mecha" in ultrawide
    assert ".mechanic-subnav-btn" in ultrawide
    assert ".chat-emoji-btn" in ultrawide
    assert "min-height: 44px;" in ultrawide
    assert "min-height: 52px;" in ultrawide

