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
    # Fase 1.4: power-ups usam o inventário PESSOAL (não o stub que devolvia o mercado)
    assert "powerups/${encodeURIComponent(minerName)}" in javascript


def test_sprint_and_result_flow_have_deterministic_actions() -> None:
    """Quatro palavras Sprint e a ação do modal devem ser sempre acionáveis."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    sprint = javascript.split("function renderWordBank()", 1)[1].split(
        "function renderBankWord(", 1
    )[0]
    assert "const uniqueWords = [...new Set(" in sprint
    assert "word => injectWordInGrid(" in sprint
    assert "setNextButtonAction(prepareNextBlock);" in javascript
    assert "btn.onclick = rbfHandler;" not in javascript


def test_global_event_reward_multiplier_is_applied_only_by_backend() -> None:
    """O frontend não pode reaplicar o multiplicador já presente na transação."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    builder = javascript.split("function buildPlayableBlock(", 1)[1].split(
        "function configureGridSize(", 1
    )[0]

    assert "globalRewardMultiplier" not in builder
    assert (
        "effectiveBaseReward = Math.floor(baseReward * halvingRewardFactor);"
        in builder
    )
    assert "tx.multiplier" in builder


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
    # FASE 1920 (25/08): sidebar fluida 22vw (antes 28vw — em 1920px era 27% da
    # tela, efeito "super zoom"); o breakpoint de aumento do chrome moveu de
    # 1920px para 2200px (1080p é resolução padrão, não "tela grande").
    assert "--sidebar-width: clamp(320px, 22vw, 520px);" in css
    assert "grid-template-columns: minmax(0, 1fr) var(--sidebar-width);" in css
    assert "@media (max-width: 1023px)" in css
    assert "@media (max-width: 767px)" in css
    assert "@media (min-width: 2200px)" in css
    assert ".stage-center {\n            display: grid;\n            grid-template-rows: auto minmax(0, 1fr) auto auto;" in css
    assert "grid-template-columns: minmax(0, 1fr) clamp(320px, 32vw, 400px);" not in css
    assert "width: min(50dvh, calc(100vw - clamp(320px, 32vw, 400px) - 48px), 720px);" not in css
    assert "width: min(58dvh, calc(100vw - clamp(320px, 22vw, 520px) - 64px), 1040px);" not in css
    assert "width: min(calc(100dvh - 420px), calc(100vw - clamp(320px, 22vw, 520px) - 64px), 1040px);" not in css

    tablet_rules = css[css.index("@media (max-width: 1023px)"):]
    assert "overflow-y: auto;" in tablet_rules
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in tablet_rules
    assert "min-height: 44px;" in tablet_rules
    assert "overflow: visible;" in tablet_rules


def test_responsive_layout_uses_available_stage_space_without_fixed_chrome_math() -> None:
    """A grade deve caber no palco sem depender de 50/58/64dvh ou 420px mágicos."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert "container-type: size;" in css
    assert "grid-template-rows: auto minmax(0, 1fr) auto auto;" in css
    assert "calc(100cqh - 112px)" in css
    assert "50dvh" not in css
    assert "58dvh" not in css
    assert "64dvh" not in css
    assert "100dvh - 420px" not in css


def test_global_event_banner_is_shell_content_and_does_not_cover_header() -> None:
    """Evento global deve reservar espaço no shell, nunca cobrir o header fixo."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    css = PIXEL_CSS.read_text(encoding="utf-8")

    banner_position = html.index('id="global-event-banner"')
    header_end = html.index("</header>")
    level_bar = html.index('id="level-bar-container"')
    assert header_end < banner_position < level_bar
    banner_css = css[css.index(".global-event-banner {"):css.index(".global-event-banner-inner")]
    assert "position: fixed" not in banner_css
    assert "position: relative" in banner_css


def test_zero_transaction_buffer_starts_watchdog_after_session_handshake() -> None:
    """Sessão sem a primeira transação também precisa de recuperação automática."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    game_start = javascript.split("if (data.action === 'game_start')", 1)[1].split(
        "if (data.action === 'network_status')", 1
    )[0]
    watchdog = javascript.split("function startTxBufferWatchdog()", 1)[1].split(
        "function prepareNextBlock()", 1
    )[0]

    assert "prepareNextBlock();" in game_start
    assert "startTxBufferWatchdog();" in game_start
    assert "if (txBuffer.length === 0) return;" not in watchdog


def test_chat_success_updates_local_rate_limit_without_undefined_variable() -> None:
    """Enviar chat não pode lançar ReferenceError após resposta 2xx."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    chat = javascript.split("async function sendChatMessage()", 1)[1].split(
        "/**\n * Insere um token", 1
    )[0]

    assert "let chatRateRemaining = 5;" in javascript
    assert "chatRateRemaining = Math.max(0, chatRateRemaining - 1);" in chat
    assert "updateRateLimitInfo(chatRateRemaining);" in chat
    assert "updateRateLimitInfo(remaining - 1);" not in chat


def test_zero_transaction_watchdog_exposes_recovery_state_before_reconnect() -> None:
    """Buffer 0/N deve explicar a recuperação, não apenas manter spinner infinito."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    watchdog = javascript.split("function startTxBufferWatchdog()", 1)[1].split(
        "function prepareNextBlock()", 1
    )[0]

    assert "Sem transações" in watchdog
    assert "Reconectando" in watchdog
    assert "announceGameStatus" in watchdog


def test_interactive_targets_are_large_enough_for_pointer_and_touch() -> None:
    """Ações internas precisam respeitar alvos mínimos no desktop e touch."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert ".btn-action-small {\n            min-height: 28px;" in css
    assert ".tab-pane :is(button, input, select)," in css
    assert "#btn-powerups-toggle," in css
    assert "#btn-dismiss-event {\n        min-height: 44px;\n        min-width: 44px;" in css


def test_service_worker_cache_version_tracks_frontend_fixes() -> None:
    """O navegador não pode servir assets anteriores às correções publicadas."""
    service_worker = SERVICE_WORKER.read_text(encoding="utf-8")

    assert "const CACHE_VERSION = 'v67';" in service_worker


def test_pwa_update_is_checked_on_startup_and_handles_already_activated_shell() -> None:
    """A atualização deve ser detectada mesmo sem worker waiting no reload."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const APP_SHELL_VERSION = 'v67';" in javascript
    assert "const APP_SHELL_VERSION_KEY = 'mempool-miner-shell-version';" in javascript
    assert "await registration.update();" in javascript
    assert "localStorage.getItem(APP_SHELL_VERSION_KEY)" in javascript
    assert "Nova versão" in javascript
    assert "RECARREGAR" in javascript


def test_pwa_update_watches_an_installing_worker_even_if_updatefound_was_early() -> None:
    """O listener deve cobrir worker já installing e o evento updatefound."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    register = javascript.split("async function registerPwa()", 1)[1].split(
        "window.addEventListener('online'", 1
    )[0]

    assert "function watchInstallingWorker(registration, installingWorker)" in javascript
    assert "watchInstallingWorker(registration, registration.installing);" in register
    assert "registration.addEventListener('updatefound'" in register


def test_pwa_update_banner_is_clickable_above_auth_modal() -> None:
    """A notificação de versão não pode ficar atrás do modal de autenticação."""
    css = PIXEL_CSS.read_text(encoding="utf-8")
    assert "#pwa-update-banner {" in css
    banner_start = css.index("#pwa-update-banner {")
    banner_end = css.index(".global-event-banner {", banner_start)
    banner_css = css[banner_start:banner_end]

    assert "z-index: 2200;" in banner_css


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


def test_powerup_shop_exposes_all_items_and_buy_flow() -> None:
    """A loja deve permitir comprar cada power-up via contrato server-side."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")
    shop = html.split('id="section-upgrades-shop"', 1)[1].split(
        'id="section-upgrades-inventory"', 1
    )[0]
    for powerup_id in ("time_freeze", "scanner", "double_combo", "magnet", "precision"):
        assert f'data-powerup-id="{powerup_id}"' in shop
        assert f'id="btn-buy-powerup-{powerup_id}"' in shop
    assert "async function buyPowerup(powerupId)" in javascript
    assert "powerups/buy" in javascript
    assert "daily_limit" in javascript
    assert "registerSessionInitializer('powerups'" in javascript


def test_powerup_pending_state_preserves_quantity_and_resets_session_effects() -> None:
    """Unidades pendentes não podem ser deduplicadas nem vazar entre sessões."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    assert "let pendingPowerups = new Map();" in javascript
    assert "pendingPowerups.set(powerupId, (pendingPowerups.get(powerupId) || 0) + 1);" in javascript
    assert "for (const [id, quantity] of pendingPowerups)" in javascript
    assert "powerupEffects.time_freeze = 0;" in javascript
    reset = javascript.split("function resetSessionModules()", 1)[1].split(
        "function formatPvpTimer", 1
    )[0]
    assert "pendingPowerups.clear();" in reset
    assert "powerupsInventoryData = null;" in reset


def test_purchase_handlers_update_missions_without_dead_wrappers() -> None:
    """Compras devem atualizar missões no próprio handler acionado pelo botão."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    for function_name, next_function in (
        ("buyHint", "buyHardware"),
        ("buyHardware", "buyLightning"),
        ("buyLightning", "startTransaction"),
    ):
        body = javascript.split(f"async function {function_name}()", 1)[1].split(
            f"async function {next_function}", 1
        )[0]
        assert "void updateMissionsProgress();" in body
    assert "const originalBuyHint = buyHint;" not in javascript


def test_native_hidden_attribute_overrides_component_display_rules() -> None:
    """Power-ups, staking e futuros painéis hidden devem realmente desaparecer."""
    css = PIXEL_CSS.read_text(encoding="utf-8")

    assert re.search(
        r"^\[hidden\]\s*\{\s*display:\s*none\s*!important;\s*\}",
        css,
        flags=re.MULTILINE,
    )


def test_energy_is_spent_before_building_the_round_and_can_resume() -> None:
    """Falha de energia não pode deixar uma grade ativa sem cronômetro."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const originalStartNetworkRace = startNetworkRace;" not in javascript
    sprint_wrapper = javascript.split(
        "const originalStartNetworkRaceForSprint = startNetworkRace;", 1
    )[1].split("// ============================================\n// Fase 5: Sistema de Amigos", 1)[0]
    assert "spendEnergy" not in sprint_wrapper

    gate = javascript.split("async function requestPlayableBlockBuild()", 1)[1].split(
        "function buildPlayableBlock(", 1
    )[0]
    assert gate.index(
        "const hasEnergy = await spendEnergy(roundId, roundRealm, roundMiner);"
    ) < gate.index(
        "buildPlayableBlock();"
    )
    assert "if (hasEnergy === null)" in gate
    assert "if (hasEnergy === false)" in gate
    assert "showPendingEnergyState();" in gate

    builder = javascript.split("function buildPlayableBlock(", 1)[1].split(
        "function injectWordInGrid(", 1
    )[0]
    assert "spendEnergy" not in builder
    assert javascript.count("void requestPlayableBlockBuild();") >= 4


def test_partial_energy_mutations_preserve_status_metadata() -> None:
    """Respostas de spend/buy não podem apagar max e next_refill_at."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    spend_energy = javascript.split(
        "async function spendEnergy(roundId, realmId, username)", 1
    )[1].split(
        "async function buyEnergy()", 1
    )[0]
    buy_energy = javascript.split("async function buyEnergy()", 1)[1].split(
        "// Event listeners do Energy System", 1
    )[0]

    assert "function mergeEnergyState(payload)" in javascript
    assert "energyState = mergeEnergyState(payload);" in spend_energy
    assert "energyState = mergeEnergyState(await response.json());" in buy_energy


def test_energy_rounds_are_idempotent_and_compensated() -> None:
    """Round abortado deve ser estornado com retry durável e UUID estável."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    gate = javascript.split("async function requestPlayableBlockBuild()", 1)[1].split(
        "function buildPlayableBlock(", 1
    )[0]
    builder = javascript.split("function buildPlayableBlock(", 1)[1].split(
        "function injectWordInGrid(", 1
    )[0]
    spend = javascript.split("async function spendEnergy(", 1)[1].split(
        "async function buyEnergy()", 1
    )[0]

    assert "const ENERGY_REFUNDS_STORAGE_KEY" in javascript
    assert "function createEnergyRoundId()" in javascript
    assert "async function queueEnergyRefund(" in javascript
    assert "async function flushPendingEnergyRefunds()" in javascript
    assert "round_id=${encodeURIComponent(roundId)}" in spend
    assert gate.count("await queueEnergyRefund(roundId") >= 2
    assert "const blockStarted = buildPlayableBlock();" in gate
    assert "return false;" in builder
    assert "return true;" in builder
    assert "await flushPendingEnergyRefunds();" in javascript


def test_uncertain_energy_spend_survives_reload_before_refund() -> None:
    """Timeout após débito deve preservar UUID e ser resolvido após reload."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "const ENERGY_PENDING_SPENDS_STORAGE_KEY" in javascript
    assert "const pendingEnergySpends = loadPendingEnergySpends();" in javascript
    assert "function reservePendingEnergySpend(" in javascript
    assert "function clearPendingEnergySpend(" in javascript
    assert "async function recoverPendingEnergySpends()" in javascript
    assert "pendingEnergySpends.set(roundId" in javascript
    assert "await recoverPendingEnergySpends();" in javascript

    gate = javascript.split("async function requestPlayableBlockBuild()", 1)[1].split(
        "function buildPlayableBlock(", 1
    )[0]
    assert "reservePendingEnergySpend(roundRealm, roundMiner)" in gate
    assert gate.count("clearPendingEnergySpend(roundId)") >= 3

    recovery = javascript.split("async function recoverPendingEnergySpends()", 1)[1].split(
        "async function flushPendingEnergyRefunds()", 1
    )[0]
    assert "energy/spend?" in recovery
    assert "round_id=${encodeURIComponent(roundId)}" in recovery
    assert "await queueEnergyRefund(roundId" in recovery


def test_energy_spend_uses_the_round_realm_and_player_snapshot() -> None:
    """Troca de rede durante o fetch não pode debitar nem renderizar outro realm."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    gate = javascript.split("async function requestPlayableBlockBuild()", 1)[1].split(
        "function buildPlayableBlock(", 1
    )[0]
    spend = javascript.split(
        "async function spendEnergy(roundId, realmId, username)", 1
    )[1].split("async function buyEnergy()", 1)[0]

    assert "await spendEnergy(roundId, roundRealm, roundMiner)" in gate
    assert "networkApiUrl(" in spend
    assert "activeNetworkApiUrl(" not in spend
    assert "encodeURIComponent(username)" in spend
    assert "realmId === activeRealmId && username === minerName" in spend


def test_saved_session_re_resolves_realm_and_restores_identity_inputs() -> None:
    """F5 deve preservar realm, nome e pool mesmo se o catálogo iniciar vazio."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    restore = javascript.split("/* Fase 1: Tenta restaurar sessão anterior", 1)[1].split(
        "void registerPwa();", 1
    )[0]
    start_session = javascript.split("async function startSession(", 1)[1].split(
        "function processTransactionReceived(", 1
    )[0]

    assert "document.getElementById('miner-input').value = minerName;" in restore
    assert "document.getElementById('pool-tag-input').value = poolName;" in restore
    assert "await startSession(activeRealmId);" in restore
    assert "await loadPlayerState(activeRealmId, minerName);" not in restore
    assert "const requestedRealmId = realmIdOverride || networkSelectEl.value;" in start_session
    assert start_session.count("selectedNetwork = networkCatalog.get(requestedRealmId);") >= 2
    validated_selection = start_session.split(
        "if (!selectedNetwork?.playable) {\n        updateNetworkChoice();", 1
    )[1].split("const input = document.getElementById('miner-input').value.trim();", 1)[0]
    assert "networkSelectEl.value = selectedNetwork.realm_id;" in validated_selection


def test_word_validation_uses_official_coordinates_and_safe_fill() -> None:
    """Ocorrência textual incidental não pode validar nem bloquear outro alvo."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    inject = javascript.split("function injectWordInGrid(", 1)[1].split(
        "function renderWordBank()", 1
    )[0]
    selection = javascript.split("function endSelection()", 1)[1].split(
        "function finishSelectionFromPointer", 1
    )[0]
    sprint = javascript.split("function renderWordBank()", 1)[1].split(
        "function renderBankWord(", 1
    )[0]

    assert inject.count("coords") >= 4
    assert "function selectionMatchesOfficialPath(" in javascript
    assert "selectionMatchesOfficialPath(w, selectedCells)" in selection
    assert "w.word === selectedWord" not in selection
    assert "function fillGridWithoutIncidentalWords(" in javascript
    assert "fillGridWithoutIncidentalWords()" in javascript
    assert "new Set(" in sprint
    assert "injectWordInGrid(" in sprint
    assert "blockWords.push({" not in sprint


def test_market_sell_uses_inventory_shape_and_username_contract() -> None:
    """Dropdown e POST de venda devem seguir exatamente o contrato backend."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    inventory_loader = javascript.split("async function loadMarketInventory()", 1)[1].split(
        "function renderMarketList()", 1
    )[0]
    seller = javascript.split("async function sellMarketPowerup()", 1)[1].split(
        "// Tabs do mercado", 1
    )[0]

    assert "const payload = await response.json();" in inventory_loader
    assert "marketInventory = payload.inventory || {};" in inventory_loader
    assert "Object.entries(marketInventory)" in javascript
    assert "username: minerName" in seller
    assert "seller: minerName" not in seller


def test_market_buy_and_history_match_backend_contract() -> None:
    """Compra deve identificar o listing e histórico deve consumir `sales`."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    buyer = javascript.split("async function buyMarketListing(", 1)[1].split(
        "async function sellMarketPowerup()", 1
    )[0]
    history = javascript.split("function renderMarketHistory()", 1)[1].split(
        "function populateSellDropdown()", 1
    )[0]

    assert "username: minerName" in buyer
    assert "listing_id: listingId" in buyer
    assert "buyer: minerName" not in buyer
    assert "marketHistoryData?.sales || []" in history
    assert "marketHistoryData?.history" not in history


def test_market_sale_event_refreshes_online_seller_state() -> None:
    """Venda concluída por outro jogador deve atualizar o vendedor conectado."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "'market_sale'" in javascript
    assert "if (data.action === 'market_sale')" in javascript
    market_event = javascript.split("if (data.action === 'market_sale')", 1)[1].split(
        "return;", 1
    )[0]
    assert "data.seller === minerName" in market_event
    assert "loadMarketList()" in market_event
    assert "loadMarketHistory()" in market_event
    assert "loadPlayerState(activeRealmId, minerName)" in market_event


def test_season_premium_button_tracks_confirmed_server_state() -> None:
    """Premium confirmado permanece bloqueado; falha restaura a UI clicável."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    purchase = javascript.split("async function buySeasonPremium()", 1)[1].split(
        "// Event listeners do Season Pass", 1
    )[0]

    assert "let purchaseSucceeded = false;" in purchase
    assert "purchaseSucceeded = true;" in purchase
    assert "btnBuySeasonPremiumEl.disabled = purchaseSucceeded" in purchase
    assert "btnBuySeasonPremiumEl.disabled = false;" not in purchase


def test_crate_render_is_side_effect_free_and_bonus_notifies_on_change() -> None:
    """Polling do inventário não deve repetir o toast de bônus lendário."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    render = javascript.split("function updateCrateUI()", 1)[1].split(
        "async function openCrate", 1
    )[0]
    opening = javascript.split("async function openCrate", 1)[1].split(
        "function showCrateResult", 1
    )[0]

    assert "showNotification" not in render
    assert "const previousLegendaryBonus = crateState.legendary_bonus" in opening
    assert "result.legendary_bonus > previousLegendaryBonus" in opening
    assert "Bônus Legendário ativo" in opening


def test_chat_and_market_loaders_cache_success_per_session() -> None:
    """Abrir painéis ou alternar tabs não deve repetir fetch já concluído."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    chat = javascript.split("async function loadChatHistory()", 1)[1].split(
        "function renderChatMessages()", 1
    )[0]
    market = javascript.split("// Fase 9: Mercado", 1)[1].split(
        "// Fase 8: Eventos Globais", 1
    )[0]
    reset = javascript.split("function resetSessionModules()", 1)[1].split(
        "function teardownSession()", 1
    )[0]

    assert "chatHistoryLoaded = true;" in chat
    assert "if (chatHistoryLoaded || chatHistoryLoading) return;" in chat
    assert "const marketLoadedSections = new Set();" in javascript
    assert "const marketLoadingSections = new Set();" in javascript
    # .add() registra o cache de sucesso de cada seção (browse/history/inventory).
    for section in ("browse", "history", "inventory"):
        assert f"marketLoadedSections.add('{section}');" in market
        assert f"marketLoadingSections.has('{section}')" in market
    # .has() guarda contra double-load apenas onde a seção é reaberta por UI
    # viva (browse/inventory alimentam marketLoaded). 'history' não tem guard
    # .has() porque o bloco de tabs do mercado (que o usava) era código morto
    # e foi removido — o cache de 'history' ainda é registrado via .add().
    for section in ("browse", "inventory"):
        assert f"marketLoadedSections.has('{section}')" in market
    assert "marketLoadedSections.clear();" in reset
    assert "marketLoadingSections.clear();" in reset
    assert "btnRefreshMarketEl.addEventListener('click', loadMarketList);" in market


def test_decoder_rate_limit_restores_launcher() -> None:
    """Resposta 429 não pode deixar o Decoder permanentemente inacessível."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    decoder = javascript.split("async function startDecoderGame()", 1)[1].split(
        "function updateDecoderTimer()", 1
    )[0]
    rate_limit = decoder.split("if (response.status === 429)", 1)[1].split(
        "throw new Error", 1
    )[0]

    assert "decoderActive = false;" in rate_limit
    assert "decoderLaunchBtnEl.classList.remove('hidden');" in rate_limit
    assert rate_limit.index("classList.remove('hidden')") < rate_limit.index("return;")


def test_rest_loaders_reject_stale_session_responses() -> None:
    """Resposta de realm/jogador anterior nunca pode mutar a sessão atual."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    assert "function captureSessionContext(" in javascript
    assert "function isSessionContextCurrent(" in javascript

    boundaries = {
        "loadPlayerState": "function updateStoreUI",
        "loadChatHistory": "function renderChatMessages",
        "loadStakingStatus": "function updateStakingUI",
        "loadSkillTree": "function renderSkillTree",
        "loadEnergyState": "function updateEnergyUI",
        "loadSeasonData": "function addSeasonXP",
        "loadMarketList": "async function loadMarketHistory",
        "loadMarketHistory": "async function loadMarketInventory",
        "loadMarketInventory": "function renderMarketList",
        "loadCrateInventory": "function updateCrateUI",
    }
    for function_name, next_boundary in boundaries.items():
        body = javascript.split(f"async function {function_name}", 1)[1].split(
            next_boundary, 1
        )[0]
        assert "const sessionContext = captureSessionContext(" in body, function_name
        assert "if (!isSessionContextCurrent(sessionContext)) return;" in body, function_name

    skill_loader = javascript.split("async function loadSkillTree()", 1)[1].split(
        "function renderSkillTree", 1
    )[0]
    stale_finally = skill_loader.split("finally", 1)[1]
    assert "if (isSessionContextCurrent(sessionContext))" in stale_finally
    guarded_cleanup = stale_finally.split(
        "if (isSessionContextCurrent(sessionContext))", 1
    )[1]
    assert "skillTreeLoading = false;" in guarded_cleanup


def test_energy_recovery_classifies_terminal_errors_and_resolves_uncertain_spend() -> None:
    """Retries preservam exatamente-uma-vez e não deixam UI stale/enganosa."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    refunds = javascript.split("async function flushPendingEnergyRefunds()", 1)[1].split(
        "async function queueEnergyRefund", 1
    )[0]
    spend = javascript.split("async function spendEnergy(", 1)[1].split(
        "async function buyEnergy", 1
    )[0]
    gate = javascript.split("async function requestPlayableBlockBuild()", 1)[1].split(
        "function startNetworkRace", 1
    )[0]

    assert "response.status >= 400 && response.status < 500" in refunds
    assert "pendingEnergyRefunds.delete(roundId);" in refunds
    assert "if (attempt === 0) continue;" in spend
    assert "await loadEnergyState(false);" in spend
    assert "if (hasEnergy === null)" in gate
    uncertain = gate.split("if (hasEnergy === null)", 1)[1].split(
        "if (hasEnergy === false)", 1
    )[0]
    assert "showPendingEnergyState" not in uncertain


def test_boss_final_word_runs_common_rewards_without_normal_result_modal() -> None:
    """Derrotar o Boss não pode pular XP, linha, persistência ou abrir dois modais."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    selection = javascript.split("function endSelection()", 1)[1].split(
        "function finishSelectionFromPointer", 1
    )[0]
    defeat = selection.split("if (bossHp <= 0 && !bossDefeatHandled)", 1)[1].split(
        "/* Fase 6: MEV Secreto", 1
    )[0]
    completion = selection.split(
        "if (wordsFoundInBlock === blockWords.length)", 1
    )[1].split("} else {\n        /* Fase 1: Slashing", 1)[0]

    assert "return;" not in defeat
    assert "currentRoundEarnings += Math.floor(points);" in selection
    assert "if (bossDefeatHandled)" in completion
    assert "roundNumber++;" in completion
    assert "maxRoundEarningsTotal = Math.max(" in completion
    assert "pushStats({ max_round_earnings: maxRoundEarningsTotal })" in completion
    assert "trackBlockCompleted();" in completion
    assert "claimFreeCrates();" in completion
    assert "else" in completion
    assert "showResult(true" not in completion


def test_every_boss_word_deals_damage_including_mev() -> None:
    """Boss com HP igual ao total de palavras deve ser sempre derrotável."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    selection = javascript.split("function endSelection()", 1)[1].split(
        "function finishSelectionFromPointer", 1
    )[0]
    boss_damage = selection.split("/* Boss Battles:", 1)[1].split(
        "/* Fase 6: MEV Secreto", 1
    )[0]

    assert "if (isBossActive)" in boss_damage
    assert "!match.isMev" not in boss_damage
    assert "bossHp = Math.max(0, bossHp - 1);" in boss_damage


def test_boss_and_sprint_respect_modal_lifecycle_and_skill_time() -> None:
    """Eventos especiais não se sobrepõem e recebem o bônus por rodada."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    boss = javascript.split("function handleBossBlock(", 1)[1].split(
        "function updateBossOverlay", 1
    )[0]
    block_mined = javascript.split('else if (data.action === "block_mined")', 1)[1].split(
        "if (data.action === 'leaderboard_reset')", 1
    )[0]

    assert "result-modal" in boss
    assert "classList.contains('active')" in boss
    assert "networkTimeLimit = bossTimer + skillTimeBonus;" in javascript
    # Fase 4.3: cap do sprintTimeLimit em SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS
    assert "SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS" in javascript
    assert "sprintTimeLimit = Math.min(" in javascript
    assert "if (sprintRoundActive)" in block_mined
    sprint_branch = block_mined.split("if (sprintRoundActive)", 1)[1].split(
        "else if (isPlaying)", 1
    )[0]
    assert "endSprintRound('block_mined')" in sprint_branch
    assert "showOrphanBlockSalvage" not in sprint_branch


def test_sprint_submit_mirrors_backend_reward_once_in_local_state() -> None:
    """Reward confirmado no backend deve aparecer imediatamente no HUD local."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    submit = javascript.split("async function submitSprintResult(", 1)[1].split(
        "function showSprintResult(", 1
    )[0]

    assert "if (generation !== sessionGeneration) return;" in submit
    assert "balanceSatoshis += data.reward;" in submit
    assert "currentRoundEarnings += data.reward;" in submit
    assert "saveSessionState();" in submit
    assert submit.index("balanceSatoshis += data.reward;") < submit.index("showSprintResult(data);")


def test_level_time_bonus_is_idempotent_and_separate_from_saved_hardware_bonus() -> None:
    """Reload/update de nível não acumula bônus nem contamina o save de hardware."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    level_ui = javascript.split("function updateLevelUI()", 1)[1]
    level_loader = javascript.split("async function loadLevelState()", 1)[1].split(
        "function updateLevelUI()", 1
    )[0]

    assert "let levelTimeBonus = 0;" in javascript
    assert "function getNetworkTimeBonus()" in javascript
    assert "levelTimeBonus = Number(bonuses?.time_bonus_seconds) || 0;" in level_ui
    assert "window.NETWORK_TIME_BONUS" not in javascript
    assert "networkTimeBonus + levelTimeBonus" in javascript
    assert "const sessionContext = captureSessionContext(" in level_loader
    assert "if (!isSessionContextCurrent(sessionContext)) return;" in level_loader


def test_phase5_dead_frontend_symbols_are_removed_without_live_stats() -> None:
    """Limpeza remove somente símbolos sem leitores/call-sites reais."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    for dead_symbol in (
        "function toggleChatPanel(",
        "isRbfMode",
        "eventPreannounceTimeout",
        "function trackPoolRank1(",
        "function loadSprintLeaderboard(",
        "function renderSprintLeaderboard(",
    ):
        assert dead_symbol not in javascript
    assert "let poolRank1 = 0;" in javascript
    assert "pool_rank_1" in javascript


def test_chat_keeps_oldest_first_order_and_caps_array_and_dom() -> None:
    """Histórico, echo local e mensagens de sistema compartilham ordem/teto."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    history = javascript.split("async function loadChatHistory()", 1)[1].split(
        "function renderChatMessages()", 1
    )[0]
    sender = javascript.split("async function sendChatMessage()", 1)[1].split(
        "function insertChatToken", 1
    )[0]
    system = javascript.split("function appendSystemMessage(", 1)[1].split(
        "function scrollToBottom", 1
    )[0]

    assert "data.messages.slice(0, CHAT_MAX_MESSAGES).reverse()" in history
    assert "chatMessages.push(data.message);" in sender
    assert "chatMessages.unshift" not in sender
    assert "chatMessages.shift();" in sender
    assert "function appendNodeToChat(" in javascript
    assert "appendNodeToChat(msgEl);" in system


def test_chat_websocket_handler_deduplicates_and_appends_remote_messages() -> None:
    """Broadcast de chat deve entrar no histórico sem duplicar o echo do remetente."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    handler = javascript.split("if (data.action === 'chat_message')", 1)[1].split(
        'if (data.action === "transaction_received"', 1
    )[0]

    assert "chatMessages.some(" in handler
    assert "m.username === data.username" in handler
    assert "m.message === data.message" in handler
    assert "m.timestamp === data.timestamp" in handler
    assert "chatMessages.push({" in handler
    assert "appendChatMessage(" in handler


def test_energy_label_and_boss_routing_keep_single_owners() -> None:
    """JS restaura label original e Boss nunca cai no buffer normal."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    energy = javascript.split("async function buyEnergy()", 1)[1].split(
        "// Event listeners do Energy System", 1
    )[0]
    boss_route = javascript.split(
        "// Boss Battles: roteia transações para o buffer do boss", 1
    )[1].split("if (txBuffer.length < WORDS_PER_BLOCK)", 1)[0]

    assert "const originalContent = btnBuyEnergyEl.innerHTML;" in energy
    assert "btnBuyEnergyEl.innerHTML = originalContent;" in energy
    assert "btnBuyEnergyEl.textContent = '2,000 SATS'" not in energy
    assert "if (handleBossTransaction(data))" not in boss_route
    assert "handleBossTransaction(data);" in boss_route
    assert "return;" in boss_route


def test_external_text_is_not_interpolated_raw_into_frontend_html() -> None:
    """Mercado usa DOM e sinks restantes escapam texto externo explicitamente."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    market = javascript.split("function renderMarketList()", 1)[1].split(
        "function renderMarketHistory()", 1
    )[0]
    dropdown = javascript.split("function populateSellDropdown()", 1)[1].split(
        "async function buyMarketListing", 1
    )[0]

    assert "marketBrowseEl.innerHTML = html" not in market
    assert "${listing.listing_id}" not in market
    # Fase B4/C2: texto do vendedor usa ternário (seu listing vs. vendedor)
    assert "seller.textContent = isOwn ? 'Seu listing' : `Vendedor: ${listing.seller}`;" in market
    assert "buyButton.dataset.listingId = String(listing.listing_id);" in market
    assert "select.innerHTML +=" not in dropdown
    assert "option.textContent =" in dropdown

    for raw_interpolation in (
        "${def.name}",
        "${def.description}",
        "${ach.name}",
        "${ach.description}",
        "${card.block_hash || '-'}",
    ):
        assert raw_interpolation not in javascript
    assert '<div class="crate-result-item">${itemName}</div>' not in javascript
    assert '<div class="crate-result-item">${escapeHtml(itemName)}</div>' in javascript
    assert "function escapeHtml(" in javascript


def test_staking_history_whitelists_type_and_uses_text_nodes() -> None:
    """Enum externo não entra em classe/HTML sem normalização."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    history = javascript.split("async function loadStakingHistory()", 1)[1].split(
        "async function performStake()", 1
    )[0]

    assert "const safeType =" in history
    assert "stake-${entry.type}" not in history
    assert "item.innerHTML" not in history
    assert "typeElement.textContent = typeLabel;" in history
    assert "amountElement.textContent = amountText;" in history
    assert "dateElement.textContent = date;" in history


def test_skill_tree_bonuses_are_idempotent_and_feed_real_game_formulas() -> None:
    """Bônus backend devem sobreviver ao reload sem acumular e afetar o jogo real."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    loader = javascript.split("async function loadSkillTree()", 1)[1].split(
        "function renderSkillTree()", 1
    )[0]
    apply_bonuses = javascript.split("function applySkillBonuses(bonuses)", 1)[1].split(
        "registerSessionInitializer('skills'", 1
    )[0]
    hint_price = javascript.split("function getHintPrice()", 1)[1].split(
        "function applyAchievementBonus", 1
    )[0]
    builder = javascript.split("function buildPlayableBlock(", 1)[1].split(
        "function injectWordInGrid(", 1
    )[0]
    selection = javascript.split("function endSelection()", 1)[1].split(
        "function finishSelectionFromPointer", 1
    )[0]

    assert "applySkillBonuses(skillTreeData.bonuses);" in loader
    for key in (
        "mining_time_bonus",
        "search_discount_percent",
        "lightning_reward_percent",
    ):
        assert key in apply_bonuses
    assert "baseTimeLimit = 60 +" in apply_bonuses
    assert "hintCost = Math.round(HINT_PRICE *" in apply_bonuses
    assert "skillRewardBonus =" in apply_bonuses
    assert "+=" not in apply_bonuses
    assert "*=" not in apply_bonuses
    assert "networkTimeLimit += baseTimeLimit - 60;" in builder
    assert "hintCost * (1 - discount)" in hint_price
    assert "effectiveBaseReward * (1 + skillRewardBonus)" in selection


def test_sprint_uses_one_idempotent_completion_path_and_real_word_count() -> None:
    """Conclusão e timeout Sprint devem submeter uma vez sem modal normal concorrente."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    selection = javascript.split("function endSelection()", 1)[1].split(
        "function finishSelectionFromPointer", 1
    )[0]
    sprint = javascript.split("async function startSprintRound()", 1)[1].split(
        "function showSprintResult(", 1
    )[0]
    reset = javascript.split("function resetSessionModules()", 1)[1].split(
        "function teardownSession(", 1
    )[0]

    assert "let sprintRoundActive = false;" in javascript
    assert "let sprintRoundEnding = false;" in javascript
    assert "sprintWordsFound = wordsFoundInBlock;" in selection
    assert "if (sprintRoundActive)" in selection
    assert "void endSprintRound('completed');" in selection
    assert "void endSprintRound('timeout');" in sprint
    assert "async function endSprintRound(reason" in javascript
    assert "if (!sprintRoundActive || sprintRoundEnding) return;" in javascript
    assert "if (sprintRoundActive || sprintRoundEnding || sprintRoundStarting) return;" in sprint
    assert "sprintRoundStarting = true;" in sprint
    assert "sprintRoundStarting = false;" in sprint
    assert "Math.max(0.001, Math.min(sprintTimeLimit" in sprint
    assert "timerEl.remove()" not in sprint
    assert "generation !== sessionGeneration" in sprint
    assert "sprintRoundActive = false;" in reset
    assert "sprintRoundEnding = false;" in reset


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
    # FASE 1920 (25/08): o bloco de "tela grande" moveu de 1920px para 2200px —
    # 1080p é resolução padrão/média, então o aumento de controles só vale em
    # telas realmente grandes (2200px+ / 42").
    ultrawide = css.split("@media (min-width: 2200px)", 1)[1]

    assert ".sidebar-right :is(" in ultrawide
    assert "font-size: 8px;" in ultrawide
    assert ".sidebar-right .btn-action-small" in ultrawide
    assert ".sidebar-right .input-mecha" in ultrawide
    assert ".mechanic-subnav-btn" in ultrawide
    assert ".chat-emoji-btn" in ultrawide
    assert "min-height: 44px;" in ultrawide
    assert "min-height: 52px;" in ultrawide


# ==========================================================================
# Fase 4 — Consistência mecânica (regressão)
# ==========================================================================


def test_boss_round_consumes_energy_like_normal_rounds() -> None:
    """Fase 4.1: o boss block consome 1 energia (decisão: consistência).

    Antes da correção, buildBossPlayableBlock era chamado diretamente e a
    rodada do boss era gratuita. Agora um gate (requestBossPlayableBlockBuild)
    reserva o spend, chama spendEnergy e trata os resultados com refund.
    """
    javascript = GAME_JS.read_text(encoding="utf-8")

    # O gate existe e é chamado no fluxo do boss
    assert "async function requestBossPlayableBlockBuild()" in javascript
    assert "void requestBossPlayableBlockBuild();" in javascript

    # O gate consome energia (mesmo mecanismo das rodadas normais)
    gate = javascript.split("async function requestBossPlayableBlockBuild()", 1)[1].split(
        "\n}", 1
    )[0]
    assert "reservePendingEnergySpend(" in gate
    assert "await spendEnergy(" in gate
    assert "queueEnergyRefund(" in gate

    # Sem energia → boss descartado (resetBossState)
    assert "resetBossState();" in gate

    # Fase 4.1 (auditoria): no descarte do boss, o txBuffer é limpo — as 10
    # palavras do boss não valem para a rodada normal (que exige 6). Sem isso,
    # o jogador ficava travado até o próximo block_mined.
    assert "txBuffer = [];" in gate

    # buildBossPlayableBlock retorna true/false (o gate depende disso)
    build = javascript.split("function buildBossPlayableBlock()", 1)[1].split(
        "\n}", 1
    )[0]
    assert "return false;" in build
    assert "return true;" in build


def test_boss_grid_size_read_from_backend() -> None:
    """Fase 4.2: o frontend lê data.boss_grid_size em vez de hardcodear 15."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    # Estado inicial
    assert "let bossGridSize = 15;" in javascript
    # Lido do evento boss_block
    assert "bossGridSize = data.boss_grid_size || 15;" in javascript
    # Usado no build da grade (não mais hardcode 15)
    assert "currentGridSize = bossGridSize;" in javascript
    # O hardcode antigo foi removido do buildBossPlayableBlock
    build = javascript.split("function buildBossPlayableBlock()", 1)[1].split(
        "\n}", 1
    )[0]
    assert "currentGridSize = 15;" not in build


def test_collection_bonus_applied_to_rewards() -> None:
    """Fase 4.6: o bônus de coleção de cards é aplicado nas recompensas.

    O backend calcula collection_bonus em _get_player_cards; o frontend soma
    o value de cada raridade completa em getCollectionBonus() e aplica no
    applyAchievementBonus (mesmo ponto do bônus de conquistas).
    """
    javascript = GAME_JS.read_text(encoding="utf-8")

    # Helper existe e lê collection_bonus
    assert "function getCollectionBonus()" in javascript
    helper = javascript.split("function getCollectionBonus()", 1)[1].split(
        "\n}", 1
    )[0]
    assert "cardsData.collection_bonus" in helper
    assert "entry.complete" in helper

    # Integrado ao applyAchievementBonus
    apply = javascript.split("function applyAchievementBonus(points)", 1)[1].split(
        "\n}", 1
    )[0]
    assert "getCollectionBonus()" in apply


# ---------------------------------------------------------------------------
# Fase 5: economia/progressão — saldo no backend, streak sem erro, rollover
# ---------------------------------------------------------------------------


def test_balance_earn_spend_helpers_exist() -> None:
    """Fase 5.1/5.3: o frontend tem earnBalance/spendBalance (backend é a
    fonte de verdade do saldo)."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "async function earnBalance(" in javascript
    assert "async function spendBalance(" in javascript

    # earnBalance chama o endpoint /earn
    earn = javascript.split("async function earnBalance(", 1)[1].split("\n}", 1)[0]
    assert "/earn" in earn

    # spendBalance chama o endpoint /spend e retorna null em falha
    spend = javascript.split("async function spendBalance(", 1)[1].split("\n}", 1)[0]
    assert "/spend" in spend


def test_player_state_uses_explicit_balance_initialization_marker() -> None:
    """Saldo zero autoritativo deve substituir o local, não disparar nova migração."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    loader = javascript.split("async function loadPlayerState(", 1)[1].split(
        "/**\n * Atualiza preços", 1
    )[0]

    assert "if (state.balance_initialized)" in loader
    assert "balanceSatoshis = state.balance;" in loader
    assert "else if (balanceSatoshis > 0)" in loader
    assert "state.balance > 0" not in loader


def test_level_ui_uses_backend_progress_after_level_up() -> None:
    """O frontend não pode substituir o progresso remanescente por 0% ou 100%."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    add_xp = javascript.split("async function addXP(", 1)[1].split(
        "// Calcula XP ganho", 1
    )[0]

    assert "levelState.xp_progress = result.xp_progress;" in add_xp
    assert "result.leveled_up ? 100" not in add_xp


def test_pvp_live_panel_and_handlers_update_score_and_timer() -> None:
    """Eventos PvP de score/timer precisam produzir estado visível em COMPETIR."""
    html = INDEX_HTML.read_text(encoding="utf-8")
    javascript = GAME_JS.read_text(encoding="utf-8")

    for element_id in (
        "pvp-live-panel",
        "pvp-status",
        "pvp-challenger-name",
        "pvp-challenger-score",
        "pvp-challenged-name",
        "pvp-challenged-score",
        "pvp-timer-value",
    ):
        assert f'id="{element_id}"' in html

    score_handler = javascript.split("if (data.action === 'pvp_score_update')", 1)[1].split(
        "if (data.action === 'pvp_end')", 1
    )[0]
    timer_handler = javascript.split("if (data.action === 'pvp_timer')", 1)[1].split(
        "// Fase 11: Online Status", 1
    )[0]
    assert "updatePvpScore(data);" in score_handler
    assert "updatePvpTimer(data.timer);" in timer_handler


def test_purchases_debit_backend_before_local_apply() -> None:
    """Fase 5.1: as compras (hint/hardware/lightning) só debitam localmente
    se o backend confirmar o débito (sem compra de graça)."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    for fn in ("buyHint", "buyHardware", "buyLightning"):
        body = javascript.split(f"function {fn}()", 1)[1].split("\n}", 1)[0]
        assert "spendBalance(" in body, f"{fn} não valida o débito no backend"
        # O saldo local é espelhado do backend (confirmed) após a confirmação
        assert "balanceSatoshis = confirmed;" in body, f"{fn} não espelha o saldo do backend"
        # Recusa do backend aborta a compra
        assert "confirmed === null" in body, f"{fn} não trata a recusa do backend"


def test_spend_balance_retries_transient_failures_with_same_idempotency_key() -> None:
    """Resposta perdida não pode cobrar sem permitir que a compra seja concluída."""
    javascript = GAME_JS.read_text(encoding="utf-8")
    spend = javascript.split("async function spendBalance(", 1)[1].split(
        "/**\n * Fase 3: Carrega estado", 1
    )[0]

    assert "const MAX_ATTEMPTS = 3;" in spend
    assert "for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)" in spend
    assert "response.status !== 429" in spend
    assert "500 * attempt" in spend
    # A idempotency key (txId) vem do caller e é reutilizada em TODAS as
    # tentativas — o retry não pode gerar uma 2ª chave (2ª cobrança).
    assert "tx_id: txId" in spend
    assert "Math.random" not in spend  # nenhuma regeneração de chave no loop


def test_purchase_callers_guard_reentry_and_use_unique_tx_ids() -> None:
    """Cliques concorrentes não podem aplicar uma segunda compra idempotente grátis."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    expectations = {
        "buyHardware": "hardwarePurchaseInFlight",
        "buyLightning": "lightningPurchaseInFlight",
    }
    for function_name, guard in expectations.items():
        body = javascript.split(f"async function {function_name}()", 1)[1].split(
            "\n}", 1
        )[0]
        assert f"if ({guard}) return;" in body
        assert f"{guard} = true;" in body
        assert f"{guard} = false;" in body
        assert "Math.random().toString(36).slice(2, 8)" in body

    rbf = javascript.split("const rbfHandler = async () =>", 1)[1].split(
        "setNextButtonAction(rbfHandler);", 1
    )[0]
    assert "if (rbfPurchaseInFlight) return;" in rbf
    assert "rbfPurchaseInFlight = true;" in rbf
    assert "rbfPurchaseInFlight = false;" in rbf
    assert "Math.random().toString(36).slice(2, 8)" in rbf


def test_rbf_and_slashing_debit_backend() -> None:
    """Fase 5.1: RBF e slashing debitam no backend antes de aplicar localmente."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    # RBF: o handler é async e chama spendBalance
    assert "const rbfHandler = async () =>" in javascript
    rbf_block = javascript.split("const rbfHandler = async () =>", 1)[1].split(
        "rbfBtn.addEventListener", 1
    )[0]
    assert "spendBalance(" in rbf_block

    # Slashing: penalidade debitada no backend (txId spend-slash-)
    assert "spendBalance(penalty, txId)" in javascript
    assert "spend-slash-" in javascript


def test_words_without_error_streak_tracked() -> None:
    """Fase 5.4: a streak de palavras sem erro é rastreada e enviada ao
    backend (reseta a cada erro)."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    assert "let wordsWithoutErrorStreak = 0;" in javascript
    # Incrementa ao encontrar palavra
    track = javascript.split("function trackWordFound(", 1)[1].split("\n}", 1)[0]
    assert "wordsWithoutErrorStreak++" in track
    assert "words_without_error: wordsWithoutErrorStreak" in track
    # Reseta a cada erro
    assert "wordsWithoutErrorStreak = 0;" in javascript
    assert "void pushStats({ words_without_error: 0 });" in javascript


def test_season_rollover_ui_shows_claim_period() -> None:
    """Fase 5.5: a UI da temporada exibe o prazo de claim quando a
    temporada está encerrada."""
    javascript = GAME_JS.read_text(encoding="utf-8")

    render = javascript.split("function renderSeasonUI()", 1)[1].split("\n}", 1)[0]
    assert "season_ended" in render
    assert "claim_period_active" in render
    assert "claim_deadline" in render
    assert "para reclamar" in render

