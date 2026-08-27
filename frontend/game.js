/**
 * MEMPOOL MINER: Proof-of-Search com grade dinâmica e upgrade L2 simulado.
 */

const UI_ICON_SPRITE = 'icons/ui-sprite.svg';
const UI_ICON_NAMES = new Set([
    'antenna', 'bolt', 'boss', 'check', 'circle', 'close', 'coin', 'combo',
    'controller', 'crate', 'cross', 'crown', 'cube', 'fire', 'gem', 'gift',
    'level', 'link', 'magnet', 'orb', 'pickaxe', 'scanner', 'sprint', 'star',
    'storm', 'swords', 'target', 'timer', 'trophy', 'warning', 'wave'
]);

/**
 * Retorna markup seguro para um símbolo do sprite local.
 */
function iconSvg(name, className = 'ui-icon') {
    const safeName = UI_ICON_NAMES.has(name) ? name : 'circle';
    const safeClass = /^[a-z0-9 _-]+$/i.test(className) ? className : 'ui-icon';
    return `<svg class="${safeClass}" aria-hidden="true" focusable="false"><use href="${UI_ICON_SPRITE}#icon-${safeName}"></use></svg>`;
}

/**
 * Substitui o conteúdo de um elemento por um ícone SVG local.
 */
function setSvgIcon(element, name, className = 'ui-icon') {
    if (!element) return;
    const safeName = UI_ICON_NAMES.has(name) ? name : 'circle';
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    svg.setAttribute('class', className);
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    use.setAttribute('href', `${UI_ICON_SPRITE}#icon-${safeName}`);
    svg.appendChild(use);
    element.replaceChildren(svg);
}

/**
 * Escapa texto externo antes de inseri-lo em templates HTML controlados.
 */
function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}

const ACHIEVEMENT_CATEGORIES = [
    { key: 'all', label: 'Todas', iconName: null },
    { key: 'volume', label: 'Volume', iconName: 'pickaxe' },
    { key: 'raridade', label: 'Raridade', iconName: 'star' },
    { key: 'velocidade', label: 'Velocidade', iconName: 'bolt' },
    { key: 'exploracao', label: 'Exploração', iconName: 'cube' },
    { key: 'social', label: 'Social', iconName: 'trophy' }
];

function achievementIconName(category) {
    return ACHIEVEMENT_CATEGORIES.find(item => item.key === category)?.iconName || 'trophy';
}

/**
 * Alterna entre as cinco áreas principais e mantém toda a navegação sincronizada.
 * @param {string} tabName - jogo, upgrades, competir, perfil ou social.
 */
function showTab(tabName) {
    const targetTab = document.getElementById(`tab-${tabName}`);
    if (!targetTab) return;

    document.querySelectorAll('.tab-pane').forEach(tab => {
        const active = tab === targetTab;
        tab.classList.toggle('active', active);
        tab.hidden = !active;
    });
    document.querySelectorAll('.mecha-nav-group .mecha-btn[data-tab]').forEach(button => {
        const active = button.dataset.tab === tabName;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', String(active));
        button.tabIndex = active ? 0 : -1;
    });

    if (typeof playSound === 'function') playSound('tick');

    /* Fase 5 (pontas soltas): se os painéis foram zerados (teardownSession)
     * e a sessão está pronta, re-chama os loaders da tab que o jogador
     * acabou de abrir. Sem isso, "Aguardando sessão." persistia em todas
     * as abas após qualquer teardown (pagehide, onclose, troca de rede). */
    if (
        sessionPanelsReset
        && sessionReady
        && activeRealmId
        && minerName
        && TAB_INITIALIZERS[tabName]
    ) {
        const names = TAB_INITIALIZERS[tabName];
        void (async () => {
            for (const name of names) {
                const initializer = sessionInitializers.get(name);
                if (typeof initializer === 'function') {
                    try { await initializer(); } catch (e) {
                        console.error(`Falha ao re-inicializar ${name} em showTab.`, e);
                    }
                }
            }
            sessionPanelsReset = false;
        })();
    }
}

function activateMechanicSection(groupName, sectionName, focusButton = false) {
    const buttons = Array.from(document.querySelectorAll(
        `.mechanic-subnav-btn[data-section-group="${groupName}"]`
    ));
    const panels = Array.from(document.querySelectorAll(
        `.mechanic-section[data-section-group="${groupName}"]`
    ));
    const targetButton = buttons.find(button => button.dataset.section === sectionName);
    const targetPanel = panels.find(panel => panel.dataset.section === sectionName);
    if (!targetButton || !targetPanel) return;

    buttons.forEach(button => {
        const active = button === targetButton;
        button.classList.toggle('active', active);
        button.setAttribute('aria-selected', String(active));
        button.tabIndex = active ? 0 : -1;
    });
    panels.forEach(panel => {
        const active = panel === targetPanel;
        panel.classList.toggle('active', active);
        panel.hidden = !active;
    });

    if (focusButton) targetButton.focus();
    if (typeof playSound === 'function') playSound('tick');
}

function handleMechanicSectionKeydown(event) {
    const supportedKeys = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'];
    if (!supportedKeys.includes(event.key)) return;

    const groupName = event.currentTarget.dataset.sectionGroup;
    const buttons = Array.from(document.querySelectorAll(
        `.mechanic-subnav-btn[data-section-group="${groupName}"]`
    ));
    const currentIndex = buttons.indexOf(event.currentTarget);
    if (currentIndex < 0) return;

    let targetIndex = currentIndex;
    if (event.key === 'Home') targetIndex = 0;
    if (event.key === 'End') targetIndex = buttons.length - 1;
    if (['ArrowRight', 'ArrowDown'].includes(event.key)) {
        targetIndex = (currentIndex + 1) % buttons.length;
    }
    if (['ArrowLeft', 'ArrowUp'].includes(event.key)) {
        targetIndex = (currentIndex - 1 + buttons.length) % buttons.length;
    }

    event.preventDefault();
    buttons[targetIndex].click();
    buttons[targetIndex].focus();
}

document.querySelectorAll('.mechanic-subnav-btn[data-section-group]').forEach(button => {
    button.addEventListener('click', () => {
        activateMechanicSection(button.dataset.sectionGroup, button.dataset.section);
    });
    button.addEventListener('keydown', handleMechanicSectionKeydown);
});


let audioContext;

/**
 * Cria o contexto de áudio somente após uma interação do jogador.
 */
function getAudioContext() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return null;
    if (!audioContext) {
        try {
            audioContext = new AudioContextClass();
        } catch (error) {
            console.warn('Áudio indisponível neste dispositivo.', error);
            return null;
        }
    }
    return audioContext;
}

/**
 * Reproduz um efeito sonoro curto associado à ação informada.
 */
function playSound(type) {
    const actx = getAudioContext();
    if (!actx) return;
    if (actx.state === 'suspended') {
        void actx.resume().catch(error => console.warn('Áudio bloqueado pelo navegador.', error));
    }
    const osc = actx.createOscillator();
    const gain = actx.createGain();

    if (type === 'tick') {
        osc.type = 'square'; osc.frequency.setValueAtTime(600, actx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, actx.currentTime + 0.05);
        gain.gain.setValueAtTime(0.03, actx.currentTime); gain.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + 0.05);
    } else if (type === 'success') {
        osc.type = 'sine'; osc.frequency.setValueAtTime(880, actx.currentTime);
        osc.frequency.setValueAtTime(1200, actx.currentTime + 0.1);
        gain.gain.setValueAtTime(0.15, actx.currentTime); gain.gain.linearRampToValueAtTime(0, actx.currentTime + 0.4);
    } else if (type === 'orphan') {
        osc.type = 'sawtooth'; osc.frequency.setValueAtTime(200, actx.currentTime);
        osc.frequency.linearRampToValueAtTime(50, actx.currentTime + 0.4);
        gain.gain.setValueAtTime(0.15, actx.currentTime); gain.gain.linearRampToValueAtTime(0, actx.currentTime + 0.4);
    } else if (type === 'buy') {
        osc.type = 'triangle'; osc.frequency.setValueAtTime(1200, actx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(2000, actx.currentTime + 0.2);
        gain.gain.setValueAtTime(0.1, actx.currentTime); gain.gain.exponentialRampToValueAtTime(0.01, actx.currentTime + 0.2);
    }

    osc.connect(gain); gain.connect(actx.destination);
    osc.start(); osc.stop(actx.currentTime + 0.4);
}

// ESTADO GLOBAL E DINÂMICO
const WORDS_PER_BLOCK = 6;
const configuredBaseUrl = document.querySelector('meta[name="api-base-url"]')?.content;
const runtimeOrigin = window.location.origin === 'null'
    ? 'http://localhost:8000'
    : window.location.origin;
const API_BASE_URL = new URL(configuredBaseUrl || runtimeOrigin, runtimeOrigin);
const NETWORKS_URL = new URL('/api/v1/networks', API_BASE_URL).toString();
const REALM_ID_PATTERN = /^[a-z0-9][a-z0-9_-]{0,31}$/;

function networkApiUrl(realmId, path) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    const normalizedPath = String(path).replace(/^\/+/, '');
    return new URL(
        `/api/v1/networks/${encodeURIComponent(realmId)}/${normalizedPath}`,
        API_BASE_URL
    ).toString();
}

function activeNetworkApiUrl(path) {
    return networkApiUrl(activeRealmId, path);
}

function leaderboardUrl(realmId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/leaderboard`, API_BASE_URL).toString();
}

function playerStateUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/player/${encodeURIComponent(username)}`, API_BASE_URL).toString();
}

function gameSocketUrl(realmId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    const url = new URL(`/ws/v1/game/${encodeURIComponent(realmId)}`, API_BASE_URL);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    return url;
}

let currentGridSize = 12;
let ws;
let grid = [];
let txBuffer = [];
let blockWords = [];
let selectedCells = [];
let isSelecting = false;
let isPlaying = false;
let isTransitioning = false;
let isLightningMode = false;
let activeRealmId = null;
let activeEpoch = null;
/* Fase 3 (pontas soltas): dedup de block_mined — ignora eventos com o mesmo
 * block_hash/epoch já processado (re-entrega ZMQ ou re-publicação). */
let lastMinedBlockHash = null;
let lastMinedEpoch = null;
/* Fase 3: orphan block salvage só pode ser oferecido uma vez por rodada. */
let orphanOfferedThisRound = false;
/* Fase 6 (pontas soltas): rodada já finalizada (todas as palavras achadas).
 * O tick do timer verifica essa flag antes de declarar "expirou" — sem ela,
 * a corrida timer × showResult fazia o sucesso ser sobrescrito pela
 * expiração (janela de 600ms do scheduleForSession). */
let roundSettled = false;
let sessionGeneration = 0;
let sessionReady = false;


let networkCatalog = new Map();
let catalogRetryTimeout;
let reconnectTimeout; /* Fase 1: declarada explicitamente */
let reconnectAttempt = 0;
const sessionTimeouts = new Set();
const requestControllers = new Set();
let leaderboardRequestController;
let networkHealthRequestController;
let networkCatalogRequestController;
let activePointerId = null;
let deferredInstallPrompt = null;
let serviceWorkerRegistration = null;
let reloadingForUpdate = false;
const modalReturnFocus = new WeakMap();

/* Fase 1: Persistência de sessão via sessionStorage */
const SESSION_KEY = 'mempool-miner-session';

function saveSessionState() {
    try {
        sessionStorage.setItem(SESSION_KEY, JSON.stringify({
            minerName,
            poolName,
            activeRealmId,
            balanceSatoshis,
            hardwareLevel,
            networkTimeBonus,
            roundNumber,
            roundAttempt,
            isLightningMode,
            lightningBlocksRemaining,
            comboMultiplier,
            sessionReady
        }));
    } catch(e) { /* Ignora erros de storage */ }
}

function loadSessionState() {
    try {
        const raw = sessionStorage.getItem(SESSION_KEY);
        if (!raw) return null;
        return JSON.parse(raw);
    } catch(e) { return null; }
}

function clearSessionState() {
    try { sessionStorage.removeItem(SESSION_KEY); } catch(e) {}
}

// Jogador e Loja
let minerName = "Anonymous";
let poolName = '';
let balanceSatoshis = 0;
let hardwareLevel = 1;
let hardwareNames = ["CPU Miner", "GPU Rig", "ASIC Antminer", "Quantum Node"];
let hardwarePrices = [100000, 500000, 2000000];
let networkTimeBonus = 0;
let levelTimeBonus = 0;

function getNetworkTimeBonus() {
    return networkTimeBonus + levelTimeBonus;
}

const HINT_PRICE = 5000;
const LIGHTNING_PRICE = 1000000;

function operatorDisplayName() {
    return poolName ? `[${poolName}] ${minerName}` : minerName;
}

let roundNumber = 1;
/* Fase C1: contador de TENTATIVAS de rodada — incrementa a cada início de
 * rodada (prepareNextBlock), inclusive após falha. Usado SOMENTE nos tx_ids
 * de earn para garantir unicidade entre rodadas: antes, o tx_id usava
 * roundNumber (que só sobe no sucesso), então uma rodada repetida colidia
 * com o marcador da anterior (TTL 7d) e as palavras não eram creditadas.
 * roundNumber continua sendo o "número do bloco" p/ halving/decoder/display. */
let roundAttempt = 0;
let baseReward = 500;
let effectiveBaseReward = 500; /* Fase 2: Halving — recompensa ajustada */
let wordsFoundInBlock = 0;
let currentRoundEarnings = 0;

/* Fase 1: Slashing — penalidade por erro repetido */
let consecutiveErrors = 0;
const SLASHING_THRESHOLD = 3;       /* erros consecutivos para disparar slashing */
const SLASHING_PENALTY = 0.05;      /* 5% do saldo */

/* Fase 5.4: streak de palavras encontradas sem erro (reseta a cada erro).
 * Diferente de wordsFoundTotal (cumulativo), este é o valor atual da streak.
 * Persiste entre rodadas (só reseta em erro real), para a missão
 * "10 palavras sem erro" ser atingível ao longo de várias rodadas. */
let wordsWithoutErrorStreak = 0;

let networkTimeLimit = 60;
let networkTimePassed = 0;
/* Fase 7 (pontas soltas): timer por timestamp — endTime absoluto em vez de
 * contador por tick. O setInterval é throttled em aba em segundo plano
 * (Chrome: 1 tick/s), então o contador "acelerava" na prática. Com
 * Date.now() o progresso é sempre fiel ao tempo real. */
let raceEndTime = 0;
let lastTickTime = 0;
let networkInterval;
let leaderboardInterval;
let networkHealthInterval;
let pendingBuildTimeout;
/* Fase A3: watchdog de buffer — força reconexão se o buffer ficar parado
 * por 45s sem completar as 6 palavras (evita travar em "aguardando
 * transações" após queda de WS ou perda de eventos). */
let txBufferWatchdog;
let lastTxActivityTime = 0;
const TX_BUFFER_STALL_MS = 45000;
let energyGatePending = false;
let lastFoundTime = 0;
let comboMultiplier = 1;

/* Power-ups: efeitos ativos na rodada (time_freeze em segundos restantes; demais = ativo na rodada) */
let powerupEffects = { time_freeze: 0, scanner: false, double_combo: false, magnet: false, precision: false };
/* Power-ups ativados entre rodadas: aplicados no início da próxima rodada */
let pendingPowerups = new Set();
/* Inventário pessoal de power-ups (carregado de powerups/{username}) */
let powerupsInventoryData = null;

/* Variaveis de estado para modulos */
let chatHistoryLoaded = false;
let chatHistoryLoading = false;
let marketLoaded = false;
const marketLoadedSections = new Set();
const marketLoadingSections = new Set();
let baseTimeLimit = 60;
let skillTimeBonus = 0;
let hintCost = HINT_PRICE;
let skillRewardBonus = 0;


/* Fase 3: Lightning Channel Liquidity — canal dura N blocos */
let lightningBlocksRemaining = 0;   /* blocos restantes no canal L2 */
const LIGHTNING_CHANNEL_DURATION = 5; /* blocos que o canal permanece aberto */

const gridEl = document.getElementById('word-grid');
const svgEl = document.getElementById('lines-svg');
const bankEl = document.getElementById('tx-list-container');
const netProgressEl = document.getElementById('race-fill');
const overlayEl = document.getElementById('grid-overlay');
const networkSelectEl = document.getElementById('network-select');
const networkStatusEl = document.getElementById('network-status');
const startSessionButtonEl = document.getElementById('btn-start-session');
const activeNetworkEl = document.getElementById('ui-active-network');
const nodeStatusEl = document.getElementById('ui-node-status');
const gridWrapperEl = document.getElementById('grid-wrapper');
const gameStatusEl = document.getElementById('game-status');
const connectivityStatusEl = document.getElementById('connectivity-status');
const installAppButtonEl = document.getElementById('btn-install-app');
const updateBannerEl = document.getElementById('pwa-update-banner');
const updateAppButtonEl = document.getElementById('btn-update-app');
const dismissUpdateButtonEl = document.getElementById('btn-dismiss-update');
const nextButtonEl = document.getElementById('next-btn');
let nextButtonAction = null;

/**
 * Anuncia mudanças importantes sem depender apenas de cor ou animação.
 */
/**
 * Notificacao visual para o usuario (toast inline no game-status).
 */
// Carrega o inventário PESSOAL de power-ups (não o mercado)
async function loadPowerupsInventory() {
    try {
        const response = await fetch(activeNetworkApiUrl(`powerups/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });
        if (!response.ok) throw new Error('Falha ao carregar inventário de power-ups');
        powerupsInventoryData = await response.json();
        renderPowerupsPanel();
    } catch (error) {
        console.error('Erro ao carregar inventário de power-ups:', error);
    }
}

// Renderiza o painel de power-ups (inventário pessoal + efeitos ativos)
function renderPowerupsPanel() {
    if (!powerupsActiveEl || !powerupsInventoryData) return;

    const inventory = powerupsInventoryData.inventory || {};
    const definitions = powerupsInventoryData.definitions || [];

    let html = '';
    for (const def of definitions) {
        const count = inventory[def.id] || 0;
        const iconName = POWERUP_ICON_NAMES[def.id] || 'bolt';
        const active = powerupEffects[def.id];
        html += `
            <div class="powerup-item ${active ? 'active' : ''}">
                <div class="powerup-item-icon">${iconSvg(iconName)}</div>
                <div class="powerup-item-info">
                    <div class="powerup-item-name">${escapeHtml(def.name)} <span class="powerup-item-count">x${count}</span></div>
                    <div class="powerup-item-desc">${escapeHtml(def.description)}</div>
                </div>
                <button type="button" class="powerup-item-btn" data-powerup-id="${escapeHtml(def.id)}" ${count <= 0 ? 'disabled' : ''}>${active ? 'ATIVO' : 'ATIVAR'}</button>
            </div>
        `;
    }
    powerupsActiveEl.innerHTML = html;

    powerupsActiveEl.querySelectorAll('.powerup-item-btn').forEach(btn => {
        btn.addEventListener('click', () => activatePowerup(btn.dataset.powerupId));
    });
}

// Ativa um power-up do inventário e aplica o efeito
async function activatePowerup(powerupId) {
    try {
        const response = await fetch(activeNetworkApiUrl('powerups/activate'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, powerup_id: powerupId })
        });
        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao ativar power-up', 'error');
            return;
        }
        playSound('buy');
        applyPowerupEffect(powerupId);
        await loadPowerupsInventory();
    } catch (error) {
        console.error('Erro ao ativar power-up:', error);
        showNotification('Erro ao ativar power-up', 'error');
    }
}

// Aplica o efeito do power-up (imediatamente se houver rodada, senão na próxima)
function applyPowerupEffect(powerupId) {
    if (isPlaying) {
        if (powerupId === 'time_freeze') {
            powerupEffects.time_freeze += 5;
            announceGameStatus('Time Freeze: cronômetro pausado por 5s.');
        } else if (powerupId === 'scanner') {
            powerupEffects.scanner = true;
            revealWordDirection();
        } else {
            powerupEffects[powerupId] = true;
            announceGameStatus(`${POWERUP_NAMES[powerupId] || powerupId} ativo nesta rodada.`);
        }
    } else {
        pendingPowerups.add(powerupId);
        announceGameStatus(`${POWERUP_NAMES[powerupId] || powerupId} será aplicado na próxima rodada.`);
    }
}

// Scanner: revela a direção de uma palavra (célula inicial + direção)
function revealWordDirection() {
    const unfound = blockWords.find(w => !w.found && !w.hinted);
    if (!unfound) return;
    unfound.hinted = true;
    const cell = grid[unfound.startY]?.[unfound.startX]?.element;
    if (cell) cell.classList.add('hint-glow');
    announceGameStatus('Scanner: uma palavra foi revelada (célula inicial destacada).');
}

// Aplica power-ups pendentes no início da rodada
function applyPendingPowerups() {
    if (pendingPowerups.size === 0) return;
    for (const id of pendingPowerups) {
        if (id === 'time_freeze') {
            powerupEffects.time_freeze += 5;
        } else if (id === 'scanner') {
            powerupEffects.scanner = true;
            revealWordDirection();
        } else {
            powerupEffects[id] = true;
        }
    }
    pendingPowerups.clear();
    if (powerupsActiveEl) renderPowerupsPanel();
}

// Reseta os efeitos de rodada ao preparar a próxima rodada
function resetRoundPowerups() {
    powerupEffects.scanner = false;
    powerupEffects.double_combo = false;
    powerupEffects.magnet = false;
    powerupEffects.precision = false;
}


function showNotification(message, type = 'info') {
    announceGameStatus(message);
}


function announceGameStatus(message) {
    gameStatusEl.textContent = message;
}

const sessionInitializers = new Map();
/* Fase 5 (pontas soltas): mapeia cada tab aos inicializadores que a
 * repopulam. Usado pelo showTab para re-chamar os loaders quando os
 * painéis foram zerados (teardownSession) e o jogador volta à tab. */
const TAB_INITIALIZERS = {
    upgrades: ['energy', 'crates', 'level'],
    perfil: ['skills', 'season', 'cards'],
    /* Fase 5 (ponta solta da auditoria): o painel de missões está na tab
     * competir (section-competir-missions), não em perfil. Antes 'missions'
     * estava mapeado para perfil e o painel ficava "Aguardando sessão."
     * para sempre após um teardown. */
    competir: ['missions'],
    social: ['chat-staking', 'market', 'friends'],
};
let sessionPanelsReset = false; /* true após teardownSession zerar os painéis */

function registerSessionInitializer(name, initializer) {
    if (!name || typeof initializer !== 'function') {
        throw new TypeError('Inicializador de sessão inválido');
    }
    sessionInitializers.set(name, initializer);
}

async function runSessionInitializers() {
    for (const [name, initializer] of sessionInitializers) {
        // Fase 5 (pontas soltas): retry com backoff — um inicializador que
        // falha (404/rede/backend não pronto) deixava o painel no placeholder
        // "Aguardando sessão." para sempre. Máx. 3 tentativas.
        let ok = false;
        for (let attempt = 0; attempt < 3 && !ok; attempt++) {
            try {
                await initializer();
                ok = true;
            } catch (error) {
                console.error(`Falha ao inicializar módulo ${name} (tentativa ${attempt + 1}/3).`, error);
                if (attempt < 2) {
                    await new Promise(r => setTimeout(r, 800 * (attempt + 1)));
                }
            }
        }
    }
    /* Fase 5: painéis repopulados — limpa a flag para o showTab não
     * re-chamar os loaders desnecessariamente. */
    sessionPanelsReset = false;
}

/**
 * Expõe o estado de conectividade. O shell offline não simula API nem WebSocket.
 */
function updateConnectivityStatus(event) {
    const isOnline = navigator.onLine;
    connectivityStatusEl.textContent = isOnline
        ? 'Online'
        : 'Offline — jogo ao vivo indisponível';
    connectivityStatusEl.classList.toggle('offline', !isOnline);
    document.body.classList.toggle('is-offline', !isOnline);
    if (!isOnline) {
        if (networkCatalogRequestController) {
            networkCatalogRequestController.abort();
            requestControllers.delete(networkCatalogRequestController);
            networkCatalogRequestController = undefined;
        }
        announceGameStatus('O shell está offline. Redes, eventos e ranking exigem conexão.');
    } else if (
        event?.type === 'online'
        && !sessionReady
        && document.getElementById('auth-modal').classList.contains('active')
    ) {
        void loadNetworkCatalog();
    }
}

/**
 * Mostra uma atualização somente quando o novo worker já está pronto.
 */
function showServiceWorkerUpdate(registration) {
    serviceWorkerRegistration = registration;
    setModalState(updateBannerEl, Boolean(registration.waiting));
    updateAppButtonEl.disabled = !registration.waiting;
}

/**
 * Registra o shell PWA e mantém a atualização sob decisão explícita do jogador.
 */
async function registerPwa() {
    if (!('serviceWorker' in navigator)) return;
    try {
        const registration = await navigator.serviceWorker.register('./service-worker.js');
        serviceWorkerRegistration = registration;
        if (registration.waiting) showServiceWorkerUpdate(registration);

        registration.addEventListener('updatefound', () => {
            const installingWorker = registration.installing;
            if (!installingWorker) return;
            installingWorker.addEventListener('statechange', () => {
                if (
                    installingWorker.state === 'installed'
                    && navigator.serviceWorker.controller
                ) {
                    showServiceWorkerUpdate(registration);
                }
            });
        });

        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                void registration.update();
            }
        });
    } catch (error) {
        console.warn('O shell PWA não pôde ser registrado.', error);
    }
}

window.addEventListener('online', updateConnectivityStatus);
window.addEventListener('offline', updateConnectivityStatus);
window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredInstallPrompt = event;
    installAppButtonEl.hidden = false;
});
window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null;
    installAppButtonEl.hidden = true;
});

installAppButtonEl.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    await deferredInstallPrompt.prompt();
    deferredInstallPrompt = null;
    installAppButtonEl.hidden = true;
});

updateAppButtonEl.addEventListener('click', () => {
    const waitingWorker = serviceWorkerRegistration?.waiting;
    if (!waitingWorker) return;
    reloadingForUpdate = true;
    updateAppButtonEl.disabled = true;
    waitingWorker.postMessage({ type: 'SKIP_WAITING' });
});

dismissUpdateButtonEl.addEventListener('click', () => {
    setModalState(updateBannerEl, false);
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (!reloadingForUpdate) return;
        reloadingForUpdate = false;
        window.location.reload();
    });
}

function scheduleForSession(callback, delay, generation = sessionGeneration) {
    const timeoutId = setTimeout(() => {
        sessionTimeouts.delete(timeoutId);
        if (generation === sessionGeneration) callback();
    }, delay);
    sessionTimeouts.add(timeoutId);
    return timeoutId;
}

function cancelSessionTimeout(timeoutId) {
    clearTimeout(timeoutId);
    sessionTimeouts.delete(timeoutId);
}

function captureSessionContext(realmId = activeRealmId, username = minerName) {
    return { generation: sessionGeneration, realmId, username };
}

function isSessionContextCurrent(context) {
    return (
        context.generation === sessionGeneration
        && context.realmId === activeRealmId
        && context.username === minerName
    );
}

function describeNetwork(network) {
    if (!network) return 'Rede indisponível.';
    if (network.status === 'disabled') return 'Mainnet desativada. Inicie o profile mainnet para habilitar.';
    if (network.status === 'unavailable' || network.status === 'stopped') {
        return `Nó ${network.status}. Verifique o serviço e tente novamente.`;
    }
    if (network.status === 'syncing' || network.initial_block_download) {
        const progress = Number.isFinite(network.verification_progress)
            ? ` — ${(network.verification_progress * 100).toFixed(1)}%`
            : '';
        return `Sincronizando${progress}. O jogo será liberado ao concluir.`;
    }
    if (!network.playable) return `Nó ${network.status || 'indisponível'}.`;
    return `${network.display_name} pronta${network.pruned ? ' (pruned)' : ''}.`;
}

function updateNetworkChoice() {
    const network = networkCatalog.get(networkSelectEl.value);
    networkStatusEl.textContent = describeNetwork(network);
    startSessionButtonEl.disabled = !network?.playable;
}

function getPreferredRealm() {
    try {
        return localStorage.getItem('mempool-miner-realm');
    } catch (error) {
        console.warn('Preferência de rede não pôde ser lida.', error);
        return null;
    }
}

function savePreferredRealm(realmId) {
    try {
        localStorage.setItem('mempool-miner-realm', realmId);
    } catch (error) {
        console.warn('Preferência de rede não pôde ser salva.', error);
    }
}

async function loadNetworkCatalog() {
    clearTimeout(catalogRetryTimeout);
    if (networkCatalogRequestController) {
        networkCatalogRequestController.abort();
        requestControllers.delete(networkCatalogRequestController);
        networkCatalogRequestController = undefined;
    }
    startSessionButtonEl.disabled = true;
    networkStatusEl.textContent = 'Consultando os nós disponíveis.';
    if (!navigator.onLine) {
        networkCatalog = new Map();
        networkSelectEl.replaceChildren();
        const option = document.createElement('option');
        option.textContent = 'Sem conexão';
        networkSelectEl.appendChild(option);
        networkSelectEl.disabled = true;
        networkStatusEl.textContent = 'O shell está offline. Reconecte para consultar as redes.';
        return;
    }
    const controller = new AbortController();
    networkCatalogRequestController = controller;
    requestControllers.add(controller);
    try {
        const response = await fetch(NETWORKS_URL, {
            headers: { Accept: 'application/json' },
            signal: controller.signal
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (!payload || !Array.isArray(payload.networks)) throw new Error('Catálogo fora do contrato');

        networkCatalog = new Map();
        networkSelectEl.replaceChildren();
        payload.networks.forEach(network => {
            if (!network || !REALM_ID_PATTERN.test(network.realm_id) || typeof network.display_name !== 'string') return;
            networkCatalog.set(network.realm_id, network);
            const option = document.createElement('option');
            option.value = network.realm_id;
            option.textContent = `${network.display_name} — ${network.status}`;
            option.disabled = !network.playable;
            networkSelectEl.appendChild(option);
        });

        const preferredRealm = getPreferredRealm();
        const fallbackRealm = payload.default_realm_id;
        const selectedRealm = networkCatalog.get(preferredRealm)?.playable
            ? preferredRealm
            : (networkCatalog.get(fallbackRealm)?.playable
                ? fallbackRealm
                : Array.from(networkCatalog.values()).find(item => item.playable)?.realm_id);
        if (selectedRealm) networkSelectEl.value = selectedRealm;
        networkSelectEl.disabled = networkCatalog.size === 0;
        updateNetworkChoice();
        if (Array.from(networkCatalog.values()).some(
            item => ['starting', 'syncing', 'unavailable'].includes(item.status)
        )) {
            catalogRetryTimeout = setTimeout(loadNetworkCatalog, 10000);
        }
    } catch (error) {
        if (error.name === 'AbortError') return;
        console.error('Erro ao carregar o catálogo de redes.', error);
        networkSelectEl.replaceChildren();
        const option = document.createElement('option');
        option.textContent = 'Catálogo indisponível';
        networkSelectEl.appendChild(option);
        networkSelectEl.disabled = true;
        networkStatusEl.textContent = 'Não foi possível consultar as redes. Recarregue para tentar novamente.';
        if (navigator.onLine) {
            catalogRetryTimeout = setTimeout(loadNetworkCatalog, 10000);
        }
    } finally {
        requestControllers.delete(controller);
        if (networkCatalogRequestController === controller) {
            networkCatalogRequestController = undefined;
        }
    }
}

function createEmptyStakeState() {
    return {
        active: false,
        amount: 0,
        duration_hours: 0,
        bonus_percent: 0,
        start_time: 0,
        end_time: 0,
        time_remaining_seconds: 0,
    };
}

function createInitialEnergyState() {
    return { current: 10, max: 10, nextRefill: null };
}

function createInitialCrateState() {
    return {
        free_crates: 0,
        owned_crates: 0,
        last_free_block: 0,
        legendary_bonus: 0,
        inventory: [],
    };
}

function createInitialLevelState() {
    return {
        level: 1,
        xp: 0,
        xp_to_next: 100,
        xp_progress: 0,
        rank: { name: 'Script Kiddie' },
        bonuses: { time_bonus_seconds: 1, hint_discount_percent: 0 },
    };
}

function resetSessionPanel(element, message) {
    if (!element) return;
    const placeholder = document.createElement('p');
    placeholder.className = 'loading-state';
    placeholder.textContent = message;
    element.replaceChildren(placeholder);
}

function resetSessionModules() {
    resetBossState();
    const bossDefeatModal = document.getElementById('boss-defeat-modal');
    const bossDefeatButton = document.getElementById('boss-defeat-btn');
    setModalState(bossDefeatModal, false);
    if (bossDefeatButton) bossDefeatButton.onclick = null;

    decoderActive = false;
    decoderTimeRemaining = DECODER_TIME_LIMIT;
    decoderCooldownRemaining = 0;
    setModalState(decoderModalEl, false);
    decoderLaunchBtnEl?.classList.add('hidden');
    if (decoderInputEl) {
        decoderInputEl.value = '';
        decoderInputEl.disabled = false;
    }
    if (decoderSubmitBtnEl) decoderSubmitBtnEl.disabled = false;
    if (decoderFeedbackEl) decoderFeedbackEl.hidden = true;
    if (decoderCloseBtnEl) decoderCloseBtnEl.hidden = true;

    hideGlobalEventBanner();
    setModalState(document.getElementById('achievements-modal'), false);
    achievementsData = null;
    achievementsFilter = 'all';
    achievementBonuses = { reward_percent: 0, hint_discount: 0 };
    realmsPlayed = new Set();
    epochsSurvived = 0;
    scoresSubmitted = 0;
    bestRank = 999;
    poolRank1 = 0;
    wordsFoundTotal = 0;
    goldenFoundTotal = 0;
    highFeeFoundTotal = 0;
    mevFoundTotal = 0;
    combos2xTotal = 0;
    combos4xTotal = 0;
    fastFindsTotal = 0;
    ultraFastFindsTotal = 0;
    blocksCompletedTotal = 0;
    maxScoreTotal = 0;
    rbfUsedTotal = 0;
    maxRoundEarningsTotal = 0;
    poolJoinedTotal = 0;

    missionsData = null;
    skillTreeData = null;
    skillTreeLoading = false;
    seasonData = null;
    cardsData = null;
    currentCardFilter = 'all';
    marketData = null;
    marketHistoryData = null;
    marketInventory = null;
    friendsData = null;
    chatHistoryLoaded = false;
    chatHistoryLoading = false;
    marketLoaded = false;
    marketLoadedSections.clear();
    marketLoadingSections.clear();

    baseTimeLimit = 60;
    skillTimeBonus = 0;
    levelTimeBonus = 0;
    hintCost = HINT_PRICE;
    skillRewardBonus = 0;

    sprintRoundActive = false;
    sprintRoundEnding = false;
    sprintRoundStarting = false;
    sprintWordsFound = 0;
    sprintTimeLeft = 30;
    sprintTimeLimit = 30;
    sprintStartTime = null;
    sprintTimerInterval = null;
    const sprintTimerValue = document.getElementById('sprint-timer-value');
    if (sprintTimerValue) {
        sprintTimerValue.textContent = '00:00';
        sprintTimerValue.classList.remove('warning');
    }
    document.querySelectorAll('.sprint-result-overlay').forEach(overlay => overlay.remove());

    stakeState = createEmptyStakeState();
    selectedStakeDuration = 6;
    if (stakingDurationEl) stakingDurationEl.value = '6';
    updateStakingUI();
    energyGatePending = false;
    pendingEnergyRoundId = null;
    energyState = createInitialEnergyState();
    updateEnergyUI();
    crateState = createInitialCrateState();
    updateCrateUI();
    levelState = createInitialLevelState();
    updateLevelUI();

    resetSessionPanel(document.getElementById('achievements-grid'), 'Aguardando sessão.');
    resetSessionPanel(missionsListEl, 'Aguardando sessão.');
    resetSessionPanel(chatMessagesEl, 'Aguardando sessão.');
    resetSessionPanel(stakingHistoryListEl, 'Aguardando sessão.');
    resetSessionPanel(skillsContentEl, 'Aguardando sessão.');
    resetSessionPanel(seasonRewardsFreeEl, 'Aguardando sessão.');
    resetSessionPanel(seasonRewardsPremiumEl, 'Aguardando sessão.');
    resetSessionPanel(cardsGridEl, 'Aguardando sessão.');
    resetSessionPanel(marketBrowseEl, 'Aguardando sessão.');
    resetSessionPanel(marketHistoryEl, 'Aguardando sessão.');
    resetSessionPanel(friendsListEl, 'Aguardando sessão.');
    /* Fase 5: marca que os painéis foram zerados — o showTab re-chama os
     * loaders da tab ativa quando o jogador voltar a ela. */
    sessionPanelsReset = true;
}

function teardownSession(reason = 'realm-switch') {
    sessionGeneration += 1;
    sessionReady = false;
    activeEpoch = null;
    const oldSocket = ws;
    ws = undefined;
    if (oldSocket) {
        oldSocket.onopen = null;
        oldSocket.onmessage = null;
        oldSocket.onerror = null;
        oldSocket.onclose = null;
        if (oldSocket.readyState < WebSocket.CLOSING) oldSocket.close(1000, reason);
    }
    clearInterval(networkInterval);
    clearInterval(leaderboardInterval);
    clearInterval(networkHealthInterval);
    clearInterval(poolsInterval); /* Fase 5 */
    clearInterval(missionsRefreshInterval);
    clearInterval(energyTimerInterval);
    clearInterval(seasonTimerInterval);
    clearInterval(sprintTimerInterval);
    clearInterval(decoderTimerInterval);
    clearInterval(eventCountdownInterval);
    clearInterval(stakeCountdownInterval);
    clearInterval(stakePollInterval);
    clearInterval(txBufferWatchdog); /* Fase A3 */
    txBufferWatchdog = null;

    clearTimeout(achievementToastTimeout);
    clearTimeout(rbfTimeout);
    clearTimeout(reconnectTimeout);
    clearTimeout(catalogRetryTimeout);
    cancelSessionTimeout(pendingBuildTimeout);
    pendingBuildTimeout = undefined;
    sessionTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
    sessionTimeouts.clear();
    requestControllers.forEach(controller => controller.abort());
    requestControllers.clear();
    leaderboardRequestController = undefined;
    networkHealthRequestController = undefined;
    networkCatalogRequestController = undefined;
    poolsRequestController = undefined; /* Fase 5 */
    resetSessionModules();
    setModalState(document.getElementById('lightning-modal'), false);
    setModalState(document.getElementById('result-modal'), false);
    setNextButtonAction(null);
    selectedCells.forEach(({ cell }) => {
        cell.classList.remove('selected');
        cell.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.floating-text').forEach(element => element.remove());
    svgEl.replaceChildren();
    txBuffer = [];
    blockWords = [];
    selectedCells = [];
    isSelecting = false;
    activePointerId = null;
    isPlaying = false;
    isTransitioning = false;
    currentRoundEarnings = 0;
    networkTimePassed = 0;
    netProgressEl.style.width = '0%';
    netProgressEl.setAttribute('aria-valuenow', '0');
    netProgressEl.setAttribute('aria-valuetext', 'Aguardando uma rodada');
    comboMultiplier = 1;
    lastFoundTime = 0;
    document.getElementById('ui-combo').innerText = '1.0×';
    consecutiveErrors = 0;
    lightningBlocksRemaining = 0;
    announceGameStatus('Sessao encerrada. Escolha uma rede para continuar.');
    updateStoreUI();
    /* Fase 3: limpa o estado salvo apenas quando NÃO é page-hide
       (page-hide preserva para restauração no próximo load) */
    if (reason !== 'page-hide') {
        clearSessionState();
    }
    return sessionGeneration;
}

/**
 * Sincroniza a apresentação visual e semântica de um modal.
 */
function setModalState(modal, isActive) {
    const wasActive = modal.classList.contains('active');
    if (isActive && !wasActive && document.activeElement instanceof HTMLElement) {
        modalReturnFocus.set(modal, document.activeElement);
    }
    modal.classList.toggle('hidden', !isActive);
    modal.hidden = !isActive;
    modal.classList.toggle('active', isActive);
    modal.setAttribute('aria-hidden', String(!isActive));
    if (isActive) {
        requestAnimationFrame(() => {
            if (!modal.classList.contains('active')) return;
            (modal.querySelector('input:not(:disabled), select:not(:disabled), button:not(:disabled)') || modal).focus();
        });
    } else if (wasActive) {
        const returnTarget = modalReturnFocus.get(modal);
        modalReturnFocus.delete(modal);
        if (returnTarget?.isConnected) returnTarget.focus();
    }
}

document.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    /* Fase 8 (ponta solta da auditoria): os modais reais usam .modal-wrap
     * (não .modal-overlay) — antes a trapa de foco nunca encontrava o modal
     * e ficava desativada em todos os modais (acessibilidade). */
    const modal = document.querySelector('.modal-wrap.active');
    if (!modal) return;
    const focusable = Array.from(modal.querySelectorAll(
        'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])'
    )).filter(element => !element.hidden);
    if (focusable.length === 0) {
        event.preventDefault();
        modal.focus();
        return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (!modal.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
    } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
    }
});

/**
 * Ajusta células e trilhas da grade à dificuldade e à largura disponível.
 */
function configureGridSize(size) {
    const compactLayout = window.matchMedia('(max-width: 559px)').matches;
    const gap = compactLayout ? 2 : 4;
    const wrapperWidth = gridWrapperEl.clientWidth || window.innerWidth;
    // clientWidth do .grid-hull inclui o padding (6px*2); o grid ocupa a caixa de
    // conteúdo, então subtraímos só o padding para a grade preencher o hull.
    const hullOverhead = 12;
    const availableWidth = Math.max(220, wrapperWidth - hullOverhead);
    const responsiveSize = Math.floor((availableWidth - ((size - 1) * gap)) / size);
    // Teto de 72px evita células gigantes em telas 4K; piso de 13px em telas pequenas.
    // (antes: teto fixo de 38/28px + largura limitada a 620px, que deixava a grade
    //  "incompleta" — não preenchendo o hull em telas grandes)
    const cellSize = Math.max(13, Math.min(72, responsiveSize));
    gridEl.style.setProperty('--grid-gap', `${gap}px`);
    gridEl.style.setProperty('--cell-size', `${cellSize}px`);
    gridEl.style.gridTemplateColumns = `repeat(${size}, var(--cell-size))`;
    gridEl.style.gridTemplateRows = `repeat(${size}, var(--cell-size))`;
    gridEl.setAttribute('aria-rowcount', String(size));
    gridEl.setAttribute('aria-colcount', String(size));
}

/**
 * Confirma o contrato mínimo de uma transação recebida pelo WebSocket.
 */
function isValidTransactionEvent(data) {
    // Valida campos obrigatorios: word, is_high_fee, is_golden, vsize
    // Campos opcionais: is_mev, expand_grid, base_reward, multiplier, fee_rate_sat_vb
    return Boolean(
        data
        && typeof data === 'object'
        && typeof data.word === 'string'
        && /^[A-Z]{1,15}$/.test(data.word)
        && typeof data.is_high_fee === 'boolean'
        && typeof data.is_golden === 'boolean'
        && typeof data.vsize === 'number'
        && Number.isFinite(data.vsize)
        && data.vsize > 0
    );
}

/**
 * Valida a estrutura usada para renderizar o leaderboard.
 */
function isValidLeaderboardPayload(data) {
    return Boolean(
        data
        && Array.isArray(data.leaderboard)
        && data.leaderboard.every(miner => (
            miner
            && typeof miner.username === 'string'
            && Number.isInteger(miner.score)
            && miner.score >= 0
        ))
    );
}

/**
 * Monta a grade visual usada antes da primeira rodada.
 */
function initEmptyGrid() {
    gridEl.innerHTML = '';
    currentGridSize = 12;
    configureGridSize(currentGridSize);

    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.innerText = String.fromCharCode(65 + Math.floor(Math.random() * 26));
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.tabIndex = x === 0 && y === 0 ? 0 : -1;
            cell.setAttribute('role', 'gridcell');
            cell.setAttribute('aria-selected', 'false');
            cell.setAttribute('aria-label', `Letra ${cell.innerText}. Aguarde o início da rodada.`);
            gridEl.appendChild(cell);
        }
    }
    updateStoreUI();
}
initEmptyGrid();

/* ==========================================================================
   Boss Battles — estado e lógica do Boss Block (a cada 50 blocos)
   ========================================================================== */
let isBossActive = false;
let bossHp = 10;
let bossMaxHp = 10;
let bossRewardMultiplier = 5;
let bossLoot = 50000;
let bossWordsRequired = 10;
let bossTimer = 45;
let bossGridSize = 15; /* Fase 4.2: lido do evento boss_block (data.boss_grid_size) */
let bossDefeatHandled = false;

/* ==========================================================================
   Fase 8: Eventos Globais — estado e lógica
   ========================================================================== */
let activeGlobalEvent = null;   // {type, label, icon, description, color, startedAt, endsAt, preannounced}
let eventBannerEl = null;       // Referência ao banner DOM
let eventCountdownInterval = null;

// Mapeamento de ícones e cores por tipo de evento
const EVENT_META = {
    fee_spike:       { iconName: 'bolt', label: 'Fee Spike',       color: '#a855f7' },
    golden_rush:     { iconName: 'star', label: 'Golden Rush',     color: '#eab308' },
    mempool_flood:   { iconName: 'wave', label: 'Mempool Flood',   color: '#f97316' },
    lightning_storm: { iconName: 'storm', label: 'Lightning Storm', color: '#0ea5e9' },
};

// Durações em segundos
const EVENT_DURATION = {
    fee_spike: 600,       // 10 min
    golden_rush: 300,     // 5 min
    mempool_flood: 600,   // 10 min
    lightning_storm: 180, // 3 min
};

networkSelectEl.addEventListener('change', updateNetworkChoice);
document.getElementById('auth-form').addEventListener('submit', event => {
    event.preventDefault();
    void startSession();
});

function handleMainTabKeydown(event) {
    const supportedKeys = ['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp', 'Home', 'End'];
    if (!supportedKeys.includes(event.key)) return;

    const tabs = Array.from(document.querySelectorAll('.mecha-nav-group .mecha-btn[data-tab]'));
    const currentIndex = tabs.indexOf(event.currentTarget);
    if (currentIndex < 0) return;

    let targetIndex = currentIndex;
    if (event.key === 'Home') targetIndex = 0;
    if (event.key === 'End') targetIndex = tabs.length - 1;
    if (['ArrowRight', 'ArrowDown'].includes(event.key)) {
        targetIndex = (currentIndex + 1) % tabs.length;
    }
    if (['ArrowLeft', 'ArrowUp'].includes(event.key)) {
        targetIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    }

    event.preventDefault();
    const target = tabs[targetIndex];
    target.focus();
    target.click();
}

document.querySelectorAll('.mecha-nav-group .mecha-btn[data-tab]').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        showTab(tabName);
        if (tabName === 'social') {
            chatPanelVisible = true;
            if (sessionReady && !chatHistoryLoaded) void loadChatHistory();
        } else if (tabName === 'perfil' && sessionReady && !skillTreeData) {
            void loadSkillTree();
        }
    });
    button.addEventListener('keydown', handleMainTabKeydown);
});
document.getElementById('btn-buy-hint').addEventListener('click', buyHint);
document.getElementById('btn-buy-hw').addEventListener('click', buyHardware);
document.getElementById('btn-buy-ln').addEventListener('click', buyLightning);
document.getElementById('btn-close-lightning').addEventListener('click', () => {
    setModalState(document.getElementById('lightning-modal'), false);
});
function setNextButtonAction(action) {
    nextButtonAction = typeof action === 'function' ? action : null;
    nextButtonEl.disabled = nextButtonAction === null;
}
nextButtonEl.addEventListener('click', () => {
    const action = nextButtonAction;
    setNextButtonAction(null);
    if (action) action();
});
document.getElementById('btn-change-network').addEventListener('click', () => {
    teardownSession('user-network-change');
    overlayEl.classList.remove('hidden');
    const loaderText = overlayEl.querySelector('#tx-loading');
    if (loaderText) loaderText.innerText = 'Escolha uma rede para iniciar uma nova sessão.';
    setModalState(document.getElementById('auth-modal'), true);
    void loadNetworkCatalog();
});
void loadNetworkCatalog();
gridEl.addEventListener('pointerdown', handlePointerStart);
gridEl.addEventListener('pointermove', handlePointerMove);
gridEl.addEventListener('keydown', handleGridKeydown);
window.addEventListener('pointerup', handlePointerEnd);
window.addEventListener('pointercancel', handlePointerCancel);
window.addEventListener('blur', () => cancelSelection());
window.addEventListener('resize', () => configureGridSize(currentGridSize));
if ('ResizeObserver' in window) {
    const gridResizeObserver = new ResizeObserver(() => configureGridSize(currentGridSize));
    gridResizeObserver.observe(gridWrapperEl);
}
window.addEventListener('pagehide', () => {
    saveSessionState(); /* Fase 1: salva estado antes de sair */
    teardownSession('page-hide');
});
/* Fase 5 (pontas soltas): ao voltar via back/forward (bfcache), o pagehide
 * já zerou os 11 painéis ("Aguardando sessão."). Re-dispara os
 * inicializadores para repopulá-los. Sem esse handler, os painéis ficavam
 * no placeholder para sempre após navegar para fora e voltar. */
window.addEventListener('pageshow', (event) => {
    if (!event.persisted) return;
    if (!sessionReady || !activeRealmId || !minerName) return;
    announceGameStatus('Restaurando painéis da sessão...');
    void runSessionInitializers();
});
updateConnectivityStatus();

/* Fase 1: Tenta restaurar sessão anterior antes de mostrar modal */
(async () => {
    try {
        const saved = loadSessionState();
        if (saved && saved.minerName && saved.activeRealmId) {
            minerName = saved.minerName;
            poolName = saved.poolName ?? '';
            activeRealmId = saved.activeRealmId;
            balanceSatoshis = saved.balanceSatoshis ?? 0;
            hardwareLevel = saved.hardwareLevel ?? 1;
            networkTimeBonus = saved.networkTimeBonus ?? 0;
            roundNumber = saved.roundNumber ?? 1;
            roundAttempt = saved.roundAttempt ?? 0;
            isLightningMode = saved.isLightningMode ?? false;
            lightningBlocksRemaining = saved.lightningBlocksRemaining ?? 0;
            comboMultiplier = saved.comboMultiplier ?? 1;

            // Restaura UI
            document.getElementById('ui-operator-tag').innerText = operatorDisplayName();
            document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
            document.getElementById('ui-hw').innerText = hardwareNames[hardwareLevel - 1];
            document.getElementById('miner-input').value = minerName;
            document.getElementById('pool-tag-input').value = poolName;
            if (isLightningMode) document.body.classList.add('lightning-theme');

            // Seleciona a rede salva no select
            if (networkSelectEl.value !== activeRealmId) {
                networkSelectEl.value = activeRealmId;
            }

            // Reconecta WebSocket automaticamente
            announceGameStatus('Restaurando sessão anterior...');
            await startSession(activeRealmId);
        } else {
            // Sem sessão anterior — mostra modal de auth
            // Fase 6.10: onboarding sem tutorial — o modal de auth serve como
            // ponto de entrada, mas não há walkthrough. Isso é aceitável para
            // um jogo de caça-palavras com UI auto-explicativa (grade + palavras).
            // TODO: adicionar tutorial interativo em versão futura.
            setModalState(document.getElementById('auth-modal'), true);
        }
    } catch (error) {
        console.error('Erro na inicialização:', error);
        // Em caso de erro, mostra o modal de auth
        setModalState(document.getElementById('auth-modal'), true);
    }
})();

void registerPwa();

/**
 * Valida o nickname, abre o WebSocket e inicia a sessão do jogador.
 * Fase 1: Aceita realmIdOverride para reconexão automática.
 */
async function startSession(realmIdOverride = null) {
    const requestedRealmId = realmIdOverride || networkSelectEl.value;
    let selectedNetwork = networkCatalog.get(requestedRealmId);

    // Fallback 1: se networkCatalog nao carregou, tentar carregar AGORA
    if (!selectedNetwork?.playable && networkCatalog.size === 0) {
        announceGameStatus('Carregando redes...');
        await loadNetworkCatalog();
        selectedNetwork = networkCatalog.get(requestedRealmId);
    }

    // Fallback 2: usar a primeira rede playable disponivel
    if (!selectedNetwork?.playable && networkCatalog.size > 0) {
        selectedNetwork = Array.from(networkCatalog.values()).find(n => n.playable);
        if (selectedNetwork) {
            networkSelectEl.value = selectedNetwork.realm_id;
        }
    }

    // Fallback 3: se ainda nao ha rede, forcar signet (default do backend)
    if (!selectedNetwork?.playable) {
        selectedNetwork = networkCatalog.get('signet');
        if (selectedNetwork?.playable) {
            networkSelectEl.value = 'signet';
        }
    }

    if (!selectedNetwork?.playable) {
        updateNetworkChoice();
        announceGameStatus('Nenhuma rede disponivel. Recarregue a pagina.');
        return;
    }
    networkSelectEl.value = selectedNetwork.realm_id;
    const input = document.getElementById('miner-input').value.trim();
    const safeInput = Array.from(input)
        .filter(char => /[\p{L}\p{N}_-]/u.test(char))
        .join('')
        .slice(0, 12);
    const poolTag = document.getElementById('pool-tag-input').value.trim();
    const safePoolTag = Array.from(poolTag)
        .filter(char => /[\p{L}\p{N}_-]/u.test(char))
        .join('')
        .slice(0, 20);
    minerName = safeInput || "Miner_" + Math.floor(Math.random() * 9999);
    poolName = safePoolTag;
    if (poolName) {
        /* Fase 7: Tracking — pool joined */
        trackPoolJoined();
    }
    const previousRealm = activeRealmId;
    const generation = teardownSession('network-change');
    clearTimeout(catalogRetryTimeout);
    activeRealmId = selectedNetwork.realm_id;
    savePreferredRealm(activeRealmId);
    /* Fase 7: Tracking — realm jogado */
    trackRealmPlayed(activeRealmId);
    if (previousRealm && previousRealm !== activeRealmId) {
        balanceSatoshis = 0;
        hardwareLevel = 1;
        networkTimeBonus = 0;
        roundNumber = 1;
        roundAttempt = 0; /* Fase C1: nova contagem de tentativas no realm */
        isLightningMode = false;
        document.body.classList.remove('lightning-theme');
        document.getElementById('ui-balance').innerText = '0';
        document.getElementById('ui-hw').innerText = hardwareNames[0];
    }
    document.getElementById('ui-operator-tag').innerText = operatorDisplayName();
    activeNetworkEl.textContent = selectedNetwork.display_name;
    nodeStatusEl.textContent = 'Conectando';
    announceGameStatus(`Conectando à rede ${selectedNetwork.display_name}.`);
    setModalState(document.getElementById('auth-modal'), false);

    // Fase 3: Carrega estado do jogador do backend
    if (!previousRealm || previousRealm === activeRealmId) {
        void loadPlayerState(activeRealmId, minerName);
    }
    /* Fase 7: Carrega stats de achievements */
    void loadAchievementStats(activeRealmId, minerName);

    const socket = new WebSocket(gameSocketUrl(activeRealmId));
    ws = socket;
    const handshakeTimeout = scheduleForSession(() => {
        if (socket === ws && !sessionReady) socket.close(4002, 'Timeout de handshake');
    }, 10000, generation);

    socket.onopen = () => {
        if (generation !== sessionGeneration || socket !== ws) return;
        nodeStatusEl.textContent = 'Aguardando handshake';
    };
    socket.onerror = () => {
        if (generation !== sessionGeneration || socket !== ws) return;
        console.error("Falha na conexão WebSocket.");
    };
    socket.onclose = (event) => {
        if (generation !== sessionGeneration || socket !== ws) return;
        const realmToReconnect = activeRealmId;
        teardownSession('socket-close');
        nodeStatusEl.textContent = 'Desconectada';

        // Fase 2: Reconexão automática
        if (event.code === 1008 || event.code === 4001 || event.code === 4002) {
            // Erros que não devem tentar reconectar
            reconnectAttempt = 0;
            announceGameStatus('Conexão ao jogo perdida. Troque a rede para reconectar.');
            overlayEl.classList.remove('hidden');
            const loaderText = overlayEl.querySelector('#tx-loading');
            if (loaderText) loaderText.innerText = "Conexão perdida. Use Trocar rede para reconectar.";
        } else {
            // Reconexão automática para quedas de rede/temporárias
            announceGameStatus('Conexão perdida. Tentando reconectar...');
            overlayEl.classList.remove('hidden');
            const loaderText = overlayEl.querySelector('#tx-loading');
            if (loaderText) loaderText.innerText = "Reconectando...";

            const maxReconnectAttempts = 5;
            const baseDelay = 1000;
            const reconnectGeneration = sessionGeneration;
            reconnectAttempt++;
            if (reconnectAttempt > maxReconnectAttempts) {
                console.warn(`Falha ao reconectar após ${maxReconnectAttempts} tentativas`);
                if (loaderText) loaderText.innerText = "Falha na reconexão. Recarregue a página.";
                return;
            }

            const delay = baseDelay * Math.pow(2, reconnectAttempt - 1);
            console.log(`Tentativa ${reconnectAttempt}/${maxReconnectAttempts} em ${delay}ms`);

            reconnectTimeout = setTimeout(() => {
                if (reconnectGeneration === sessionGeneration && !ws) {
                    void startSession(realmToReconnect);
                }
            }, delay);
        }
    };

    socket.onmessage = (event) => {
        if (generation !== sessionGeneration || socket !== ws) return;
        let data;
        try {
            data = JSON.parse(event.data);
        } catch (error) {
            console.error("Evento WebSocket inválido.", error);
            return;
        }
        if (!data || typeof data !== 'object' || Array.isArray(data)) {
            console.warn("Evento WebSocket fora do contrato foi ignorado.");
            return;
        }
        const scopedActions = new Set([
            'game_start', 'network_status', 'transaction_received', 'block_mined',
            'leaderboard_reset' /* Fase 4 */,
            'market_sale' /* Fase 4: atualização do vendedor */,
            'boss_block' /* Boss Battles */,
            'event_preannounce', 'event_started', 'event_ended' /* Fase 8: Eventos Globais */,
            'pvp_challenge', 'pvp_start', 'pvp_score_update', 'pvp_end', 'pvp_timer' /* Fase 3: PvP */,
            'heartbeat' /* Fase 11: Online Status */,
            'chat_message' /* Fase 9: Chat em Tempo Real */
        ]);
        if (scopedActions.has(data.action) && data.realm_id !== activeRealmId) {
            if (data.action === 'game_start') socket.close(4001, 'Realm divergente');
            console.warn('Evento de outro realm foi ignorado.');
            return;
        }
        if (data.action === 'game_start') {
            cancelSessionTimeout(handshakeTimeout);
            activeEpoch = data.epoch || null;
            sessionReady = data.playable === true;
            if (sessionReady) reconnectAttempt = 0;
            nodeStatusEl.textContent = sessionReady ? 'Pronta' : (data.status || 'Indisponível');
            if (!sessionReady) {
                teardownSession('network-not-playable');
                overlayEl.classList.remove('hidden');
                const loaderText = overlayEl.querySelector('#tx-loading');
                if (loaderText) loaderText.innerText = describeNetwork(data);
                setModalState(document.getElementById('auth-modal'), true);
                catalogRetryTimeout = setTimeout(loadNetworkCatalog, 10000);
                return;
            }
            announceGameStatus(`${selectedNetwork.display_name} conectada. Aguardando transações.`);
            prepareNextBlock();
            /* Fase A2: replay de transações pendentes — o backend reenvia as
             * transações da epoch atual que ainda não foram consumidas. Isso
             * evita o estado "aguardando transações" após queda de WS ou
             * mudança de epoch. O handler de transaction_received deduplica
             * por `word`, então reenviar é seguro. */
            if (Array.isArray(data.pending_transactions) && data.pending_transactions.length > 0) {
                console.log(`Recebendo ${data.pending_transactions.length} transações pendentes (replay).`);
                for (const pendingTx of data.pending_transactions) {
                    // Reenvia como transaction_received para reutilizar o handler existente
                    // (que deduplica por word e respeita isPlaying/isBossActive).
                    handleTransactionEvent(pendingTx);
                }
            }
            void fetchLeaderboard(activeRealmId, generation);
            clearInterval(leaderboardInterval);
            leaderboardInterval = setInterval(
                () => fetchLeaderboard(activeRealmId, generation),
                10000
            );
            /* Fase 5: Mining Pools — polling de pools */
            void fetchPools(activeRealmId, generation);
            clearInterval(poolsInterval);
            poolsInterval = setInterval(
                () => fetchPools(activeRealmId, generation),
                15000
            );
            clearInterval(networkHealthInterval);
            networkHealthInterval = setInterval(
                () => pollNetworkHealth(activeRealmId, generation),
                10000
            );
            return;
        }
        if (data.action === 'network_status') {
            nodeStatusEl.textContent = data.status || 'Indisponível';
            if (data.playable === false) {
                teardownSession('network-unavailable');
                overlayEl.classList.remove('hidden');
                const loaderText = overlayEl.querySelector('#tx-loading');
                if (loaderText) loaderText.innerText = describeNetwork(data);
                setModalState(document.getElementById('auth-modal'), true);
                void loadNetworkCatalog();
            }
            return;
        }
        if (data.action === 'market_sale') {
            if (data.seller === minerName) {
                void Promise.all([
                    loadMarketList(),
                    loadMarketHistory(),
                    loadPlayerState(activeRealmId, minerName),
                ]);
                showNotification(`Power-up vendido por ${Number(data.price).toLocaleString()} sats.`, 'success');
            }
            return;
        }
        if (data.action === 'chat_message') {
            /* Fase 9: Chat em Tempo Real — mensagem broadcast via WebSocket.
             * Dedup: o remetente já adicionou a própria mensagem na resposta
             * do POST /chat/send (game.js:4473). Comparamos por
             * username+message+timestamp para não duplicar. */
            const already = chatMessages.some(
                m => m.username === data.username
                    && m.message === data.message
                    && m.timestamp === data.timestamp
            );
            if (!already) {
                chatMessages.push({
                    username: data.username,
                    message: data.message,
                    timestamp: data.timestamp,
                });
                if (chatMessages.length > CHAT_MAX_MESSAGES) chatMessages.shift();
                appendChatMessage(
                    { username: data.username, message: data.message, timestamp: data.timestamp },
                    true
                );
            }
            return;
        }
        if (data.action === "transaction_received" && sessionReady && !isPlaying) {
            handleTransactionEvent(data);
        }
        else if (data.action === "block_mined") {
            /* Fase 3 (pontas soltas): dedup — ignora block_mined com o mesmo
             * block_hash/epoch já processado (re-entrega ZMQ ou re-publicação
             * do backend). Sem isso, "Bloco minerado!" aparece 2× e a rodada
             * reinicia com tempo acelerado. */
            if (data.block_hash && data.block_hash === lastMinedBlockHash) {
                console.warn("block_mined duplicado ignorado:", data.block_hash.slice(0, 16));
                return;
            }
            if (data.epoch && data.epoch === lastMinedEpoch && !data.block_hash) {
                console.warn("block_mined duplicado ignorado (epoch):", data.epoch.slice(0, 16));
                return;
            }
            lastMinedBlockHash = data.block_hash || null;
            lastMinedEpoch = data.epoch || null;
            orphanOfferedThisRound = false;
            activeEpoch = data.epoch ?? activeEpoch; /* Usa nullish coalescing para evitar sobrescrever com block_hash */
            clearInterval(networkInterval);
            cancelSessionTimeout(pendingBuildTimeout);
            pendingBuildTimeout = undefined;
            txBuffer = [];
            const loadingText = document.getElementById('tx-loading-bank');
            if (loadingText) {
                loadingText.innerText = `Aguardando transações (0/${WORDS_PER_BLOCK})...`;
            }
            /* Fase 2: Halving Protocol — evento visual quando bloco múltiplo de 210000 */
            if (data.is_halving_block) {
                announceGameStatus('HALVING! A recompensa da rede será cortada pela metade!');
                document.body.classList.add('halving-flash');
                scheduleForSession(() => document.body.classList.remove('halving-flash'), 2000);
            }
            /* Fase 2: Cards — credita o card do bloco na coleção do jogador */
            if (data.block_hash) {
                void creditBlockCard(data.block_hash);
            }
            if (sprintRoundActive) {
                void endSprintRound('block_mined');
            } else if (isPlaying) {
                isPlaying = false;
                playSound('orphan');
                /* Fase 2: Orphan Block Salvage (RBF) — oferece resgate.
                 * Fase 3: só uma vez por rodada (flag orphanOfferedThisRound). */
                if (!orphanOfferedThisRound) {
                    orphanOfferedThisRound = true;
                    showOrphanBlockSalvage();
                }
            } else if (!isTransitioning && !document.getElementById('result-modal').classList.contains('active')) {
                /* Fase 3: Lightning Channel Liquidity — decrementa blocos restantes */
                if (isLightningMode && lightningBlocksRemaining > 0) {
                    lightningBlocksRemaining--;
                    if (lightningBlocksRemaining <= 0) {
                        /* Canal expirado — desativa Lightning */
                        isLightningMode = false;
                        lightningBlocksRemaining = 0;
                        document.body.classList.remove('lightning-theme');
                        announceGameStatus('Canal Lightning fechado. Retornando a Mainnet.');
                        updateStoreUI();
                    } else {
                        announceGameStatus(`Canal Lightning: ${lightningBlocksRemaining} blocos restantes.`);
                    }
                }
                prepareNextBlock();
            }
        }
        /* Fase 4: Leaderboard Epochs — reset a cada 2016 blocos */
        if (data.action === 'leaderboard_reset') {
            announceGameStatus(`Nova temporada! Leaderboard resetado (epoch ${data.epoch}).`);
            void fetchLeaderboard(activeRealmId, generation);
            /* Fase 7: Tracking — epoch sobrevivida */
            trackEpochSurvived();
            return;
        }
        /* Boss Battles: evento boss_block — a cada 50 blocos */
        if (data.action === 'boss_block') {
            handleBossBlock(data, generation);
            return;
        }

        // Fase 8: Eventos Globais — handlers para eventos de evento global
        // O backend envia event_started_at / event_ends_at (não started_at/ends_at)
        if (data.action === 'event_preannounce') {
            handleGlobalEventMessage({ event_type: data.event_type, action: 'preannounce', ends_at: data.event_ends_at, started_at: data.event_started_at });
            return;
        }
        if (data.action === 'event_started') {
            handleGlobalEventMessage({ event_type: data.event_type, action: 'started', ends_at: data.event_ends_at, started_at: data.event_started_at });
            return;
        }
        if (data.action === 'event_ended') {
            handleGlobalEventMessage({ event_type: data.event_type, action: 'ended', ends_at: data.event_ends_at, started_at: data.event_started_at });
            return;
        }

        // Fase 3: PvP — handlers para eventos PvP
        if (data.action === 'pvp_challenge') {
            showNotification(`${data.challenger} te desafiou para PvP!`, 'info');
            return;
        }
        if (data.action === 'pvp_start') {
            showNotification('PvP iniciado!', 'success');
            return;
        }
        if (data.action === 'pvp_score_update') {
            /* Fase 6.12: handler vazio — PvP ainda não implementado.
             * O evento é reconhecido para evitar warnings no console,
             * mas não há lógica de jogo PvP ativa. */
            return;
        }
        if (data.action === 'pvp_end') {
            showNotification(`PvP finalizado! ${data.winner === minerName ? 'Você venceu!' : 'Você perdeu.'}`, data.winner === minerName ? 'success' : 'error');
            return;
        }
        if (data.action === 'pvp_timer') {
            /* Fase 6.12: handler vazio — PvP ainda não implementado. */
            return;
        }

        // Fase 11: Online Status — handler para heartbeat
        if (data.action === 'heartbeat') {
            // Responde ao heartbeat para manter status online
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ action: 'player_heartbeat', username: minerName }));
            }
            return;
        }

        // Fase 4: Sincronização de epoch — verifica se o frontend está na mesma epoch que o backend
        if (data.action === 'block_mined' && data.epoch) {
            const backendEpoch = data.epoch;
            if (activeEpoch && activeEpoch !== backendEpoch) {
                // Epoch divergente — reconectar para sincronizar
                console.warn(`Epoch divergente: frontend=${activeEpoch.substring(0, 16)}... backend=${backendEpoch.substring(0, 16)}...`);
                announceGameStatus('Epoch divergente. Reconectando para sincronizar...');

                // Fechar conexão atual
                if (socket) {
                    socket.close(4003, 'Epoch divergente');
                }

                // Reconectar automaticamente
                setTimeout(() => {
                    if (generation === sessionGeneration && socket === ws) {
                        startSession(activeRealmId);
                    }
                }, 1000);
            }
        }
    };
    await runSessionInitializers();
}

/**
 * Detecta expiração do heartbeat mesmo quando o ingestor não encerra limpo.
 */
async function pollNetworkHealth(realmId, generation) {
    if (!realmId || generation !== sessionGeneration) return;
    if (networkHealthRequestController) {
        networkHealthRequestController.abort();
        requestControllers.delete(networkHealthRequestController);
    }
    const controller = new AbortController();
    networkHealthRequestController = controller;
    requestControllers.add(controller);
    try {
        const url = new URL(
            `/api/v1/networks/${encodeURIComponent(realmId)}/health`,
            API_BASE_URL
        );
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const network = await response.json();
        if (generation !== sessionGeneration || realmId !== activeRealmId) return;
        nodeStatusEl.textContent = network.status || 'Indisponível';
        if (network.playable !== true) {
            teardownSession('heartbeat-expired');
            overlayEl.classList.remove('hidden');
            const loaderText = overlayEl.querySelector('#tx-loading');
            if (loaderText) loaderText.innerText = describeNetwork(network);
            setModalState(document.getElementById('auth-modal'), true);
            void loadNetworkCatalog();
        }
    } catch (error) {
        if (error.name !== 'AbortError') console.error('Falha ao consultar o nó ativo.', error);
    } finally {
        requestControllers.delete(controller);
        if (networkHealthRequestController === controller) {
            networkHealthRequestController = undefined;
        }
    }
}

/**
 * Busca e renderiza o Top 10 sem interpretar dados do servidor como HTML.
 */
async function fetchLeaderboard(realmId = activeRealmId, generation = sessionGeneration) {
    if (!realmId || generation !== sessionGeneration) return;
    if (leaderboardRequestController) {
        leaderboardRequestController.abort();
        requestControllers.delete(leaderboardRequestController);
    }
    const controller = new AbortController();
    leaderboardRequestController = controller;
    requestControllers.add(controller);
    try {
        const response = await fetch(leaderboardUrl(realmId), { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (generation !== sessionGeneration || realmId !== activeRealmId) return;
        if (!isValidLeaderboardPayload(data)) {
            throw new Error('Resposta do leaderboard fora do contrato');
        }
        if (data.realm_id && data.realm_id !== realmId) throw new Error('Leaderboard de outro realm');
        const listEl = document.getElementById('leaderboard-list');
        listEl.replaceChildren();
        data.leaderboard.forEach((miner, index) => {
            const item = document.createElement('div');
            item.className = `rank-item top-${index + 1}`;
            const identity = document.createElement('span');
            const score = document.createElement('span');
            identity.textContent = `#${index + 1} ${miner.username}`;
            score.textContent = Number(miner.score).toLocaleString();
            item.append(identity, score);
            listEl.appendChild(item);

            /* Fase 7: Tracking — melhor rank no leaderboard */
            if (miner.username === minerName) {
                trackBestRank(index + 1);
            }
        });
        if (data.leaderboard.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'loading-state';
            emptyState.textContent = 'Nenhuma pontuação registrada.';
            listEl.appendChild(emptyState);
        }
    } catch (error) {
        if (error.name !== 'AbortError') console.error("Erro ao buscar o leaderboard.", error);
    } finally {
        requestControllers.delete(controller);
        if (leaderboardRequestController === controller) {
            leaderboardRequestController = undefined;
        }
    }
}

/* Fase 5: Mining Pools — polling do leaderboard de pools */
let poolsRequestController;
let poolsInterval;

async function fetchPools(realmId = activeRealmId, generation = sessionGeneration) {
    if (!realmId || generation !== sessionGeneration) return;
    if (poolsRequestController) {
        poolsRequestController.abort();
        requestControllers.delete(poolsRequestController);
    }
    const controller = new AbortController();
    poolsRequestController = controller;
    requestControllers.add(controller);
    try {
        const url = `${leaderboardUrl(realmId).replace('/leaderboard', '')}/pools`;
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (generation !== sessionGeneration || realmId !== activeRealmId) return;
        const listEl = document.getElementById('pool-list');
        if (!listEl) return;
        listEl.replaceChildren();
        if (data.pools && data.pools.length > 0) {
            data.pools.forEach((pool, index) => {
                const item = document.createElement('div');
                item.className = `rank-item top-${index + 1}`;
                const identity = document.createElement('span');
                const score = document.createElement('span');
                identity.textContent = `#${index + 1} [${pool.pool_name}]`;
                score.textContent = Number(pool.score).toLocaleString();
                item.append(identity, score);
                listEl.appendChild(item);
            });
        } else {
            const emptyState = document.createElement('div');
            emptyState.className = 'loading-state';
            emptyState.textContent = 'Nenhuma pool registrada.';
            listEl.appendChild(emptyState);
        }
    } catch (error) {
        if (error.name !== 'AbortError') console.error("Erro ao buscar pools.", error);
    } finally {
        requestControllers.delete(controller);
        if (poolsRequestController === controller) {
            poolsRequestController = undefined;
        }
    }
}

/**
 * Envia a maior pontuacao local para a API do leaderboard.
 */
async function submitScore() {
    const realmId = activeRealmId;
    const generation = sessionGeneration;
    if (!realmId || !sessionReady) return;
    const controller = new AbortController();
    requestControllers.add(controller);
    try {
        const response = await fetch(leaderboardUrl(realmId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: minerName,
                pool_name: poolName || null,
                score: balanceSatoshis,
            }),
            signal: controller.signal
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        if (generation === sessionGeneration && realmId === activeRealmId) {
            void fetchLeaderboard(realmId, generation);
            /* Fase 7: Tracking — score enviado */
            trackScoreSubmitted(balanceSatoshis);
        }
    } catch(error) {
        if (error.name !== 'AbortError') console.error("Erro ao enviar a pontuação.", error);
    } finally {
        requestControllers.delete(controller);
    }
}

/**
 * Fase 3: Sincroniza estado do jogador com o backend.
 *
 * Fase 5.3: o backend é a fonte de verdade do saldo (earn/spend via
 * /earn e /spend). O sync envia o saldo local, mas o backend só o aplica
 * quando o saldo armazenado é 0 (migração do primeiro uso) — um saldo
 * local inflado (earn em falha de rede) ou stale (duas abas) NÃO
 * sobrescreve o saldo do backend.
 *
 * Fase 2 (pontas soltas): retry com backoff — o sync é a ponte entre o
 * estado local (hardware/lightning) e o backend (Redis).
 */
async function syncPlayerState(retries = 2) {
    const realmId = activeRealmId;
    const generation = sessionGeneration;
    if (!realmId || !sessionReady || !minerName) return;
    const controller = new AbortController();
    requestControllers.add(controller);
    try {
        const response = await fetch(playerStateUrl(realmId, minerName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: minerName,
                balance: balanceSatoshis,
                hardware_level: hardwareLevel,
                lightning_active: isLightningMode,
                lightning_blocks_remaining: lightningBlocksRemaining,
                combo_multiplier: comboMultiplier,
            }),
            signal: controller.signal
        });
        if (!response.ok && retries > 0) {
            // Retry com backoff (500ms * tentativa) para falhas transitórias.
            await new Promise(r => setTimeout(r, 500 * (3 - retries)));
            requestControllers.delete(controller);
            return syncPlayerState(retries - 1);
        }
    } catch(error) {
        if (error.name !== 'AbortError') {
            console.warn("Erro ao sincronizar estado do jogador.", error);
            if (retries > 0) {
                await new Promise(r => setTimeout(r, 500 * (3 - retries)));
                requestControllers.delete(controller);
                return syncPlayerState(retries - 1);
            }
        }
    } finally {
        requestControllers.delete(controller);
    }
}

/**
 * Fase 5.1/5.3: Credita sats ao saldo no backend (fonte de verdade).
 *
 * O backend é a fonte de verdade do saldo: o frontend envia o crédito
 * (recompensa da rodada, loot do boss, bônus MEV) e espelha o saldo
 * retornado. Idempotente por tx_id — reenviar o mesmo tx_id não credita
 * em dobro (retry após falha de rede é seguro).
 *
 * @param {number} amount - Sats a creditar.
 * @param {string} txId - Identificador único da transação (UUID).
 * @returns {Promise<number|null>} Novo saldo do backend, ou null em falha.
 */
async function earnBalance(amount, txId) {
    if (!activeRealmId || !minerName || amount <= 0) return null;
    /* Fase C4: retry com backoff — o tx_id é idempotente (marcador no
     * backend), então reenviar em falha de rede/5xx NÃO credita em dobro.
     * Antes era fire-and-forget: uma falha de rede perdia o crédito
     * (saldo local inflado, backend sem o valor). */
    const MAX_ATTEMPTS = 3;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        const controller = new AbortController();
        requestControllers.add(controller);
        try {
            const response = await fetch(
                playerStateUrl(activeRealmId, minerName) + '/earn',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: minerName, amount, tx_id: txId }),
                    signal: controller.signal,
                }
            );
            if (!response.ok) {
                // 4xx (exceto 429) não tem retry — erro de validação/saldo
                if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                    return null;
                }
                if (attempt === MAX_ATTEMPTS) return null;
            } else {
                const data = await response.json();
                return data.balance ?? null;
            }
        } catch (error) {
            if (error.name !== 'AbortError' && attempt === MAX_ATTEMPTS) {
                console.warn('Erro ao creditar saldo no backend (tentativas esgotadas).', error);
            }
        } finally {
            requestControllers.delete(controller);
        }
        // Backoff exponencial: 500ms, 1000ms
        await new Promise(r => setTimeout(r, 500 * attempt));
    }
    return null;
}

/**
 * Fase 5.1/5.3: Debita sats do saldo no backend (fonte de verdade).
 *
 * O backend valida o saldo antes de aceitar o débito — sem isso, o
 * frontend poderia "comprar" com saldo local que não existe no backend
 * (compra de graça). Idempotente por tx_id.
 *
 * @param {number} amount - Sats a debitar.
 * @param {string} txId - Identificador único da transação (UUID).
 * @returns {Promise<number|null>} Novo saldo do backend, ou null em falha
 *   (inclui saldo insuficiente — o caller deve reverter a compra local).
 */
async function spendBalance(amount, txId) {
    if (!activeRealmId || !minerName || amount <= 0) return null;
    const controller = new AbortController();
    requestControllers.add(controller);
    try {
        const response = await fetch(
            playerStateUrl(activeRealmId, minerName) + '/spend',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: minerName, amount, tx_id: txId }),
                signal: controller.signal,
            }
        );
        if (!response.ok) return null;
        const data = await response.json();
        return data.balance ?? null;
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.warn('Erro ao debitar saldo no backend.', error);
        }
        return null;
    } finally {
        requestControllers.delete(controller);
    }
}

/**
 * Fase 3: Carrega estado do jogador do backend ao iniciar sessão.
 *
 * Fase 5.3: backend é a fonte de verdade do saldo — o frontend ESPELHA o
 * saldo do backend (não mais "quem tiver mais, vence"). Se o backend está
 * 0 mas o local tem saldo > 0 (ex.: primeiro uso, ou o backend perdeu o
 * estado), empurra o valor local para o backend via syncPlayerState() para
 * que compras funcionem.
 */
async function loadPlayerState(realmId, username) {
    if (!realmId || !username) return;
    const sessionContext = captureSessionContext(realmId, username);
    try {
        const response = await fetch(playerStateUrl(realmId, username));
        if (!response.ok) return;
        const state = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        // Fase 5.3: espelha o saldo do backend (fonte de verdade).
        // O local só é empurrado para o backend quando o backend está 0
        // (primeiro uso / migração) — nunca quando o backend tem saldo,
        // para não sobrescrever o valor da fonte de verdade.
        // Fase A1: espelha SEMPRE quando o backend tem saldo > 0 (antes:
        // só quando backend > local, o que impedia o débito de energia
        // de atualizar o HUD — "cold wallet não desconta").
        if (state.balance > 0) {
            balanceSatoshis = state.balance;
        } else if (balanceSatoshis > 0 && state.balance === 0) {
            void syncPlayerState();
        }
        if (state.hardware_level > 1) {
            hardwareLevel = state.hardware_level;
            networkTimeBonus = (hardwareLevel - 1) * 10;
        }
        if (state.lightning_active) {
            isLightningMode = true;
            lightningBlocksRemaining = state.lightning_blocks_remaining;
            document.body.classList.add('lightning-theme');
        }
        /* Season Pass: bônus de recompensa temporário (+5%/+10%) */
        seasonRewardBonus = state.reward_bonus_percent || 0;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        document.getElementById('ui-hw').innerText = hardwareNames[hardwareLevel - 1];
        saveSessionState(); /* Fase 1: salva após carregar estado */
    } catch(error) {
        console.warn("Erro ao carregar estado do jogador.", error);
    }
}

/**
 * Atualiza preços, rótulos e disponibilidade dos upgrades.
 */
function updateStoreUI() {
    document.getElementById('btn-buy-hint').disabled = balanceSatoshis < HINT_PRICE || !isPlaying;

    const hwBtn = document.getElementById('btn-buy-hw');
    const hwTitle = document.getElementById('hw-title');

    if (hardwareLevel >= hardwareNames.length) {
        hwTitle.innerText = "MAX TIER REACHED"; hwBtn.innerText = "SOLD OUT"; hwBtn.disabled = true;
    } else {
        const nextPrice = hardwarePrices[hardwareLevel - 1];
        hwTitle.innerText = `Upgrade: ${hardwareNames[hardwareLevel]}`;
        hwBtn.innerText = `${nextPrice.toLocaleString()} SATS`;
        hwBtn.disabled = balanceSatoshis < nextPrice;
    }

    const lnBtn = document.getElementById('btn-buy-ln');
    if(isLightningMode) {
        /* Fase 3: mostra blocos restantes do canal */
        lnBtn.innerText = `NODE ACTIVE (${lightningBlocksRemaining} BLK)`;
        lnBtn.disabled = true;
    } else {
        lnBtn.innerText = `${LIGHTNING_PRICE.toLocaleString()} SATS`;
        lnBtn.disabled = balanceSatoshis < LIGHTNING_PRICE || isPlaying;
    }
}

/**
 * Compra e aplica uma dica à primeira palavra ainda não encontrada.
 *
 * Fase 5.1: o débito é validado no backend (fonte de verdade do saldo).
 * A dica só é aplicada localmente se o backend confirmar o débito — sem
 * isso, o jogador poderia "comprar" com saldo local que não existe no
 * backend (compra de graça).
 *
 * Fase 5 (auditoria): trava de "em andamento" — dois cliques no mesmo
 * milissegundo gerariam o mesmo tx_id e o 2º spend seria tratado como
 * idempotente (confirmado) → 2ª dica grátis.
 */
let hintPurchaseInFlight = false;
async function buyHint() {
    if (hintPurchaseInFlight) return;
    hintPurchaseInFlight = true;
    try {
        /* Fase 7: usa preço com desconto de conquistas/skill tree */
        const price = getHintPrice();
        if (balanceSatoshis < price || !isPlaying) return;
        const unfound = blockWords.find(w => !w.found && !w.hinted);
        if (!unfound) return;
        const txId = `spend-hint-${activeRealmId}-${roundNumber}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        const confirmed = await spendBalance(price, txId);
        if (confirmed === null) return; /* backend recusou (saldo insuficiente/falha) */
        /* Backend confirmou o débito — aplica a dica e espelha o saldo */
        balanceSatoshis = confirmed;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        playSound('buy');
        unfound.hinted = true;
        grid[unfound.startY][unfound.startX].element.classList.add('hint-glow');
        updateStoreUI(); submitScore();
        saveSessionState(); /* Fase 1: salva após compra de dica */
    } finally {
        hintPurchaseInFlight = false;
    }
}

/**
 * Compra o próximo nível de hardware e amplia o tempo de rodada.
 *
 * Fase 5.1: o débito é validado no backend (fonte de verdade do saldo).
 * O upgrade só é aplicado localmente se o backend confirmar o débito.
 */
async function buyHardware() {
    if (hardwareLevel >= hardwareNames.length) return;
    const nextPrice = hardwarePrices[hardwareLevel - 1];
    if (balanceSatoshis < nextPrice) return;
    const txId = `spend-hw-${activeRealmId}-${hardwareLevel}-${Date.now()}`;
    const confirmed = await spendBalance(nextPrice, txId);
    if (confirmed === null) return; /* backend recusou */
    /* Backend confirmou o débito — aplica o upgrade e espelha o saldo */
    balanceSatoshis = confirmed;
    document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
    playSound('buy');
    networkTimeBonus += 10;
    if (isPlaying && !isLightningMode) {
        networkTimeLimit += 10;
        /* Fase 7: estende o endTime do timer por timestamp — sem isso,
         * o +10s do hardware não valeria na rodada em andamento. */
        raceEndTime += 10 * 1000;
        updateRaceLimitLabel();
    }
    document.getElementById('ui-hw').innerText = hardwareNames[hardwareLevel];
    hardwareLevel++; updateStoreUI(); submitScore();
    saveSessionState(); /* Fase 1: salva após compra de hardware */
    // Sincroniza hardware_level no backend (o saldo já foi debitado via /spend)
    void syncPlayerState();
}

/**
 * Ativa o upgrade Lightning simulado depois de debitar o saldo fictício.
 *
 * Fase 5.1: o débito é validado no backend (fonte de verdade do saldo).
 * O estado do Lightning só é ativado localmente se o backend confirmar o
 * débito — sem isso, o jogador poderia ativar o Lightning de graça.
 */
async function buyLightning() {
    if (balanceSatoshis < LIGHTNING_PRICE || isLightningMode || isPlaying || isTransitioning) return;
    const txId = `spend-ln-${activeRealmId}-${Date.now()}`;
    const confirmed = await spendBalance(LIGHTNING_PRICE, txId);
    if (confirmed === null) return; /* backend recusou */
    /* Backend confirmou o débito — ativa o Lightning e espelha o saldo */
    isTransitioning = true;
    isLightningMode = true;
    /* Fase 3: Lightning Channel Liquidity — canal dura LIGHTNING_CHANNEL_DURATION blocos */
    lightningBlocksRemaining = LIGHTNING_CHANNEL_DURATION;
    balanceSatoshis = confirmed;
    document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
    playSound('buy');
    document.body.classList.add('lightning-theme');
    document.getElementById('result-title').style.color = "var(--lightning-blue)";
    updateStoreUI(); submitScore();
    saveSessionState(); /* Fase 1: salva após compra de Lightning */
    // Sincroniza lightning_active no backend (o saldo já foi debitado via /spend)
    void syncPlayerState();

    const term = document.getElementById('lightning-modal');
    const termText = document.getElementById('lightning-text');
    setModalState(term, true);
    termText.textContent = "> INIT LIGHTNING_DAEMON\n";

    const generation = sessionGeneration;
    scheduleForSession(() => { termText.textContent += "> FINDING PEERS... [OK]\n"; }, 800, generation);
    scheduleForSession(() => { termText.textContent += "> OPENING CHANNEL (SIMULADO)... [OK]\n"; }, 1600, generation);
    scheduleForSession(() => {
        termText.textContent += `> ZERO-CONF SIMULADO. LIGHTNING MODE ACTIVE.\n`;
        termText.textContent += `> CHANNEL CAPACITY: ${LIGHTNING_CHANNEL_DURATION} BLOCKS\n`;
        scheduleForSession(() => {
            setModalState(term, false);
            isTransitioning = false;
            if (!isPlaying && txBuffer.length === WORDS_PER_BLOCK) {
                void requestPlayableBlockBuild();
            }
        }, 1500, generation);
    }, 2500, generation);
}

/**
 * Fase A2: processa um evento de transação (ao vivo ou replay).
 *
 * Extrai a lógica do handler de `transaction_received` para que o replay de
 * transações pendentes no `game_start` possa reutilizá-la. Deduplica por
 * `word`, respeita `isBossActive` e dispara o build quando o buffer completa.
 */
function handleTransactionEvent(data) {
    if (!isValidTransactionEvent(data)) {
        console.warn("Evento de transação fora do contrato foi ignorado.");
        return;
    }
    if (activeEpoch && data.epoch && data.epoch !== activeEpoch) {
        txBuffer = [];
        activeEpoch = data.epoch;
    }
    // Boss Battles: roteia transações para o buffer do boss quando ativo
    if (isBossActive) {
        handleBossTransaction(data);
        return;
    }
    if (txBuffer.length < WORDS_PER_BLOCK) {
        if (!txBuffer.find(t => t.word === data.word)) {
            txBuffer.push({ word: data.word, isHighFee: data.is_high_fee, isGolden: data.is_golden, vsize: data.vsize, isMev: data.is_mev, multiplier: data.multiplier });
            const loadingText = document.getElementById('tx-loading-bank');
            if (loadingText) loadingText.innerText = `Aguardando transações (${txBuffer.length}/${WORDS_PER_BLOCK})...`;
            /* Fase A3: registra atividade e reinicia o watchdog de buffer */
            lastTxActivityTime = Date.now();
            startTxBufferWatchdog();
            if (txBuffer.length === WORDS_PER_BLOCK && !isTransitioning) {
                cancelSessionTimeout(pendingBuildTimeout);
                pendingBuildTimeout = scheduleForSession(() => {
                    pendingBuildTimeout = undefined;
                    void requestPlayableBlockBuild();
                }, 500, generation);
            }
        }
    }
}

/**
 * Fase A3: watchdog de buffer — se o buffer ficar parado por 45s sem
 * completar as 6 palavras e a rede estiver jogável, força reconexão.
 * A reconexão dispara o replay de transações pendentes (Fase A2), o que
 * normalmente completa o buffer e destrava o jogo.
 */
function startTxBufferWatchdog() {
    if (txBufferWatchdog) return; // já ativo
    txBufferWatchdog = setInterval(() => {
        // Só age se a sessão está pronta, não está jogando, não está em boss
        // block e o buffer está incompleto MAS já tem algumas palavras
        // (parou no meio, não é buffer recém-limpo com 0 palavras).
        if (!sessionReady || isPlaying || isBossActive || txBuffer.length >= WORDS_PER_BLOCK) {
            return;
        }
        if (txBuffer.length === 0) return; // buffer vazio — ainda não começou
        const stalled = Date.now() - lastTxActivityTime > TX_BUFFER_STALL_MS;
        if (stalled) {
            console.warn(`Watchdog: buffer parado há ${Math.round((Date.now() - lastTxActivityTime) / 1000)}s com ${txBuffer.length}/${WORDS_PER_BLOCK} palavras. Forçando reconexão.`);
            clearInterval(txBufferWatchdog);
            txBufferWatchdog = null;
            // Força reconexão: teardown + startSession
            const realmToReconnect = activeRealmId;
            teardownSession('tx-buffer-stall');
            void startSession(realmToReconnect);
        }
    }, 5000); // verifica a cada 5s
}

/**
 * Limpa a rodada anterior e volta ao estado de coleta de transações.
 */
function prepareNextBlock() {
    clearInterval(networkInterval);
    setNextButtonAction(null);
    setModalState(document.getElementById('result-modal'), false);
    selectedCells.forEach(({ cell }) => {
        cell.classList.remove('selected');
        cell.setAttribute('aria-selected', 'false');
    });
    selectedCells = [];
    isSelecting = false;
    activePointerId = null;
    isPlaying = false; txBuffer = []; wordsFoundInBlock = 0; currentRoundEarnings = 0; networkTimePassed = 0; netProgressEl.style.width = '0%';
    roundSettled = false; /* Fase 6: nova rodada — libera o timer para expirar de novo */
    lastTxActivityTime = Date.now(); /* Fase A3: reseta o watchdog para a nova rodada */
    roundAttempt++; /* Fase C1: nova tentativa de rodada — tx_ids de earn ficam únicos */
    netProgressEl.setAttribute('aria-valuenow', '0');
    netProgressEl.setAttribute('aria-valuetext', 'Aguardando uma rodada');
    bankEl.innerHTML = `<div class="loading-state" id="tx-loading-bank">Aguardando transacoes (0/${WORDS_PER_BLOCK})...</div>`;
    overlayEl.classList.remove('hidden'); updateStoreUI();
    consecutiveErrors = 0; /* Fase 1: reseta erros entre rodadas */
    resetRoundPowerups(); /* Power-ups: reseta efeitos de rodada entre rodadas */
    announceGameStatus(`Aguardando ${WORDS_PER_BLOCK} transacoes da rede ativa.`);
}

/**
 * Mantém a coleta visível quando não há energia para iniciar uma rodada.
 */
function showPendingEnergyState(bossDiscarded = false) {
    isPlaying = false;
    overlayEl.classList.remove('hidden');
    const loaderText = overlayEl.querySelector('#tx-loading');
    if (loaderText) {
        loaderText.innerText = 'Energia insuficiente. Aguarde a recarga ou compre energia.';
    }
    const bankLoadingText = document.getElementById('tx-loading-bank');
    if (bankLoadingText) {
        /* Fase 4.1: no descarte do boss o buffer foi limpo — a rodada recomeça de 0 */
        bankLoadingText.innerText = bossDiscarded
            ? `Boss descartado. Aguardando transações (0/${WORDS_PER_BLOCK})...`
            : `Rodada pronta (${WORDS_PER_BLOCK}/${WORDS_PER_BLOCK}). Aguardando energia...`;
    }
    announceGameStatus(bossDiscarded
        ? 'Boss descartado. Aguarde a recarga ou compre energia para continuar.'
        : 'Rodada pronta. Aguarde a recarga ou compre energia para continuar.');
}

/**
 * Consome energia antes de expor a grade e evita cobranças concorrentes.
 */
async function requestPlayableBlockBuild() {
    if (
        energyGatePending
        || isTransitioning
        || isPlaying
        || !sessionReady
        || !ws
        || ws.readyState !== WebSocket.OPEN
        || txBuffer.length !== WORDS_PER_BLOCK
    ) return;

    const generation = sessionGeneration;
    const roundRealm = activeRealmId;
    const roundMiner = minerName;
    const roundId = reservePendingEnergySpend(roundRealm, roundMiner);
    energyGatePending = true;
    try {
        const hasEnergy = await spendEnergy(roundId, roundRealm, roundMiner);
        if (
            generation !== sessionGeneration
            || !sessionReady
            || txBuffer.length !== WORDS_PER_BLOCK
        ) {
            if (hasEnergy) {
                await queueEnergyRefund(roundId, roundRealm, roundMiner);
                clearPendingEnergySpend(roundId);
            } else if (hasEnergy === false) {
                clearPendingEnergySpend(roundId);
            }
            pendingEnergyRoundId = null;
            return;
        }
        if (hasEnergy === null) {
            isPlaying = false;
            overlayEl.classList.remove('hidden');
            announceGameStatus('Não foi possível confirmar a energia. Sincronizando estado...');
            return;
        }
        if (hasEnergy === false) {
            clearPendingEnergySpend(roundId);
            showPendingEnergyState();
            return;
        }
        const blockStarted = buildPlayableBlock();
        if (!blockStarted) {
            await queueEnergyRefund(roundId, roundRealm, roundMiner);
            clearPendingEnergySpend(roundId);
            showPendingEnergyState();
            return;
        }
        clearPendingEnergySpend(roundId);
    } finally {
        if (generation === sessionGeneration) {
            energyGatePending = false;
        }
    }
}

/**
 * Define a dificuldade, constrói a grade e inicia a corrida contra a rede.
 */
function buildPlayableBlock(buildAttempt = 0) {
    if (
        isTransitioning
        || !sessionReady
        || !ws
        || ws.readyState !== WebSocket.OPEN
        || txBuffer.length !== WORDS_PER_BLOCK
    ) return false;
    overlayEl.classList.add('hidden');
    gridEl.innerHTML = ''; svgEl.innerHTML = ''; bankEl.innerHTML = '';
    grid = []; blockWords = []; currentRoundEarnings = 0; isPlaying = true;

    // Análise Dinâmica de Tamanho (vsize)
    const maxVsize = Math.max(...txBuffer.map(t => t.vsize));

    /* Fase 3: Eventos Globais — sobrepõem grade/tempo.
       A recompensa do evento é aplicada pelo BACKEND via match.multiplier
       (game.js:2819), então NÃO se multiplica aqui (evita double-counting). */
    const globalEventType = activeGlobalEvent?.type || null;
    if (globalEventType === 'lightning_storm') {
        currentGridSize = 8; // Condensado
        networkTimeLimit = 20; // Ultra rápido
    } else if (globalEventType === 'mempool_flood') {
        currentGridSize = 15; // Grade pesada obrigatória
        networkTimeLimit = 75 + getNetworkTimeBonus();
    } else if (globalEventType === 'fee_spike') {
        if (isLightningMode) { currentGridSize = 8; networkTimeLimit = 20; }
        else if (maxVsize > 1000) { currentGridSize = 15; networkTimeLimit = 75 + getNetworkTimeBonus(); }
        else { currentGridSize = 12; networkTimeLimit = 60 + getNetworkTimeBonus(); }
    } else if (globalEventType === 'golden_rush') {
        if (isLightningMode) { currentGridSize = 8; networkTimeLimit = 20; }
        else if (maxVsize > 1000) { currentGridSize = 15; networkTimeLimit = 75 + getNetworkTimeBonus(); }
        else { currentGridSize = 12; networkTimeLimit = 60 + getNetworkTimeBonus(); }
    } else if (isLightningMode) {
        currentGridSize = 8; // Condensado
        networkTimeLimit = 20; // Ultra rápido
    } else if (maxVsize > 1000) {
        currentGridSize = 15; // Bloco pesado
        networkTimeLimit = 75 + getNetworkTimeBonus();
    } else {
        currentGridSize = 12; // Padrão
        networkTimeLimit = 60 + getNetworkTimeBonus();
    }
    // Fase 2: Halving Protocol — tempo fica 1s mais curto a cada bloco
    const halvingPenalty = Math.min(roundNumber - 1, 30); // Máx 30s de penalidade
    networkTimeLimit += baseTimeLimit - 60;
    networkTimeLimit = Math.max(networkTimeLimit - halvingPenalty, 15); // Mínimo 15s
    // Fase 2: Halving Protocol — baseReward decresce 2% a cada 10 blocos
    const halvingRewardFactor = Math.max(1 - (Math.floor(roundNumber / 10) * 0.02), 0.5); // Mínimo 50%
    // O multiplicador do evento global é aplicado pelo backend (match.multiplier),
    // então aqui só entra o fator de halving (evita double-counting).
    effectiveBaseReward = Math.floor(baseReward * halvingRewardFactor);

    configureGridSize(currentGridSize);

    document.getElementById('ui-block').innerText = `#${roundNumber.toLocaleString()}`;

    for (let y = 0; y < currentGridSize; y++) {
        let row = [];
        for (let x = 0; x < currentGridSize; x++) {
            const cell = document.createElement('div'); cell.className = 'cell'; cell.dataset.x = x; cell.dataset.y = y;
            cell.tabIndex = x === 0 && y === 0 ? 0 : -1;
            cell.setAttribute('role', 'gridcell');
            cell.setAttribute('aria-selected', 'false');
            gridEl.appendChild(cell); row.push({ element: cell, char: '', isFound: false });
        }
        grid.push(row);
    }

    const allWordsPlaced = txBuffer.every(
        tx => injectWordInGrid(tx.word, tx.isHighFee, tx.isGolden, tx.isMev, tx.multiplier)
    );
    const safeGridFilled = allWordsPlaced && fillGridWithoutIncidentalWords();
    if (!safeGridFilled) {
        if (buildAttempt < 4) {
            return buildPlayableBlock(buildAttempt + 1);
        }
        isPlaying = false;
        overlayEl.classList.remove('hidden');
        const loaderText = overlayEl.querySelector('#tx-loading');
        if (loaderText) loaderText.innerText = "Falha ao montar a grade. Aguarde o próximo conjunto.";
        return false;
    }

    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            grid[y][x].element.innerText = grid[y][x].char;
            grid[y][x].element.setAttribute('aria-label', `Letra ${grid[y][x].char}, linha ${y + 1}, coluna ${x + 1}`);
        }
    }

    updateStoreUI();
    announceGameStatus('Rodada iniciada. Arraste nas letras ou use setas e Enter.');
    /* Power-ups: aplica efeitos pendentes no início da rodada */
    applyPendingPowerups();
    startNetworkRace();
    return true;
}

/**
 * Posiciona uma palavra sem sobreposicao e registra seu item na lista lateral.
 * Fase 6: palavras MEV sao injetadas sem aparecer no word bank.
 */
function injectWordInGrid(word, isHighFee, isGolden, isMev = false, multiplier = 1.0) {
    /* Fase 6.4: removido o truncamento de palavras > grid — as palavras
     * BIP39 têm no máximo 6 caracteres e o grid mínimo é 8×8 (normal) ou
     * 15×15 (boss), então o truncamento nunca dispara. */

    const dirs = [[1, 0], [0, 1], [1, 1], [1, -1]];
    for (let attempts = 0; attempts < 200; attempts++) {
        const dir = dirs[Math.floor(Math.random() * dirs.length)];
        const startX = Math.floor(Math.random() * currentGridSize);
        const startY = Math.floor(Math.random() * currentGridSize);
        const endX = startX + dir[0] * (word.length - 1);
        const endY = startY + dir[1] * (word.length - 1);

        if (endX >= 0 && endX < currentGridSize && endY >= 0 && endY < currentGridSize) {
            let canPlace = true;
            for (let i = 0; i < word.length; i++) {
                const cx = startX + dir[0] * i; const cy = startY + dir[1] * i;
                if (grid[cy][cx].char !== '') { canPlace = false; break; }
            }
            if (canPlace) {
                const coords = Array.from({ length: word.length }, (_, index) => ({
                    x: startX + dir[0] * index,
                    y: startY + dir[1] * index
                }));
                coords.forEach(({ x, y }, index) => { grid[y][x].char = word[index]; });
                blockWords.push({
                    word, found: false, isHighFee, isGolden, startX, startY,
                    coords, hinted: false, isMev: isMev, multiplier: multiplier
                });

                /* Fase 6: palavras MEV nao aparecem no word bank (secretas) */
                if (!isMev) {
                    renderBankWord(word, isHighFee, isGolden);
                }
                return true;
            }
        }
    }

    // Fallback determinístico: as palavras BIP39 cabem em linhas vazias.
    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x <= currentGridSize - word.length; x++) {
            const segment = Array.from({ length: word.length }, (_, index) => grid[y][x + index]);
            if (segment.every(cell => cell.char === '')) {
                segment.forEach((cell, index) => { cell.char = word[index]; });
                const coords = Array.from({ length: word.length }, (_, index) => ({
                    x: x + index,
                    y
                }));
                blockWords.push({
                    word, found: false, isHighFee, isGolden, startX: x, startY: y,
                    coords, hinted: false, isMev: isMev, multiplier: multiplier
                });
                /* Fase 6: palavras MEV nao aparecem no word bank (secretas) */
                if (!isMev) {
                    renderBankWord(word, isHighFee, isGolden);
                }
                return true;
            }
        }
    }

    console.error(`Não foi possível inserir a palavra ${word} na grade.`);
    return false;
}

const WORD_SEARCH_DIRECTIONS = [[1, 0], [0, 1], [1, 1], [1, -1]];

function normalizedCoordinatePath(coords) {
    const forward = coords.map(({ x, y }) => `${x},${y}`).join('|');
    const reverse = [...coords].reverse().map(({ x, y }) => `${x},${y}`).join('|');
    return forward < reverse ? forward : reverse;
}

function selectionMatchesOfficialPath(target, selection) {
    if (!Array.isArray(target?.coords) || target.coords.length !== selection.length) return false;
    const selectedCoords = selection.map(({ x, y }) => ({ x, y }));
    return normalizedCoordinatePath(target.coords) === normalizedCoordinatePath(selectedCoords);
}

function hasIncidentalTargetOccurrence() {
    const targets = new Map();
    blockWords.forEach(target => {
        if (!targets.has(target.word)) targets.set(target.word, new Set());
        targets.get(target.word).add(normalizedCoordinatePath(target.coords));
    });

    for (const [word, officialPaths] of targets) {
        const reversedWord = [...word].reverse().join('');
        for (let startY = 0; startY < currentGridSize; startY++) {
            for (let startX = 0; startX < currentGridSize; startX++) {
                for (const [dx, dy] of WORD_SEARCH_DIRECTIONS) {
                    const endX = startX + dx * (word.length - 1);
                    const endY = startY + dy * (word.length - 1);
                    if (endX < 0 || endX >= currentGridSize || endY < 0 || endY >= currentGridSize) continue;
                    const coords = Array.from({ length: word.length }, (_, index) => ({
                        x: startX + dx * index,
                        y: startY + dy * index
                    }));
                    const candidate = coords.map(({ x, y }) => grid[y][x].char).join('');
                    if (
                        (candidate === word || candidate === reversedWord)
                        && !officialPaths.has(normalizedCoordinatePath(coords))
                    ) return true;
                }
            }
        }
    }
    return false;
}

function fillGridWithoutIncidentalWords(maxAttempts = 200) {
    const officialCells = new Set(
        blockWords.flatMap(target => target.coords.map(({ x, y }) => `${x},${y}`))
    );
    const fillerCells = [];
    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            if (!officialCells.has(`${x},${y}`)) fillerCells.push(grid[y][x]);
        }
    }
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        fillerCells.forEach(cell => {
            cell.char = String.fromCharCode(65 + Math.floor(Math.random() * 26));
        });
        if (!hasIncidentalTargetOccurrence()) return true;
    }
    /* Fase 6.5: fallback — se 200 tentativas não bastaram, preenche com
     * letras que não formam palavras do word bank (mais seguro que falhar). */
    fillerCells.forEach(cell => {
        cell.char = 'X';
    });
    return true;
}

/**
 * Cria o item de uma palavra usando somente APIs seguras do DOM.
 */
function renderWordBank() {
    bankEl.replaceChildren();
    gridEl.replaceChildren();
    svgEl.replaceChildren();
    grid = [];
    blockWords = [];
    selectedCells = [];
    isPlaying = true;

    for (let y = 0; y < currentGridSize; y++) {
        const row = [];
        for (let x = 0; x < currentGridSize; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.tabIndex = x === 0 && y === 0 ? 0 : -1;
            cell.setAttribute('role', 'gridcell');
            cell.setAttribute('aria-selected', 'false');
            gridEl.appendChild(cell);
            row.push({ element: cell, char: '', isFound: false });
        }
        grid.push(row);
    }

    const uniqueWords = [...new Set(
        currentRoundWords
            .map(rawWord => String(rawWord).toUpperCase().slice(0, currentGridSize))
            .filter(Boolean)
    )];
    currentRoundWords = uniqueWords;
    const allWordsPlaced = uniqueWords.every(
        word => injectWordInGrid(word, false, false, false, 1.0)
    );
    if (!allWordsPlaced || !fillGridWithoutIncidentalWords()) {
        isPlaying = false;
        return false;
    }

    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            const cell = grid[y][x];
            cell.element.textContent = cell.char;
            cell.element.setAttribute(
                'aria-label',
                `Letra ${cell.char}, linha ${y + 1}, coluna ${x + 1}`
            );
        }
    }
    return true;
}


function renderBankWord(word, isHighFee, isGolden) {
    // Evita duplicar itens quando a mesma palavra aparece mais de uma vez
    // no bloco (ex.: duas transações com a mesma palavra BIP39).
    if (bankEl.querySelector(`.word-item[data-word="${word}"]`)) {
        return;
    }
    const item = document.createElement('div');
    const wordText = document.createElement('span');
    const tag = document.createElement('span');
    item.className = 'word-item';
    // ID único: suporta palavras repetidas no mesmo bloco (antes era
    // `bank-${word}`, que gerava IDs duplicados no DOM).
    item.id = `bank-${word}-${bankEl.children.length}`;
    item.dataset.word = word;
    wordText.className = 'word-text';
    wordText.textContent = word;
    tag.className = 'word-fee fee-low';
    tag.textContent = 'STD FEE';
    if (isGolden) {
        tag.className = 'word-fee fee-golden';
        tag.textContent = 'GOLDEN HASH';
    } else if (isHighFee) {
        tag.className = 'word-fee fee-high';
        tag.textContent = 'HIGH FEE';
    }
    item.append(wordText, tag);
    bankEl.appendChild(item);
}

/**
 * Resolve uma célula válida sob um ponto da tela.
 */
function getCellFromPoint(clientX, clientY) {
    const target = document.elementFromPoint(clientX, clientY);
    const cell = target?.closest?.('.cell');
    return cell && gridEl.contains(cell) ? cell : null;
}

/**
 * Mantém somente uma célula no fluxo de tabulação da grade.
 */
function focusGridCell(cell, shouldFocus = true) {
    gridEl.querySelectorAll('.cell[tabindex="0"]').forEach(item => {
        if (item !== cell) item.tabIndex = -1;
    });
    cell.tabIndex = 0;
    if (shouldFocus) cell.focus({ preventScroll: true });
}

/**
 * Inicia uma seleção por mouse, caneta ou toque sem duplicar handlers.
 */
function handlePointerStart(event) {
    if (
        !event.isPrimary
        || (event.pointerType === 'mouse' && event.button !== 0)
        || !isPlaying
    ) return;
    const cell = event.target.closest?.('.cell');
    if (!cell || !gridEl.contains(cell) || cell.classList.contains('found')) return;
    event.preventDefault();
    activePointerId = event.pointerId;
    focusGridCell(cell, event.pointerType === 'mouse');
    startSelection(cell, Number(cell.dataset.x), Number(cell.dataset.y));
}

/**
 * Estende a seleção acompanhando o ponteiro, inclusive sob captura implícita.
 */
function handlePointerMove(event) {
    if (event.pointerId !== activePointerId || !isSelecting) return;
    event.preventDefault();
    const cell = getCellFromPoint(event.clientX, event.clientY);
    if (!cell) return;
    continueSelection(cell, Number(cell.dataset.x), Number(cell.dataset.y));
}

/**
 * Conclui a tentativa associada ao ponteiro ativo.
 */
function handlePointerEnd(event) {
    if (event.pointerId !== activePointerId) return;
    activePointerId = null;
    endSelection();
}

/**
 * Cancela ponteiros interrompidos sem validar uma palavra parcial.
 */
function handlePointerCancel(event) {
    if (event.pointerId !== activePointerId) return;
    activePointerId = null;
    cancelSelection('Seleção cancelada.');
}

/**
 * Permite percorrer e selecionar a grade somente com o teclado.
 */
function handleGridKeydown(event) {
    const cell = event.target.closest?.('.cell');
    if (!cell || !gridEl.contains(cell)) return;
    const x = Number(cell.dataset.x);
    const y = Number(cell.dataset.y);
    const movement = {
        ArrowLeft: [-1, 0],
        ArrowRight: [1, 0],
        ArrowUp: [0, -1],
        ArrowDown: [0, 1]
    }[event.key];

    if (movement) {
        event.preventDefault();
        const nextX = Math.max(0, Math.min(currentGridSize - 1, x + movement[0]));
        const nextY = Math.max(0, Math.min(currentGridSize - 1, y + movement[1]));
        const nextCell = grid[nextY]?.[nextX]?.element
            || gridEl.querySelector(`.cell[data-x="${nextX}"][data-y="${nextY}"]`);
        if (!nextCell) return;
        focusGridCell(nextCell);
        if (isSelecting) continueSelection(nextCell, nextX, nextY);
        return;
    }

    if (event.key === 'Home' || event.key === 'End') {
        event.preventDefault();
        const nextX = event.key === 'Home' ? 0 : currentGridSize - 1;
        const nextCell = grid[y]?.[nextX]?.element
            || gridEl.querySelector(`.cell[data-x="${nextX}"][data-y="${y}"]`);
        if (nextCell) focusGridCell(nextCell);
        return;
    }

    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        if (!isPlaying) {
            announceGameStatus('Aguarde o início de uma rodada antes de selecionar.');
            return;
        }
        if (isSelecting) {
            endSelection();
        } else {
            startSelection(cell, x, y);
        }
        return;
    }

    if (event.key === 'Escape' && isSelecting) {
        event.preventDefault();
        cancelSelection('Seleção cancelada.');
    }
}

/**
 * Remove uma tentativa parcial e sincroniza o estado acessível.
 */
function cancelSelection(message = '') {
    if (!isSelecting && selectedCells.length === 0) return;
    selectedCells.forEach(({ cell }) => {
        cell.classList.remove('selected');
        cell.setAttribute('aria-selected', 'false');
    });
    selectedCells = [];
    isSelecting = false;
    activePointerId = null;
    if (message) announceGameStatus(message);
}

/**
 * Registra a primeira célula de uma tentativa.
 */
function startSelection(cell, x, y) {
    if(!isPlaying || cell.classList.contains('found')) return;
    cancelSelection();
    isSelecting = true;
    selectedCells = [{ cell, x, y }];
    cell.classList.add('selected');
    cell.setAttribute('aria-selected', 'true');
    announceGameStatus(`Seleção iniciada na letra ${cell.textContent}.`);
    playSound('tick');
}
/**
 * Adiciona células adjacentes mantendo uma única direção.
 */
function continueSelection(cell, x, y) {
    if (!isSelecting || cell.classList.contains('found')) return;
    const last = selectedCells[selectedCells.length - 1];
    const dx = Math.abs(x - last.x); const dy = Math.abs(y - last.y);
    const isAdjacent = dx <= 1 && dy <= 1 && (dx !== 0 || dy !== 0);
    if (!isAdjacent || selectedCells.find(c => c.x === x && c.y === y)) return;

    if (selectedCells.length >= 2) {
        const first = selectedCells[0];
        const second = selectedCells[1];
        const directionX = Math.sign(second.x - first.x);
        const directionY = Math.sign(second.y - first.y);
        if (x !== last.x + directionX || y !== last.y + directionY) return;
    }

    if (isAdjacent) {
        selectedCells.push({ cell, x, y });
        cell.classList.add('selected');
        cell.setAttribute('aria-selected', 'true');
        playSound('tick');
    }
}

/**
 * Valida a palavra selecionada, calcula a recompensa e encerra a tentativa.
 */
function endSelection() {
    if (!isSelecting) return;
    isSelecting = false;

    const match = blockWords.find(
        w => !w.found && selectionMatchesOfficialPath(w, selectedCells)
    );

    if (match) {
        playSound('success'); match.found = true; wordsFoundInBlock++;
        if (sprintRoundActive) sprintWordsFound = wordsFoundInBlock;
        consecutiveErrors = 0; /* Fase 1: reseta contador de erros ao acertar */

        const now = Date.now();
        /* Power-up Double Combo: teto de combo sobe de 4× para 6× */
        const comboCap = powerupEffects.double_combo ? 6.0 : 4.0;
        if (lastFoundTime !== 0 && now - lastFoundTime < 8000) { comboMultiplier = Math.min(comboMultiplier + 0.5, comboCap); }
        else { comboMultiplier = 1.0; }
        lastFoundTime = now;
        document.getElementById('ui-combo').innerText = `${comboMultiplier.toFixed(1)}×`;

        let points = (
            (effectiveBaseReward * (1 + skillRewardBonus))
            + (match.word.length * 50)
        ) * comboMultiplier;
        // Fase 3: Usa multiplicador do backend (GOLDEN=5×, HIGH FEE=3×)
        const backendMultiplier = match.multiplier || 1.0;
        points *= backendMultiplier;
        if (isLightningMode) points *= 10;
        /* Power-up Magnet: +50% de sats nas palavras da rodada */
        if (powerupEffects.magnet) points *= 1.5;
        /* Fase 7: Bônus de conquistas (recompensa %) */
        points = applyAchievementBonus(points);

        /* Boss Battles: multiplicador 5× e dano ao boss */
        if (isBossActive) {
            points *= bossRewardMultiplier;
            // Dano ao boss — diminui HP
            bossHp = Math.max(0, bossHp - 1);
            updateBossHpUI();
            // Flash de dano na barra de HP
            const bossHpBar = document.getElementById('boss-hp-bar');
            if (bossHpBar) {
                bossHpBar.classList.add('boss-hp-damage');
                scheduleForSession(() => bossHpBar.classList.remove('boss-hp-damage'), 300);
            }
            // Tremor na tela a cada dano
            document.body.classList.add('boss-shake');
            scheduleForSession(() => document.body.classList.remove('boss-shake'), 500);

            // Boss derrotado — todas as palavras encontradas
            if (bossHp <= 0 && !bossDefeatHandled) {
                bossDefeatHandled = true;
                /* Fase 6.2: marca a rodada como finalizada ANTES de qualquer
                 * delay — o tick do timer em andamento verifica essa flag e
                 * não dispara showResult("expirou") sobrepondo o modal de
                 * derrota do boss. */
                roundSettled = true;
                // Bonus de loot
                balanceSatoshis += bossLoot;
                currentRoundEarnings += bossLoot;
                document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
                /* Fase 5.1/5.3: credita o loot do boss no backend */
                void earnBalance(bossLoot, `earn-boss-${activeRealmId}-${roundAttempt}`);
                announceGameStatus(`BOSS DERROTADO! +${bossLoot.toLocaleString()} sats de loot!`);
                // Mostra modal de derrota do boss
                scheduleForSession(() => showBossDefeatModal(), 1000, sessionGeneration);
                // Limpa timer
                clearInterval(networkInterval);
                isPlaying = false;
            }
        }

        /* Fase 6: MEV Secreto — recompensa oculta de 50.000 sats */
        if (match.isMev) {
            const mevBonus = 50000;
            balanceSatoshis += mevBonus;
            currentRoundEarnings += mevBonus;
            document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
            /* Fase 5.1/5.3: credita o bônus MEV no backend */
            void earnBalance(mevBonus, `earn-mev-${activeRealmId}-${roundAttempt}-${wordsFoundInBlock}`);
            announceGameStatus(`MEV SECRETO ENCONTRADO! +${mevBonus.toLocaleString()} sats bonus.`);
        }

        currentRoundEarnings += Math.floor(points);
        balanceSatoshis += Math.floor(points);
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        saveSessionState(); /* Fase 1: salva após mudança de saldo */

        /* Fase 7: Tracking de achievements — palavra encontrada */
        trackWordFound(match.isGolden, match.isHighFee, match.isMev);
        trackCombo(comboMultiplier);

        /* Fase 2: XP — nível do jogador e season pass (100% do XP da palavra) */
        const wordXP = calculateWordXP(match.word, comboMultiplier);
        void addXP(wordXP);
        void addSeasonXP(wordXP);

        const firstCell = selectedCells[0].cell;
        showFloatingText(firstCell, points, match.isHighFee, match.isGolden);
        drawAnimatedLine(selectedCells[0].cell, selectedCells[selectedCells.length - 1].cell);

        selectedCells.forEach(c => {
            c.cell.classList.remove('selected');
            c.cell.classList.add('found');
            c.cell.classList.remove('hint-glow');
            c.cell.setAttribute('aria-selected', 'false');
            c.cell.setAttribute('aria-label', `${c.cell.getAttribute('aria-label')}. Palavra encontrada`);
        });
        document.querySelector(`.word-item[data-word="${match.word}"]`)?.classList.add('found');
        /* Fase 6: mensagem MEV já foi mostrada acima, usa mensagem genérica apenas para palavras normais */
        if (!match.isMev) {
            announceGameStatus(
                `${match.word} encontrada. ${Math.floor(points).toLocaleString()} sats simulados adicionados.`
            );
        }
        updateStoreUI(); submitScore();
        /* Fase 5.1/5.3: backend é a fonte de verdade do saldo — credita a
         * recompensa da palavra no backend (idempotente por tx_id). O saldo
         * local já foi atualizado acima para feedback imediato; o valor
         * retornado pelo backend é a referência. */
        void earnBalance(Math.floor(points), `earn-${activeRealmId}-${roundAttempt}-${wordsFoundInBlock}`);

        if (wordsFoundInBlock === blockWords.length) {
            clearInterval(networkInterval);
            isPlaying = false;
            /* Fase 6 (pontas soltas): marca a rodada como finalizada ANTES de
             * qualquer delay — o tick do timer em andamento verifica essa flag
             * e não sobrescreve o sucesso com "expirou". */
            roundSettled = true;
            if (sprintRoundActive) {
                void endSprintRound('completed');
            } else if (bossDefeatHandled) {
                maxRoundEarningsTotal = Math.max(maxRoundEarningsTotal, currentRoundEarnings);
                void pushStats({ max_round_earnings: maxRoundEarningsTotal });
                roundNumber++;
                trackBlockCompleted();
                void claimFreeCrates();
            } else {
                scheduleForSession(() => showResult(
                    true,
                    isLightningMode
                        ? "Rodada L2 simulada concluída."
                        : "Todas as palavras foram encontradas antes do cronômetro."
                ), 600, sessionGeneration);
            }
        }
    } else {
        /* Fase 1: Slashing — penalidade por erro repetido */
        consecutiveErrors++;
        /* Fase 5.4: erro quebra a streak de palavras sem erro */
        wordsWithoutErrorStreak = 0;
        void pushStats({ words_without_error: 0 });
        selectedCells.forEach(c => {
            c.cell.classList.remove('selected');
            c.cell.setAttribute('aria-selected', 'false');
        });
        announceGameStatus('A selecao nao corresponde a uma transacao pendente.');
        comboMultiplier = 1.0; document.getElementById('ui-combo').innerText = `1.0×`;

        /* Se 3+ erros consecutivos, debita 5% do saldo (slashing) — Power-up Precision isenta a rodada */
        if (consecutiveErrors >= SLASHING_THRESHOLD && !powerupEffects.precision) {
            const penalty = Math.floor(balanceSatoshis * SLASHING_PENALTY);
            if (penalty > 0) {
                /* Fase 5.1: débito validado no backend — só aplica se confirmado.
                 * Captura a célula antes do async (selectedCells é limpo no fim). */
                const slashCell = selectedCells[0]?.cell;
                const txId = `spend-slash-${activeRealmId}-${roundNumber}-${Date.now()}`;
                void spendBalance(penalty, txId).then(confirmed => {
                    if (confirmed === null) return; /* backend recusou */
                    balanceSatoshis = confirmed;
                    document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
                    announceGameStatus(`SLASHING: ${penalty.toLocaleString()} sats debitados por ${consecutiveErrors} erros consecutivos.`);
                    showFloatingText(slashCell, -penalty, false, false);
                    updateStoreUI();
                });
            }
            /* Flash vermelho na tela */
            document.body.classList.add('slashing-flash');
            scheduleForSession(() => document.body.classList.remove('slashing-flash'), 600);
            consecutiveErrors = 0; /* Reseta contador após slashing para evitar penalidade cumulativa */
        }
    }
    selectedCells = [];
}

/**
 * Exibe uma etiqueta temporária com a recompensa obtida.
 */
function showFloatingText(cell, points, isHighFee, isGolden) {
    const floatText = document.createElement('div'); floatText.className = 'floating-text';
    const absPoints = Math.abs(Math.floor(points));
    floatText.innerText = `${points < 0 ? '-' : '+'}${absPoints} Sats`;
    if (points < 0) {
        /* Fase 1: slashing mostra em vermelho */
        floatText.innerText += " (SLASHING)";
        floatText.style.color = 'var(--error-red)';
    } else if (isGolden) {
        floatText.innerText += " (GOLDEN)"; floatText.style.color = 'var(--golden-hash)';
    } else if (isLightningMode) {
        floatText.innerText += " (L2 BOLT)"; floatText.style.color = 'var(--lightning-blue)';
    } else if (isHighFee) {
        floatText.innerText += " (HIGH FEE)"; floatText.style.color = 'var(--high-fee)';
    } else {
        floatText.style.color = 'var(--success-green)';
    }

    const rect = cell.getBoundingClientRect(); floatText.style.left = `${rect.left}px`; floatText.style.top = `${rect.top}px`;
    document.body.appendChild(floatText);
    scheduleForSession(() => floatText.remove(), 1200);
}

/**
 * Desenha no SVG a linha que marca uma palavra encontrada.
 */
function drawAnimatedLine(startCell, endCell) {
    const sRect = startCell.getBoundingClientRect(); const eRect = endCell.getBoundingClientRect(); const wrapRect = svgEl.getBoundingClientRect();
    const x1 = (sRect.left - wrapRect.left) + sRect.width/2; const y1 = (sRect.top - wrapRect.top) + sRect.height/2;
    const x2 = (eRect.left - wrapRect.left) + eRect.width/2; const y2 = (eRect.top - wrapRect.top) + eRect.height/2;

    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', x1); line.setAttribute('y1', y1); line.setAttribute('x2', x2); line.setAttribute('y2', y2);
    line.setAttribute('class', 'cross-line');
    if (isLightningMode) line.style.stroke = 'var(--lightning-blue)';

    const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    line.style.strokeDasharray = length; line.style.strokeDashoffset = length;
    svgEl.appendChild(line); requestAnimationFrame(() => { line.style.strokeDashoffset = 0; });
}

/**
 * Fase 7 (pontas soltas): exibe o limite efetivo da rodada no HUD.
 * Antes o HUD só mostrava "GLOBAL_NETWORK_LIMIT" genérico e o jogador não
 * via por que o tempo "acelerava" (Lightning=20s, RBF=15s, Halving -30s).
 */
function updateRaceLimitLabel() {
    const label = document.getElementById('race-limit-label');
    if (!label) return;
    const prefix = isLightningMode ? 'L2 ' : '';
    label.textContent = `LIMIT ${prefix}${networkTimeLimit}s`;
}

/**
 * Inicia o cronômetro visual da corrida contra a rede.
 *
 * Fase 7 (pontas soltas): timer por timestamp (endTime absoluto) em vez de
 * contador por tick. O setInterval é throttled em aba em segundo plano
 * (Chrome: 1 tick/s, depois 1 tick/min), então o contador "acelerava"/
 * atrasava na prática. Com Date.now() o progresso é sempre fiel ao tempo
 * real — a rodada expira no tempo certo mesmo com a aba em segundo plano.
 */
function startNetworkRace() {
    clearInterval(networkInterval);
    const now = Date.now();
    raceEndTime = now + networkTimeLimit * 1000;
    lastTickTime = now;
    updateRaceLimitLabel();
    netProgressEl.setAttribute('aria-valuetext', `${networkTimeLimit} segundos restantes`);
    const generation = sessionGeneration;
    networkInterval = setInterval(() => {
        if (generation !== sessionGeneration || !sessionReady) {
            clearInterval(networkInterval);
            return;
        }
        const tickNow = Date.now();
        const deltaMs = tickNow - lastTickTime;
        lastTickTime = tickNow;

        /* Power-up Time Freeze: pausa o cronômetro — adia o endTime pelo
         * delta real do tick para o tempo restante não diminuir durante o
         * freeze, e decrementa o freeze pelo tempo real. */
        if (powerupEffects.time_freeze > 0) {
            raceEndTime += deltaMs;
            powerupEffects.time_freeze = Math.max(0, powerupEffects.time_freeze - deltaMs / 1000);
            const freezeLeft = Math.ceil(powerupEffects.time_freeze);
            netProgressEl.classList.add('time-frozen');
            netProgressEl.setAttribute('aria-valuetext', `Time Freeze ativo: ${freezeLeft}s restantes`);
            return;
        }
        netProgressEl.classList.remove('time-frozen');

        const remainingMs = raceEndTime - Date.now();
        const remaining = Math.max(0, Math.ceil(remainingMs / 1000));
        networkTimePassed = Math.max(0, networkTimeLimit - remaining);
        const percent = (networkTimePassed / networkTimeLimit) * 100;
        netProgressEl.style.width = `${Math.min(100, percent)}%`;
        netProgressEl.setAttribute('aria-valuenow', String(Math.min(100, Math.round(percent))));
        netProgressEl.setAttribute('aria-valuetext', `${remaining} segundos restantes`);

        if (remainingMs <= 0) {
            clearInterval(networkInterval);
            /* Fase 6 (pontas soltas): se a rodada já foi finalizada (todas as
             * palavras achadas), não sobrescreve o sucesso com "expirou". */
            if (roundSettled) return;
            isPlaying = false; playSound('orphan'); submitScore();
            showResult(false, "O cronômetro da rodada expirou.");
        }
    }, 250);
}

/**
 * Apresenta o resultado final da rodada e prepara a próxima ação.
 */
function showResult(success, message) {
    const modal = document.getElementById('result-modal'); const title = document.getElementById('result-title');
    const text = document.getElementById('result-text'); const btn = document.getElementById('next-btn');

    updateStoreUI();
    announceGameStatus(message);
    setModalState(modal, true);
    saveSessionState(); /* Fase 1: salva estado ao mostrar resultado */
    if (success) {
        title.innerText = "Desafio concluído!"; title.style.color = isLightningMode ? "var(--lightning-blue)" : "var(--success-green)";
        text.innerText = message; btn.innerText = "Próxima rodada";
        maxRoundEarningsTotal = Math.max(maxRoundEarningsTotal, currentRoundEarnings);
        void pushStats({ max_round_earnings: maxRoundEarningsTotal });
        roundNumber++;
        /* Fase 7: Tracking — bloco completado */
        trackBlockCompleted();
        /* Crates grátis: 1 a cada 10 blocos minerados */
        void claimFreeCrates();
    } else {
        title.innerText = "Rodada encerrada"; title.style.color = "var(--error-red)";
        text.innerText = message; btn.innerText = "Tentar nova rodada";
        comboMultiplier = 1.0; document.getElementById('ui-combo').innerText = `1.0×`;
    }
    setNextButtonAction(prepareNextBlock);
}

/* Fase 2: Orphan Block Salvage (RBF) — oferece resgate com 100K sats */
const RBF_PRICE = 100000;
let rbfTimeout = null;
/* Fase 6.1: tempo original da rodada (salvo ao mostrar o RBF) — o resgate
 * reinicia a rodada com o tempo que o jogador tinha, não com 15s fixos. */
let rbfOriginalTimeLimit = 0;

function showOrphanBlockSalvage() {
    const modal = document.getElementById('result-modal');
    const title = document.getElementById('result-title');
    const text = document.getElementById('result-text');
    const btn = document.getElementById('next-btn');

    /* Fase 6.1: salva o tempo original da rodada para o resgate */
    rbfOriginalTimeLimit = networkTimeLimit;

    setModalState(modal, true);
    title.innerText = "Bloco minerado!";
    title.style.color = "var(--warning-orange)";
    text.innerText = `Um novo bloco real encerrou esta rodada. Gastar ${RBF_PRICE.toLocaleString()} sats para RBF (recomeça com ${rbfOriginalTimeLimit}s)?`;
    btn.innerText = `Resgatar (${RBF_PRICE.toLocaleString()} sats)`;
    btn.style.display = 'inline-flex';
    saveSessionState(); /* Fase 1: salva estado ao mostrar RBF */

    const generation = sessionGeneration;
    rbfTimeout = scheduleForSession(() => {
        rbfTimeout = null;
        showResult(false, "O tempo de RBF expirou.");
    }, 3000, generation);

    const rbfHandler = async () => {
        if (rbfTimeout) {
            cancelSessionTimeout(rbfTimeout);
            rbfTimeout = null;
        }
        if (balanceSatoshis < RBF_PRICE) {
            announceGameStatus("Saldo insuficiente para RBF.");
            scheduleForSession(() => showResult(false, "Saldo insuficiente para RBF."), 500, generation);
            return;
        }
        /* Fase 5.1: débito validado no backend — só resgata se confirmado */
        const txId = `spend-rbf-${activeRealmId}-${roundNumber}-${Date.now()}`;
        const confirmed = await spendBalance(RBF_PRICE, txId);
        if (confirmed === null) {
            announceGameStatus("Falha ao confirmar o RBF. Tente novamente.");
            return;
        }
        balanceSatoshis = confirmed;
        rbfUsedTotal++;
        void pushStats({ rbf_used: rbfUsedTotal });
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        announceGameStatus(`RBF ativado: rodada reinicia com ${rbfOriginalTimeLimit}s.`);
        playSound('buy');
        updateStoreUI();

        /* Fase 6.1: reinicia a rodada com o tempo original (hardware + nível) */
        isPlaying = true;
        networkTimePassed = 0;
        networkTimeLimit = rbfOriginalTimeLimit;
        netProgressEl.style.width = '0%';
        netProgressEl.setAttribute('aria-valuenow', '0');
        netProgressEl.setAttribute('aria-valuetext', `${rbfOriginalTimeLimit} segundos restantes`);
        setModalState(modal, false);
        startNetworkRace();
    };
    setNextButtonAction(rbfHandler);
}

/* Fase 7: Achievements — sistema de conquistas */
let achievementsData = null;
let achievementsFilter = 'all';
let achievementBonuses = { reward_percent: 0, hint_discount: 0 };
/* Bônus de recompensa temporário do Season Pass (ex.: +5%/+10%) */
let seasonRewardBonus = 0;
let realmsPlayed = new Set();
let epochsSurvived = 0;
let scoresSubmitted = 0;
let bestRank = 999;
let poolRank1 = 0;
let wordsFoundTotal = 0;
let goldenFoundTotal = 0;
let highFeeFoundTotal = 0;
let mevFoundTotal = 0;
let combos2xTotal = 0;
let combos4xTotal = 0;
let fastFindsTotal = 0;
let ultraFastFindsTotal = 0;
let blocksCompletedTotal = 0;
let maxScoreTotal = 0;
let rbfUsedTotal = 0;
let maxRoundEarningsTotal = 0;
let poolJoinedTotal = 0;
let lastWordFoundTime = 0;
let achievementToastTimeout = null;

function achievementsUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/achievements/${encodeURIComponent(username)}`, API_BASE_URL).toString();
}

function statsUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/stats/${encodeURIComponent(username)}`, API_BASE_URL).toString();
}

/* Fase 7: Carregar achievements do backend */
async function fetchAchievements(realmId = activeRealmId, username = minerName) {
    if (!realmId || !username) return;
    try {
        const response = await fetch(achievementsUrl(realmId, username));
        if (!response.ok) return;
        const data = await response.json();
        achievementsData = data;
        achievementBonuses = data.bonuses || { reward_percent: 0, hint_discount: 0 };
        const stats = data.stats || {};
        wordsFoundTotal = stats.words_found ?? wordsFoundTotal;
        goldenFoundTotal = stats.golden_found ?? goldenFoundTotal;
        highFeeFoundTotal = stats.high_fee_found ?? highFeeFoundTotal;
        mevFoundTotal = stats.mev_found ?? mevFoundTotal;
        combos2xTotal = stats.combos_2x ?? combos2xTotal;
        combos4xTotal = stats.combos_4x ?? combos4xTotal;
        fastFindsTotal = stats.fast_finds ?? fastFindsTotal;
        ultraFastFindsTotal = stats.ultra_fast_finds ?? ultraFastFindsTotal;
        blocksCompletedTotal = stats.blocks_completed ?? blocksCompletedTotal;
        maxScoreTotal = stats.max_score ?? maxScoreTotal;
        rbfUsedTotal = stats.rbf_used ?? rbfUsedTotal;
        maxRoundEarningsTotal = stats.max_round_earnings ?? maxRoundEarningsTotal;
        renderAchievementsModal();
    } catch (error) {
        console.warn('Erro ao carregar achievements.', error);
    }
}

/* Fase 7: Enviar stats para o backend */
async function pushStats(statsObj) {
    if (!activeRealmId || !minerName) return;
    try {
        const response = await fetch(statsUrl(activeRealmId, minerName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, ...statsObj })
        });
        if (!response.ok) return;
        const data = await response.json();
        if (data.newly_unlocked && data.newly_unlocked.length > 0) {
            for (const achId of data.newly_unlocked) {
                const ach = achievementsData?.achievements?.find(a => a.id === achId);
                if (ach) {
                    showAchievementToast(ach);
                }
            }
        }
        if (data.bonuses) {
            achievementBonuses = data.bonuses;
        }
        if (data.stats) {
            rbfUsedTotal = data.stats.rbf_used ?? rbfUsedTotal;
            maxRoundEarningsTotal = data.stats.max_round_earnings ?? maxRoundEarningsTotal;
        }
        if (achievementsData) {
            renderAchievementsModal();
        }
    } catch (error) {
        console.warn('Erro ao enviar stats.', error);
    }
}

/* Fase 7: Renderizar modal de achievements */
function renderAchievementsModal() {
    if (!achievementsData) return;

    const grid = document.getElementById('achievements-grid');
    const summary = document.getElementById('achievements-summary');
    const filters = document.getElementById('achievements-filters');
    if (!grid || !summary || !filters) return;

    const allAchievements = achievementsData.achievements || [];
    const unlockedCount = allAchievements.filter(a => a.unlocked).length;
    const totalCount = allAchievements.length;
    const rewardBonus = (achievementBonuses.reward_percent * 100).toFixed(1);
    const hintDiscount = (achievementBonuses.hint_discount * 100).toFixed(1);

    summary.innerHTML = `
        <span class="summary-count">${unlockedCount}/${totalCount} desbloqueadas</span>
        <span class="summary-bonus">+${rewardBonus}% recompensa · -${hintDiscount}% dicas</span>
    `;

    /* Filtros por categoria */
    filters.innerHTML = '';
    ACHIEVEMENT_CATEGORIES.forEach(cat => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `achievements-filter-btn${achievementsFilter === cat.key ? ' active' : ''}`;
        btn.innerHTML = `${cat.iconName ? iconSvg(cat.iconName) : ''}<span>${cat.label}</span>`;
        btn.addEventListener('click', () => {
            achievementsFilter = cat.key;
            renderAchievementsModal();
        });
        filters.appendChild(btn);
    });

    /* Grid de achievements */
    const filtered = achievementsFilter === 'all'
        ? allAchievements
        : allAchievements.filter(a => a.category === achievementsFilter);

    grid.innerHTML = '';
    filtered.forEach(ach => {
        const card = document.createElement('div');
        card.className = `achievement-card ${ach.unlocked ? 'unlocked' : 'locked'}`;
        card.setAttribute('role', 'listitem');
        card.setAttribute('tabindex', '0');

        const progressPercent = Math.min(ach.progress * 100, 100);
        const currentLabel = ach.stat_name === 'best_rank'
            ? `${ach.current || '—'}/${ach.target}`
            : `${ach.current || 0}/${ach.target}`;

        const bonusLabel = ach.bonus ? (
            ach.bonus.type === 'reward_percent'
                ? `+${(ach.bonus.value * 100).toFixed(1)}% recompensa`
                : `-${(ach.bonus.value * 100).toFixed(1)}% dicas`
        ) : '';

        card.innerHTML = `
            <span class="achievement-icon">${iconSvg(achievementIconName(ach.category))}</span>
            <span class="achievement-name">${escapeHtml(ach.name)}</span>
            <div class="achievement-progress-bar">
                <div class="achievement-progress-fill"></div>
            </div>
            <span class="achievement-progress-text">${currentLabel}</span>
            <div class="achievement-tooltip">
                <div class="achievement-tooltip-desc">${escapeHtml(ach.description)}</div>
                ${bonusLabel ? `<div class="achievement-tooltip-bonus">Bônus: ${escapeHtml(bonusLabel)}</div>` : ''}
            </div>
        `;
        card.querySelector('.achievement-progress-fill').style.width = `${progressPercent}%`;

        grid.appendChild(card);
    });
}

/* Fase 7: Toast de notificacao de achievement desbloqueado */
function showAchievementToast(ach) {
    const toast = document.getElementById('achievement-toast');
    const icon = document.getElementById('achievement-toast-icon');
    const title = document.getElementById('achievement-toast-title');
    const desc = document.getElementById('achievement-toast-desc');
    if (!toast || !icon || !title || !desc) return;

    setSvgIcon(icon, achievementIconName(ach.category));
    title.textContent = ach.name;
    desc.textContent = ach.description;

    toast.hidden = false;
    requestAnimationFrame(() => {
        toast.classList.add('visible');
    });

    if (achievementToastTimeout) {
        clearTimeout(achievementToastTimeout);
    }
    achievementToastTimeout = scheduleForSession(() => {
        toast.classList.remove('visible');
        scheduleForSession(() => { toast.hidden = true; }, 400);
    }, 4000);

    playSound('success');
}

/* Fase 7: Abrir/fechar modal de achievements */
function openAchievementsModal() {
    if (!activeRealmId || !minerName) return;
    void fetchAchievements(activeRealmId, minerName).then(() => {
        setModalState(document.getElementById('achievements-modal'), true);
    });
}

function closeAchievementsModal() {
    setModalState(document.getElementById('achievements-modal'), false);
}

/* Fase 7: Integracao com eventos do jogo — incrementar stats */
function trackWordFound(isGolden, isHighFee, isMev) {
    wordsFoundTotal++;
    if (isGolden) goldenFoundTotal++;
    if (isHighFee) highFeeFoundTotal++;
    if (isMev) mevFoundTotal++;

    /* Fase 5.4: streak de palavras sem erro — incrementa a cada acerto */
    wordsWithoutErrorStreak++;

    /* Verificar velocidade (fast finds) */
    const now = Date.now();
    if (lastWordFoundTime > 0) {
        const elapsed = (now - lastWordFoundTime) / 1000;
        if (elapsed < 2) ultraFastFindsTotal++;
        else if (elapsed < 3) fastFindsTotal++;
    }
    lastWordFoundTime = now;

    pushStats({
        words_found: wordsFoundTotal,
        golden_found: goldenFoundTotal,
        high_fee_found: highFeeFoundTotal,
        mev_found: mevFoundTotal,
        fast_finds: fastFindsTotal,
        ultra_fast_finds: ultraFastFindsTotal,
        words_without_error: wordsWithoutErrorStreak
    });
}

function trackCombo(comboMult) {
    if (comboMult >= 4) {
        combos4xTotal++;
        pushStats({ combos_4x: combos4xTotal });
    }
    if (comboMult >= 2) {
        combos2xTotal++;
        pushStats({ combos_2x: combos2xTotal });
    }
}

function trackBlockCompleted() {
    blocksCompletedTotal++;
    pushStats({ blocks_completed: blocksCompletedTotal });
}

function trackRealmPlayed(realmId) {
    if (realmId) {
        realmsPlayed.add(realmId);
        pushStats({ realms_played: realmsPlayed.size });
    }
}

function trackScoreSubmitted(score) {
    scoresSubmitted++;
    if (score > maxScoreTotal) maxScoreTotal = score;
    pushStats({ scores_submitted: scoresSubmitted, max_score: maxScoreTotal });
}

function trackPoolJoined() {
    poolJoinedTotal = 1;
    pushStats({ pool_joined: poolJoinedTotal });
}

function trackBestRank(rank) {
    if (rank < bestRank) bestRank = rank;
    pushStats({ best_rank: bestRank });
}

function trackEpochSurvived() {
    epochsSurvived++;
    pushStats({ epochs_survived: epochsSurvived });
}


/* Fase 7: Aplicar bônus de achievements ao preco de dica */
function getHintPrice() {
    const discount = achievementBonuses.hint_discount || 0;
    return Math.floor(hintCost * (1 - discount));
}

/* Fase 7: Aplicar bônus de achievements a recompensa */
function applyAchievementBonus(points) {
    const bonus = (achievementBonuses.reward_percent || 0) + seasonRewardBonus + getCollectionBonus();
    return Math.floor(points * (1 + bonus));
}

/* Fase 4.6: Bônus de coleção de cards (recompensa % por coleção completa).
 * Soma o value de cada raridade cuja coleção está completa (owned >= required).
 * O backend já calcula collection_bonus em _get_player_cards; aqui só somamos.
 * Retorna 0 se a coleção ainda não foi carregada (cardsData nulo). */
function getCollectionBonus() {
    if (!cardsData || !cardsData.collection_bonus) return 0;
    let total = 0;
    for (const rarity of Object.keys(cardsData.collection_bonus)) {
        const entry = cardsData.collection_bonus[rarity];
        if (entry && entry.complete && entry.bonus && entry.bonus.type === 'reward_percent') {
            total += entry.bonus.value || 0;
        }
    }
    return total;
}

/* Fase 7: Event listeners para achievements */
document.addEventListener('DOMContentLoaded', () => {
    const btnAchievements = document.getElementById('btn-achievements');
    const btnCloseAchievements = document.getElementById('btn-close-achievements');
    if (btnAchievements) {
        btnAchievements.addEventListener('click', openAchievementsModal);
    }
    if (btnCloseAchievements) {
        btnCloseAchievements.addEventListener('click', closeAchievementsModal);
    }
    /* Fase C1: atalho de missões — o jogador procurava missões no PERFIL;
     * elas ficam em COMPETIR. Navega direto para a seção de missões. */
    const btnMissionsShortcut = document.getElementById('btn-missions-shortcut');
    if (btnMissionsShortcut) {
        btnMissionsShortcut.addEventListener('click', () => {
            showTab('competir');
            activateMechanicSection('competir', 'missions', true);
        });
    }
});

/* Fase 7: Carregar stats iniciais ao iniciar sessao */
async function loadAchievementStats(realmId, username) {
    if (!realmId || !username) return;
    try {
        const response = await fetch(achievementsUrl(realmId, username));
        if (!response.ok) return;
        const data = await response.json();
        achievementBonuses = data.bonuses || { reward_percent: 0, hint_discount: 0 };
        const stats = data.stats || {};
        wordsFoundTotal = stats.words_found || 0;
        goldenFoundTotal = stats.golden_found || 0;
        highFeeFoundTotal = stats.high_fee_found || 0;
        mevFoundTotal = stats.mev_found || 0;
        combos2xTotal = stats.combos_2x || 0;
        combos4xTotal = stats.combos_4x || 0;
        fastFindsTotal = stats.fast_finds || 0;
        ultraFastFindsTotal = stats.ultra_fast_finds || 0;
        blocksCompletedTotal = stats.blocks_completed || 0;
        maxScoreTotal = stats.max_score || 0;
        poolJoinedTotal = stats.pool_joined || 0;
        bestRank = stats.best_rank || 999;
        epochsSurvived = stats.epochs_survived || 0;
        poolRank1 = stats.pool_rank_1 || 0;
    } catch (error) {
        console.warn('Erro ao carregar stats de achievements.', error);
    }
}

/* ==========================================================================
   Boss Battles — funções de controle do Boss Block
   ========================================================================== */

/**
 * Fase Boss: recebe evento boss_block do WebSocket e prepara a rodada especial.
 * Substitui os parâmetros normais por configurações do boss.
 */
function handleBossBlock(data, generation) {
    if (generation !== sessionGeneration) return;
    if (document.getElementById('result-modal')?.classList.contains('active')) {
        console.warn('Boss block recebido com resultado pendente — ignorado.');
        return;
    }
    if (isPlaying) {
        /* Fase 6.3 (decisão de design): o boss block é ignorado se o jogador
         * está no meio de uma rodada. Interromper a rodada atual para
         * enfileirar o boss exigiria salvar/restaurar o estado da rodada em
         * curso (risco alto de regressão). Como o boss block recorre a cada
         * 50 blocos (~10 min), perder um por estar em rodada é aceitável —
         * o próximo boss block será a oportunidade. */
        console.warn('Boss block recebido mas rodada já em andamento — ignorado (design: o próximo boss block será a oportunidade).');
        return;
    }
    if (isTransitioning) {
        console.warn('Boss block recebido mas transição em andamento — ignorado.');
        return;
    }

    // Configura parâmetros do boss
    isBossActive = true;
    bossMaxHp = data.boss_hp || 10;
    bossHp = bossMaxHp;
    bossRewardMultiplier = data.boss_reward_multiplier || 5;
    bossLoot = data.boss_loot || 50000;
    bossWordsRequired = data.boss_words || 10;
    bossTimer = data.boss_timer || 45;
    bossGridSize = data.boss_grid_size || 15; /* Fase 4.2: backend é a fonte de verdade */
    bossDefeatHandled = false;

    // Efeitos visuais dramáticos
    document.body.classList.add('boss-flash', 'boss-active');
    scheduleForSession(() => document.body.classList.remove('boss-flash'), 1500);
    document.body.classList.add('boss-shake');
    scheduleForSession(() => document.body.classList.remove('boss-shake'), 500);

    // Mostra HUD do boss
    const bossHud = document.getElementById('boss-hud');
    if (bossHud) {
        bossHud.classList.remove('hidden');
        updateBossHpUI();
    }

    announceGameStatus(`BOSS BLOCK! ${bossMaxHp} HP — ${bossWordsRequired} palavras — ${bossTimer}s — ${bossRewardMultiplier}× recompensa!`);

    // Limpa buffer e prepara para coletar palavras do boss
    txBuffer = [];
    wordsFoundInBlock = 0;

    // Atualiza o loading text para refletir o boss
    const loadingText = document.getElementById('tx-loading-bank');
    if (loadingText) {
        loadingText.innerText = `Aguardando transações do boss (0/${bossWordsRequired})...`;
    }

    // Anula a verificação normal de WORDS_PER_BLOCK — o boss precisa de bossWordsRequired
    // Isso é controlado no handler de transaction_received abaixo
}

/**
 * Atualiza a barra de HP do boss na UI.
 */
function updateBossHpUI() {
    const bossHpBar = document.getElementById('boss-hp-bar');
    const bossHpText = document.getElementById('boss-hp-text');
    const hpContainer = document.querySelector('.boss-hp-bar-container');
    if (!bossHpBar || !bossHpText) return;

    const percent = (bossHp / bossMaxHp) * 100;
    bossHpBar.style.width = `${percent}%`;
    bossHpText.textContent = `${bossHp} / ${bossMaxHp}`;

    if (hpContainer) {
        hpContainer.setAttribute('aria-valuenow', String(bossHp));
        hpContainer.setAttribute('aria-valuetext', `${bossHp} de ${bossMaxHp} HP`);
    }

    // Muda cor conforme HP restante
    if (percent <= 20) {
        bossHpBar.style.background = 'linear-gradient(90deg, #ff0000, #ff4444)';
    } else if (percent <= 50) {
        bossHpBar.style.background = 'linear-gradient(90deg, #ff6b00, #ff8844)';
    }
}

/**
 * Fase Boss: processa uma transação recebida durante o boss block.
 * Retorna true se a palavra foi adicionada ao buffer do boss.
 */
function handleBossTransaction(data) {
    if (!isBossActive) return false;
    if (!isValidTransactionEvent(data)) return false;
    if (txBuffer.length >= bossWordsRequired) return false;

    // Evita duplicatas
    if (txBuffer.find(t => t.word === data.word)) return false;

    txBuffer.push({
        word: data.word,
        isHighFee: data.is_high_fee,
        isGolden: data.is_golden,
        vsize: data.vsize,
        isMev: data.is_mev,
        multiplier: data.multiplier,
        isBoss: true, // flag especial para palavras do boss
    });

    /* Fase A3 (ponta solta da auditoria): atualiza o watchdog também no boss
     * block — antes, handleBossTransaction não tocava lastTxActivityTime,
     * então um buffer do boss parcial parado >45s podia disparar reconexão
     * no meio da luta (timer do boss é 45s — janela estreita). */
    lastTxActivityTime = Date.now();

    const loadingText = document.getElementById('tx-loading-bank');
    if (loadingText) {
        loadingText.innerText = `Aguardando transações do boss (${txBuffer.length}/${bossWordsRequired})...`;
    }

    // Quando todas as palavras do boss foram coletadas, constrói a grade
    if (txBuffer.length === bossWordsRequired && !isTransitioning) {
        cancelSessionTimeout(pendingBuildTimeout);
        pendingBuildTimeout = scheduleForSession(() => {
            pendingBuildTimeout = undefined;
            void requestBossPlayableBlockBuild();
        }, 500, sessionGeneration);
    }

    return true;
}

/**
 * Fase 4.1: gate de energia do boss block.
 *
 * O boss consome 1 energia como qualquer rodada (decisão do usuário:
 * consistência). Antes da correção, buildBossPlayableBlock era chamado
 * diretamente e a rodada do boss era gratuita. Este gate espelha
 * requestPlayableBlockBuild: reserva o spend, chama spendEnergy e trata os
 * três resultados (sem energia / erro / falha no build) com refund quando
 * aplicável. Se o jogador não tem energia, o boss é descartado (resetBossState)
 * e o jogo volta ao fluxo normal.
 */
async function requestBossPlayableBlockBuild() {
    if (
        energyGatePending
        || isTransitioning
        || isPlaying
        || !sessionReady
        || !ws
        || ws.readyState !== WebSocket.OPEN
        || !isBossActive
        || txBuffer.length !== bossWordsRequired
    ) return;

    const generation = sessionGeneration;
    const roundRealm = activeRealmId;
    const roundMiner = minerName;
    const roundId = reservePendingEnergySpend(roundRealm, roundMiner);
    energyGatePending = true;
    try {
        const hasEnergy = await spendEnergy(roundId, roundRealm, roundMiner);
        if (
            generation !== sessionGeneration
            || !sessionReady
            || !isBossActive
            || txBuffer.length !== bossWordsRequired
        ) {
            if (hasEnergy) {
                await queueEnergyRefund(roundId, roundRealm, roundMiner);
                clearPendingEnergySpend(roundId);
            } else if (hasEnergy === false) {
                clearPendingEnergySpend(roundId);
            }
            pendingEnergyRoundId = null;
            return;
        }
        if (hasEnergy === null) {
            // Erro de rede: não confirma energia — descarta o boss e volta ao normal.
            clearPendingEnergySpend(roundId);
            pendingEnergyRoundId = null;
            resetBossState();
            txBuffer = []; /* Fase 4.1: as palavras do boss não valem para a rodada normal */
            isPlaying = false;
            overlayEl.classList.remove('hidden');
            announceGameStatus('Não foi possível confirmar a energia. Boss descartado.');
            return;
        }
        if (hasEnergy === false) {
            // Sem energia: o boss é descartado (decisão Fase 4.1).
            clearPendingEnergySpend(roundId);
            pendingEnergyRoundId = null;
            resetBossState();
            txBuffer = []; /* Fase 4.1: as palavras do boss não valem para a rodada normal */
            showPendingEnergyState(true);
            return;
        }
        const blockStarted = buildBossPlayableBlock();
        if (!blockStarted) {
            await queueEnergyRefund(roundId, roundRealm, roundMiner);
            clearPendingEnergySpend(roundId);
            pendingEnergyRoundId = null;
            resetBossState();
            txBuffer = []; /* Fase 4.1: as palavras do boss não valem para a rodada normal */
            showPendingEnergyState(true);
            return;
        }
        clearPendingEnergySpend(roundId);
    } finally {
        if (generation === sessionGeneration) {
            energyGatePending = false;
        }
    }
}

/**
 * Fase Boss: constrói a grade especial do boss (15×15, 10 palavras, timer 45s).
 * Sobrescreve buildPlayableBlock apenas para o contexto do boss.
 */
function buildBossPlayableBlock() {
    if (
        isTransitioning
        || !sessionReady
        || !ws
        || ws.readyState !== WebSocket.OPEN
        || txBuffer.length !== bossWordsRequired
    ) return false;

    overlayEl.classList.add('hidden');
    gridEl.innerHTML = '';
    svgEl.innerHTML = '';
    bankEl.innerHTML = '';
    grid = [];
    blockWords = [];
    isPlaying = true;

    // Boss: grade definida pelo backend (data.boss_grid_size), fallback 15
    currentGridSize = bossGridSize;
    networkTimeLimit = bossTimer + skillTimeBonus;

    configureGridSize(currentGridSize);

    document.getElementById('ui-block').innerText = `#${roundNumber.toLocaleString()} BOSS`;

    for (let y = 0; y < currentGridSize; y++) {
        let row = [];
        for (let x = 0; x < currentGridSize; x++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.dataset.x = x;
            cell.dataset.y = y;
            cell.tabIndex = x === 0 && y === 0 ? 0 : -1;
            cell.setAttribute('role', 'gridcell');
            cell.setAttribute('aria-selected', 'false');
            gridEl.appendChild(cell);
            row.push({ element: cell, char: '', isFound: false });
        }
        grid.push(row);
    }

    const allWordsPlaced = txBuffer.every(
        tx => injectWordInGrid(tx.word, tx.isHighFee, tx.isGolden, tx.isMev, tx.multiplier)
    );
    if (!allWordsPlaced) {
        // Tenta reconstruir a grade do boss
        gridEl.innerHTML = '';
        svgEl.innerHTML = '';
        bankEl.replaceChildren(); // limpa itens do word bank da 1ª tentativa (evita duplicados)
        grid = [];
        blockWords = [];
        for (let y = 0; y < currentGridSize; y++) {
            let row = [];
            for (let x = 0; x < currentGridSize; x++) {
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.dataset.x = x;
                cell.dataset.y = y;
                cell.tabIndex = x === 0 && y === 0 ? 0 : -1;
                cell.setAttribute('role', 'gridcell');
                cell.setAttribute('aria-selected', 'false');
                gridEl.appendChild(cell);
                row.push({ element: cell, char: '', isFound: false });
            }
            grid.push(row);
        }
        const retryPlaced = txBuffer.every(
            tx => injectWordInGrid(tx.word, tx.isHighFee, tx.isGolden, tx.isMev, tx.multiplier)
        );
        if (!retryPlaced) {
            isPlaying = false;
            overlayEl.classList.remove('hidden');
            const loaderText = overlayEl.querySelector('#tx-loading');
            if (loaderText) loaderText.innerText = "Falha ao montar a grade do boss. Aguarde o próximo conjunto.";
            return false;
        }
    }

    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            if (grid[y][x].char === '') {
                grid[y][x].char = String.fromCharCode(65 + Math.floor(Math.random() * 26));
            }
            grid[y][x].element.innerText = grid[y][x].char;
            grid[y][x].element.setAttribute(
                'aria-label',
                `Letra ${grid[y][x].char}, linha ${y + 1}, coluna ${x + 1}`
            );
        }
    }

    updateStoreUI();
    announceGameStatus(`BOSS BLOCK! Encontre todas as ${bossWordsRequired} palavras em ${bossTimer}s!`);
    startBossNetworkRace();
    return true;
}

/**
 * Fase Boss: inicia o cronômetro especial do boss (45s).
 * Usa cor vermelha na barra de progresso para indicar urgência.
 *
 * Fase 7 (pontas soltas): timer por timestamp (endTime absoluto) — mesmo
 * tratamento do startNetworkRace, imune a throttling de aba em 2º plano.
 */
function startBossNetworkRace() {
    clearInterval(networkInterval);
    const now = Date.now();
    raceEndTime = now + networkTimeLimit * 1000;
    lastTickTime = now;
    updateRaceLimitLabel();
    netProgressEl.setAttribute('aria-valuetext', `${networkTimeLimit} segundos restantes`);
    netProgressEl.style.background = 'var(--error-red)';
    netProgressEl.style.boxShadow = '0 0 10px rgba(239, 68, 68, 0.8)';

    const generation = sessionGeneration;
    networkInterval = setInterval(() => {
        if (generation !== sessionGeneration || !sessionReady) {
            clearInterval(networkInterval);
            return;
        }
        const remainingMs = raceEndTime - Date.now();
        const remaining = Math.max(0, Math.ceil(remainingMs / 1000));
        networkTimePassed = Math.max(0, networkTimeLimit - remaining);
        const percent = (networkTimePassed / networkTimeLimit) * 100;
        netProgressEl.style.width = `${Math.min(100, percent)}%`;
        netProgressEl.setAttribute('aria-valuenow', String(Math.min(100, Math.round(percent))));
        netProgressEl.setAttribute('aria-valuetext', `${remaining} segundos restantes`);

        // Timer crítico — menos de 10s
        if (remaining <= 10 && remaining > 0) {
            netProgressEl.style.background = 'var(--error-red)';
            netProgressEl.style.animation = 'rbfPulse 0.5s ease-in-out infinite';
        }

        if (remainingMs <= 0) {
            clearInterval(networkInterval);
            isPlaying = false;
            playSound('orphan');
            submitScore();
            // Boss expirou — mostra resultado normal
            showBossResult(false, "O cronômetro do boss expirou. O boss resistiu!");
        }
    }, 250);
}

/**
 * Fase Boss: mostra o resultado da rodada do boss.
 */
function showBossResult(success, message) {
    const modal = document.getElementById('result-modal');
    const title = document.getElementById('result-title');
    const text = document.getElementById('result-text');
    const btn = document.getElementById('next-btn');

    updateStoreUI();
    announceGameStatus(message);
    setModalState(modal, true);
    saveSessionState();

    if (success) {
        title.innerText = 'Boss Derrotado!';
        title.style.color = "var(--success-green)";
        text.innerText = message;
        btn.innerText = "Continuar";
        roundNumber++;
    } else {
        title.innerText = "Boss Resistiu";
        title.style.color = "var(--error-red)";
        text.innerText = message;
        btn.innerText = "Tentar novamente";
        comboMultiplier = 1.0;
        document.getElementById('ui-combo').innerText = '1.0×';
        /* Fase 3: reseta o estado do boss na derrota por timeout — evita rodadas de boss fantasma em cadeia */
        resetBossState();
    }
    setNextButtonAction(prepareNextBlock);
}

/**
 * Fase Boss: reseta todo o estado do boss após a rodada.
 */
function resetBossState() {
    isBossActive = false;
    bossHp = 10;
    bossMaxHp = 10;
    bossRewardMultiplier = 5;
    bossLoot = 50000;
    bossWordsRequired = 10;
    bossTimer = 45;
    bossGridSize = 15; /* Fase 4.2: reseta junto com os demais campos do boss */
    bossDefeatHandled = false;

    // Esconde HUD do boss
    const bossHud = document.getElementById('boss-hud');
    if (bossHud) bossHud.classList.add('hidden');

    // Remove classes de efeito do corpo
    document.body.classList.remove('boss-active');

    // Reseta barra de progresso para cor normal
    netProgressEl.style.background = '';
    netProgressEl.style.boxShadow = '';
    netProgressEl.style.animation = '';

    // Reseta loading text
    const loadingText = document.getElementById('tx-loading');
    if (loadingText) {
        loadingText.innerText = `Aguardando transações (0/${WORDS_PER_BLOCK})...`;
    }
}

/**
 * Fase Boss: mostra o modal de derrota do boss com loot especial.
 */
function showBossDefeatModal() {
    const modal = document.getElementById('boss-defeat-modal');
    const title = document.getElementById('boss-defeat-title');
    const text = document.getElementById('boss-defeat-text');
    const btn = document.getElementById('boss-defeat-btn');

    /* Fase 6.2: fecha o modal de resultado (se aberto) antes de mostrar o
     * modal de derrota do boss — evita sobreposição de dois modais. */
    const resultModal = document.getElementById('result-modal');
    if (resultModal && resultModal.classList.contains('active')) {
        setModalState(resultModal, false);
    }

    // Atualiza loot
    text.innerHTML = `
        Boss Block eliminado! Achievement <strong>"Boss Slayer"</strong> desbloqueado.<br>
        <span class="boss-loot-text">+${bossLoot.toLocaleString()} sats de loot especial!</span>
    `;

    setModalState(modal, true);

    // Handler do botão continuar
    btn.onclick = () => {
        setModalState(modal, false);
        btn.onclick = null;
        // Reseta estado do boss
        resetBossState();
        // Prepara próxima rodada normal
        prepareNextBlock();
    };
}

/* ==========================================================================
   Fase 8: Missões Diárias & Semanais — UI e lógica
   ========================================================================== */

let missionsData = null;
let missionsRefreshInterval;

// Elementos do painel de missões
const missionsPanelEl = document.getElementById('missions-panel');
const missionsLoadingEl = document.getElementById('missions-loading');
const missionsListEl = document.getElementById('missions-list');

/**
 * URL para o endpoint de missões.
 */
function missionsUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(
        `/api/v1/networks/${encodeURIComponent(realmId)}/missions/${encodeURIComponent(username)}`,
        API_BASE_URL
    ).toString();
}

/**
 * URL para reclamar recompensa de missão.
 */
function claimMissionUrl(realmId, username, missionId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(
        `/api/v1/networks/${encodeURIComponent(realmId)}/missions/${encodeURIComponent(username)}/claim/${encodeURIComponent(missionId)}`,
        API_BASE_URL
    ).toString();
}

/**
 * URL para atualizar progresso das missões.
 */
function updateMissionsUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(
        `/api/v1/networks/${encodeURIComponent(realmId)}/missions/${encodeURIComponent(username)}/update`,
        API_BASE_URL
    ).toString();
}

/**
 * Carrega as missões do backend e renderiza o painel.
 */
async function loadMissions(realmId = activeRealmId, username = minerName) {
    if (!realmId || !username) return;
    if (!missionsListEl) return;

    missionsLoadingEl?.remove();

    try {
        const response = await fetch(missionsUrl(realmId, username));
        if (!response.ok) {
            console.warn('Falha ao carregar missões:', response.status);
            return;
        }
        missionsData = await response.json();
        renderMissions(missionsData);
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Erro ao buscar missões:', error);
        }
    }
}

/**
 * Renderiza o painel de missões com base nos dados do backend.
 */
function renderMissions(data) {
    if (!missionsListEl) return;
    missionsListEl.innerHTML = '';

    // Missões diárias
    if (data.daily_missions && data.daily_missions.length > 0) {
        data.daily_missions.forEach(mission => {
            missionsListEl.appendChild(createMissionCard(mission, 'daily'));
        });
    }

    // Seção semanal
    if (data.weekly_mission) {
        const weeklySection = document.createElement('div');
        weeklySection.className = 'missions-weekly-section';

        const weeklyLabel = document.createElement('div');
        weeklyLabel.className = 'missions-weekly-label';
        weeklyLabel.textContent = 'Missão Semanal';
        weeklySection.appendChild(weeklyLabel);

        weeklySection.appendChild(createMissionCard(data.weekly_mission, 'weekly'));
        missionsListEl.appendChild(weeklySection);
    }
}

/**
 * Cria o elemento DOM de um card de missão.
 */
function createMissionCard(mission, type) {
    const card = document.createElement('div');
    card.className = 'mission-card';
    if (type === 'weekly') card.classList.add('weekly');
    if (mission.completed && !mission.claimed) card.classList.add('completed');
    if (mission.claimed) card.classList.add('claimed');

    // Cabeçalho: título + recompensa
    const header = document.createElement('div');
    header.className = 'mission-header';

    const title = document.createElement('div');
    title.className = 'mission-title';
    title.textContent = mission.title;
    header.appendChild(title);

    const reward = document.createElement('div');
    reward.className = 'mission-reward';
    reward.textContent = `+${mission.reward.toLocaleString()} sats`;
    header.appendChild(reward);

    card.appendChild(header);

    // Descrição
    const description = document.createElement('div');
    description.className = 'mission-description';
    description.textContent = mission.description;
    card.appendChild(description);

    // Barra de progresso
    const progressContainer = document.createElement('div');
    progressContainer.className = 'mission-progress-container';
    progressContainer.setAttribute('role', 'progressbar');
    progressContainer.setAttribute('aria-label', `Progresso: ${mission.current}/${mission.target}`);
    progressContainer.setAttribute('aria-valuenow', String(mission.current));
    progressContainer.setAttribute('aria-valuemin', '0');
    progressContainer.setAttribute('aria-valuemax', String(mission.target));

    const progressFill = document.createElement('div');
    progressFill.className = 'mission-progress-fill';
    const progressPercent = Math.min(mission.progress * 100, 100);
    progressFill.style.width = `${progressPercent}%`;
    progressContainer.appendChild(progressFill);
    card.appendChild(progressContainer);

    // Texto de progresso
    const progressText = document.createElement('div');
    progressText.className = 'mission-progress-text';
    progressText.textContent = `${mission.current} / ${mission.target}`;
    card.appendChild(progressText);

    // Botão de coletar recompensa (se completada e não reclamada)
    if (mission.completed && !mission.claimed) {
        const claimBtn = document.createElement('button');
        claimBtn.className = 'btn-claim';
        claimBtn.textContent = 'Coletar Recompensa';
        claimBtn.addEventListener('click', () => claimReward(mission));
        card.appendChild(claimBtn);
    } else if (mission.claimed) {
        // Missão já reclamada — mostra badge de concluída
        const badge = document.createElement('span');
        badge.className = 'mission-type-badge daily';
        badge.textContent = 'Coletada';
        card.appendChild(badge);
    }

    return card;
}

/**
 * Reclama a recompensa de uma missão.
 */
async function claimReward(mission) {
    if (!activeRealmId || !minerName) return;

    const claimBtn = document.querySelector(`.mission-card .btn-claim`);
    if (claimBtn) {
        claimBtn.disabled = true;
        claimBtn.textContent = 'Coletando...';
    }

    try {
        const response = await fetch(claimMissionUrl(activeRealmId, minerName, mission.id), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
            console.warn('Falha ao coletar recompensa:', error.detail);
            if (claimBtn) {
                claimBtn.disabled = false;
                claimBtn.textContent = 'Coletar Recompensa';
            }
            return;
        }

        const result = await response.json();

        // Atualiza saldo
        balanceSatoshis += result.reward;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        saveSessionState();
        updateStoreUI();

        // Sincroniza com backend
        void syncPlayerState();

        // Recarrega missões
        await loadMissions();

        // Feedback visual
        announceGameStatus(`Recompensa coletada: +${result.reward.toLocaleString()} sats!`);
        playSound('success');
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.error('Erro ao coletar recompensa:', error);
        }
        if (claimBtn) {
            claimBtn.disabled = false;
            claimBtn.textContent = 'Coletar Recompensa';
        }
    }
}

/**
 * Atualiza o progresso das missões com base nos stats atuais.
 */
async function updateMissionsProgress() {
    if (!activeRealmId || !minerName) return;

    try {
        const response = await fetch(updateMissionsUrl(activeRealmId, minerName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: minerName,
                words_found: wordsFoundTotal,
                high_fee_found: highFeeFoundTotal,
                mev_found: mevFoundTotal,
                rbf_used: rbfUsedTotal,
                blocks_completed: blocksCompletedTotal,
                max_round_earnings: maxRoundEarningsTotal,
            }),
        });

        if (!response.ok) return;

        const result = await response.json();

        // Se novas missões foram completadas, recarrega o painel
        if (result.newly_completed_daily?.length > 0 || result.newly_completed_weekly?.length > 0) {
            await loadMissions();
            announceGameStatus('Missões atualizadas! Verifique o painel de missões.');
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.warn('Erro ao atualizar progresso das missões:', error);
        }
    }
}

// Carrega missões ao iniciar sessão
registerSessionInitializer('missions', async () => {
    if (activeRealmId && minerName) {
        await loadMissions(activeRealmId, minerName);

        // Atualiza missões a cada 30 segundos
        clearInterval(missionsRefreshInterval);
        missionsRefreshInterval = setInterval(() => {
            if (sessionReady && activeRealmId && minerName) {
                void loadMissions(activeRealmId, minerName);
            }
        }, 30000);
    }
});

// Atualiza progresso das missões ao encontrar palavras
const originalEndSelection = endSelection;
endSelection = function() {
    const result = originalEndSelection();

    // Atualiza progresso das missões após encontrar palavra
    if (minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// Atualiza progresso ao completar bloco
const originalShowResult = showResult;
showResult = function(success, message) {
    const result = originalShowResult(success, message);

    // Atualiza progresso das missões ao completar bloco
    if (success && minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// Atualiza progresso ao usar RBF
const originalShowOrphanBlockSalvage = showOrphanBlockSalvage;
showOrphanBlockSalvage = function() {
    const result = originalShowOrphanBlockSalvage();

    // Atualiza progresso das missões ao ativar RBF
    if (minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// Atualiza progresso ao comprar hint
const originalBuyHint = buyHint;
buyHint = function() {
    const result = originalBuyHint();

    // Atualiza progresso das missões após comprar hint
    if (minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// Atualiza progresso ao comprar hardware
const originalBuyHardware = buyHardware;
buyHardware = function() {
    const result = originalBuyHardware();

    // Atualiza progresso das missões após comprar hardware
    if (minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// Atualiza progresso ao comprar lightning
const originalBuyLightning = buyLightning;
buyLightning = function() {
    const result = originalBuyLightning();

    // Atualiza progresso das missões após comprar lightning
    if (minerName && activeRealmId) {
        void updateMissionsProgress();
    }

    return result;
};

// ==========================================================================
// Fase 9: Chat em Tempo Real — lógica do painel de chat
// ==========================================================================

// Estado do chat
let chatPanelVisible = false;
let chatMessages = [];
const CHAT_MAX_MESSAGES = 50;
const CHAT_MAX_CHARS = 100;
const CHAT_REACTIONS = [
    { token: '[btc]', iconName: 'coin', label: 'Bitcoin' },
    { token: '[mine]', iconName: 'pickaxe', label: 'Mineração' },
    { token: '[node]', iconName: 'antenna', label: 'Node' },
    { token: '[link]', iconName: 'link', label: 'Conexão' },
    { token: '[energy]', iconName: 'bolt', label: 'Energia' },
    { token: '[rare]', iconName: 'gem', label: 'Raro' },
    { token: '[win]', iconName: 'trophy', label: 'Vitória' }
];

// Elementos DOM do chat
const chatPanelEl = document.getElementById('chat-panel');
const chatMessagesEl = document.getElementById('chat-messages');
const chatInputEl = document.getElementById('chat-input');
const chatSendBtnEl = document.getElementById('chat-send-btn');
const chatEmojiBarEl = document.getElementById('chat-emoji-bar');
const chatRateInfoEl = document.getElementById('chat-rate-info');

if (chatEmojiBarEl) {
    CHAT_REACTIONS.forEach(reaction => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'chat-emoji-btn';
        button.dataset.token = reaction.token;
        button.setAttribute('aria-label', `Inserir reação: ${reaction.label}`);
        button.innerHTML = iconSvg(reaction.iconName);
        chatEmojiBarEl.appendChild(button);
    });
}

/**
 * Constrói a URL do endpoint de chat para o realm atual.
 */
function chatSendUrl(realmId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/chat/send`, API_BASE_URL).toString();
}

/**
 * Constrói a URL do histórico de chat para o realm atual.
 */
function chatHistoryUrl(realmId, limit = 20) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    const url = new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/chat/history`, API_BASE_URL);
    url.searchParams.set('limit', String(Math.min(limit, 50)));
    return url.toString();
}


/**
 * Carrega o histórico recente de mensagens do backend.
 */
async function loadChatHistory() {
    if (!activeRealmId) return;
    if (chatHistoryLoaded || chatHistoryLoading) return;
    const sessionContext = captureSessionContext();
    chatHistoryLoading = true;
    const controller = new AbortController();
    requestControllers.add(controller);
    try {
        const response = await fetch(chatHistoryUrl(activeRealmId, 20), {
            headers: { Accept: 'application/json' },
            signal: controller.signal,
        });
        if (!response.ok) return;
        const data = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        if (data.messages && Array.isArray(data.messages)) {
            chatMessages = data.messages.slice(0, CHAT_MAX_MESSAGES).reverse();
            renderChatMessages();
            chatHistoryLoaded = true;
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.warn('Erro ao carregar histórico do chat:', error);
        }
    } finally {
        requestControllers.delete(controller);
        if (isSessionContextCurrent(sessionContext)) chatHistoryLoading = false;
    }
}

/**
 * Renderiza todas as mensagens do chat no painel.
 */
function renderChatMessages() {
    chatMessagesEl.replaceChildren();
    chatMessages.forEach(msg => {
        appendChatMessage(msg, false);
    });
    scrollToBottom();
}

/**
 * Insere um nó no chat e mantém apenas as mensagens mais recentes.
 */
function appendNodeToChat(node) {
    chatMessagesEl.appendChild(node);
    const allMessages = chatMessagesEl.querySelectorAll('.chat-message');
    if (allMessages.length > CHAT_MAX_MESSAGES) allMessages[0].remove();
}

/**
 * Adiciona uma mensagem ao painel de chat.
 *
 * @param {object} msg - Objeto com username, message, timestamp.
 * @param {boolean} animate - Se true, aplica animação de entrada.
 */
function appendChatMessage(msg, animate = true) {
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message';
    if (!animate) msgEl.style.animation = 'none';

    // Cabeçalho com nome e hora
    const headerEl = document.createElement('div');
    headerEl.className = 'chat-message-header';

    const usernameEl = document.createElement('span');
    usernameEl.className = 'chat-message-username';
    usernameEl.textContent = msg.username;
    headerEl.appendChild(usernameEl);

    const timeEl = document.createElement('span');
    timeEl.className = 'chat-message-time';
    if (msg.timestamp) {
        try {
            const date = new Date(msg.timestamp);
            timeEl.textContent = date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } catch {
            timeEl.textContent = '';
        }
    }
    headerEl.appendChild(timeEl);
    msgEl.appendChild(headerEl);

    // Texto da mensagem
    const textEl = document.createElement('div');
    textEl.className = 'chat-message-text';
    textEl.textContent = msg.message;
    msgEl.appendChild(textEl);

    appendNodeToChat(msgEl);

    scrollToBottom();
}

/**
 * Adiciona uma mensagem de sistema (notificação).
 */
function appendSystemMessage(text) {
    const msgEl = document.createElement('div');
    msgEl.className = 'chat-message system';
    msgEl.textContent = text;
    appendNodeToChat(msgEl);
    scrollToBottom();
}

/**
 * Rola o painel de chat para a mensagem mais recente.
 */
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
    });
}

/**
 * Atualiza o indicador de rate limit no painel.
 */
function updateRateLimitInfo(remaining) {
    if (remaining <= 0) {
        chatRateInfoEl.textContent = 'Limite atingido. Aguarde 1 min.';
        chatRateInfoEl.className = 'chat-rate-info error';
        chatSendBtnEl.disabled = true;
    } else if (remaining <= 2) {
        chatRateInfoEl.textContent = `${remaining} mensagens restantes neste minuto.`;
        chatRateInfoEl.className = 'chat-rate-info warning';
        chatSendBtnEl.disabled = false;
    } else {
        chatRateInfoEl.textContent = `${remaining}/5 mensagens neste minuto.`;
        chatRateInfoEl.className = 'chat-rate-info';
        chatSendBtnEl.disabled = false;
    }
}

/**
 * Valida e envia uma mensagem de chat.
 */
async function sendChatMessage() {
    const text = chatInputEl.value.trim();
    if (!text || !activeRealmId || !minerName) return;
    if (text.length > CHAT_MAX_CHARS) {
        appendSystemMessage(`Mensagem muito longa (máx ${CHAT_MAX_CHARS} caracteres).`);
        return;
    }

    // Desabilita envio durante a requisição
    chatSendBtnEl.disabled = true;
    chatInputEl.disabled = true;

    const controller = new AbortController();
    requestControllers.add(controller);
    try {
        const response = await fetch(chatSendUrl(activeRealmId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, message: text }),
            signal: controller.signal,
        });

        if (response.status === 429) {
            const data = await response.json().catch(() => ({}));
            appendSystemMessage(data.detail || 'Limite de mensagens excedido.');
            updateRateLimitInfo(0);
        } else if (response.status === 400) {
            const data = await response.json().catch(() => ({}));
            appendSystemMessage(data.detail || 'Mensagem bloqueada por moderação.');
        } else if (response.ok) {
            const data = await response.json();
            if (data.message) {
                chatMessages.push(data.message);
                if (chatMessages.length > CHAT_MAX_MESSAGES) chatMessages.shift();
                appendChatMessage(data.message, true);
            }
            chatInputEl.value = '';
            updateRateLimitInfo(remaining - 1);
        } else {
            appendSystemMessage('Erro ao enviar mensagem.');
        }
    } catch (error) {
        if (error.name !== 'AbortError') {
            console.warn('Erro ao enviar mensagem de chat:', error);
        }
        appendSystemMessage('Erro de conexão. Verifique sua rede.');
    } finally {
        requestControllers.delete(controller);
        chatInputEl.disabled = false;
        chatInputEl.focus();
    }
}

/**
 * Insere um token temático no cursor do input.
 */
function insertChatToken(token) {
    if (chatInputEl.disabled) return;
    const start = chatInputEl.selectionStart;
    const end = chatInputEl.selectionEnd;
    const text = chatInputEl.value;
    chatInputEl.value = text.slice(0, start) + token + text.slice(end);
    chatInputEl.selectionStart = chatInputEl.selectionEnd = start + token.length;
    chatInputEl.focus();
}

if (chatSendBtnEl) {
    chatSendBtnEl.addEventListener('click', sendChatMessage);
}

if (chatInputEl) {
    chatInputEl.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendChatMessage();
        }
    });
}

// Reações temáticas em SVG
if (chatEmojiBarEl) {
    chatEmojiBarEl.addEventListener('click', (event) => {
        const btn = event.target.closest('.chat-emoji-btn');
        if (btn) {
            const token = btn.dataset.token;
            if (token) insertChatToken(token);
        }
    });
}

// Limpa estado do chat ao encerrar sessão
const originalTeardownSession = teardownSession;
teardownSession = function(reason) {
    const result = originalTeardownSession(reason);
    chatMessages = [];
    if (chatMessagesEl) chatMessagesEl.replaceChildren();
    if (chatRateInfoEl) {
        chatRateInfoEl.textContent = '';
        chatRateInfoEl.className = 'chat-rate-info';
    }
    if (chatSendBtnEl) chatSendBtnEl.disabled = false;
    return result;
};

// Reconecta ao carregar histórico quando sessão é restaurada
registerSessionInitializer('chat-staking', async () => {
    // Carrega histórico do chat ao iniciar sessão
    if (activeRealmId && minerName && chatPanelVisible) {
        await loadChatHistory();
    }
    // Fase 10: Carrega status de staking ao iniciar sessão
    if (activeRealmId && minerName) {
        await loadStakingStatus();
    }
});

/* ==========================================================================
   Fase 10: Staking de Sats — lógica frontend
   ========================================================================== */

// Estado de staking
let stakeState = createEmptyStakeState();
let stakeCountdownInterval = null;
let stakePollInterval = null;
let selectedStakeDuration = 6; // 6h padrão

// Elementos do painel de staking
const stakingPanelEl = document.getElementById('staking-panel');
const stakingActiveEl = document.getElementById('staking-active');
const stakingFormEl = document.getElementById('staking-form');
const stakingAmountEl = document.getElementById('staking-amount');
const stakingBonusEl = document.getElementById('staking-bonus');
const stakingDurationEl = document.getElementById('staking-duration');
const stakingActiveDurationEl = document.getElementById('staking-active-duration');
const stakingTimerEl = document.getElementById('staking-timer');
const stakingAmountInputEl = document.getElementById('staking-amount-input');
const btnStakeEl = document.getElementById('btn-stake');
const btnCancelStakeEl = document.getElementById('btn-cancel-stake');
const stakingHistoryListEl = document.getElementById('staking-history-list');

// URL helpers para staking
function stakingStakeUrl(realmId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/staking/stake`, API_BASE_URL).toString();
}

function stakingUnstakeUrl(realmId) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/staking/unstake`, API_BASE_URL).toString();
}

function stakingStatusUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/staking/status/${encodeURIComponent(username)}`, API_BASE_URL).toString();
}

function stakingHistoryUrl(realmId, username) {
    if (!REALM_ID_PATTERN.test(realmId)) throw new Error('Realm inválido');
    return new URL(`/api/v1/networks/${encodeURIComponent(realmId)}/staking/history/${encodeURIComponent(username)}`, API_BASE_URL).toString();
}

/**
 * Formata segundos para HH:MM:SS
 */
function formatCountdown(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

/**
 * Atualiza a UI de staking com base no estado atual
 */
function updateStakingUI() {
    if (!stakingPanelEl) return;

    if (stakeState.active) {
        stakingActiveEl.hidden = false;
        stakingFormEl.style.display = 'none';

        stakingAmountEl.textContent = `${stakeState.amount.toLocaleString()} sats`;
        stakingBonusEl.textContent = `+${(stakeState.bonus_percent * 100).toFixed(0)}%`;
        stakingActiveDurationEl.textContent = `${stakeState.duration_hours}h`;

        // Inicia countdown
        startStakeCountdown();
    } else {
        stakingActiveEl.hidden = true;
        stakingFormEl.style.display = '';

        // Para countdown
        stopStakeCountdown();
    }

    // Atualiza botão de stake
    if (btnStakeEl) {
        btnStakeEl.disabled = stakeState.active;
    }
    if (btnCancelStakeEl) {
        btnCancelStakeEl.disabled = !stakeState.active;
    }
}

/**
 * Inicia o countdown do stake
 */
function startStakeCountdown() {
    stopStakeCountdown();

    updateStakeTimer();

    stakeCountdownInterval = setInterval(() => {
        updateStakeTimer();
    }, 1000);

    // Poll a cada 30s para verificar se o stake expirou
    stakePollInterval = setInterval(() => {
        if (activeRealmId && minerName) {
            void loadStakingStatus();
        }
    }, 30000);
}

/**
 * Atualiza o timer do countdown
 */
function updateStakeTimer() {
    if (!stakeState.active || !stakingTimerEl) return;

    const now = Math.floor(Date.now() / 1000);
    const remaining = Math.max(0, stakeState.end_time - now);

    stakingTimerEl.textContent = formatCountdown(remaining);

    if (remaining <= 0) {
        stopStakeCountdown();
        stakeState.active = false;
        updateStakingUI();
        announceGameStatus('Stake expirado. Sats devolvidos à carteira.');
        void loadStakingStatus();
    }
}

/**
 * Para o countdown do stake
 */
function stopStakeCountdown() {
    if (stakeCountdownInterval) {
        clearInterval(stakeCountdownInterval);
        stakeCountdownInterval = null;
    }
    if (stakePollInterval) {
        clearInterval(stakePollInterval);
        stakePollInterval = null;
    }
}

/**
 * Carrega o status do stake do backend
 */
async function loadStakingStatus() {
    if (!activeRealmId || !minerName) return;
    const sessionContext = captureSessionContext();

    try {
        const response = await fetch(stakingStatusUrl(activeRealmId, minerName));
        if (!response.ok) return;

        const data = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        stakeState = {
            active: data.active || false,
            amount: data.amount || 0,
            duration_hours: data.duration_hours || 0,
            bonus_percent: data.bonus_percent || 0,
            start_time: data.start_time || 0,
            end_time: data.end_time || 0,
            time_remaining_seconds: data.time_remaining_seconds || 0,
        };

        updateStakingUI();

        // Carrega histórico
        void loadStakingHistory();
    } catch (error) {
        console.warn('Erro ao carregar status de staking.', error);
    }
}

/**
 * Carrega o histórico de stakes do backend
 */
async function loadStakingHistory() {
    if (!activeRealmId || !minerName || !stakingHistoryListEl) return;
    const sessionContext = captureSessionContext();

    try {
        const response = await fetch(stakingHistoryUrl(activeRealmId, minerName));
        if (!response.ok) return;

        const data = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        const history = data.history || [];

        if (history.length === 0) {
            stakingHistoryListEl.innerHTML = '<div class="loading-state">Nenhum stake realizado ainda.</div>';
            return;
        }

        stakingHistoryListEl.innerHTML = '';
        // Mostra os últimos 10 stakes (mais recentes primeiro)
        const recent = history.slice(-10).reverse();
        for (const entry of recent) {
            const item = document.createElement('div');
            const safeType = ['created', 'unstake', 'expired'].includes(entry.type)
                ? entry.type
                : 'created';
            item.className = `staking-history-item stake-${safeType}`;

            const typeLabel = safeType === 'created' ? 'Stake' :
                              safeType === 'unstake' ? 'Cancelado' : 'Expirado';

            const amountText = safeType === 'unstake'
                ? `${entry.returned.toLocaleString()} sats (penalty: ${entry.penalty.toLocaleString()})`
                : safeType === 'expired' && entry.bonus
                    ? `${entry.amount.toLocaleString()} sats (+${entry.bonus.toLocaleString()} bônus)`
                    : `${entry.amount.toLocaleString()} sats`;

            const date = entry.timestamp
                ? new Date(entry.timestamp * 1000).toLocaleString('pt-BR', {
                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                })
                : '';

            const typeElement = document.createElement('span');
            typeElement.className = 'staking-history-type';
            typeElement.textContent = typeLabel;
            const amountElement = document.createElement('span');
            amountElement.className = 'staking-history-amount';
            amountElement.textContent = amountText;
            const dateElement = document.createElement('span');
            dateElement.className = 'staking-history-date';
            dateElement.textContent = date;
            item.append(typeElement, amountElement, dateElement);
            stakingHistoryListEl.appendChild(item);
        }
    } catch (error) {
        console.warn('Erro ao carregar histórico de staking.', error);
    }
}

/**
 * Realiza um stake de sats
 */
async function performStake() {
    if (!activeRealmId || !minerName) return;
    if (stakeState.active) return;

    const amount = parseInt(stakingAmountInputEl?.value, 10);
    if (!amount || amount < 1000) {
        announceGameStatus('Mínimo de 1.000 sats para staking.');
        return;
    }

    try {
        const response = await fetch(stakingStakeUrl(activeRealmId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: minerName,
                amount: amount,
                duration_hours: selectedStakeDuration,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            announceGameStatus(`Erro ao staking: ${errorData.detail || 'Falha na requisição'}`);
            return;
        }

        const data = await response.json();
        stakeState = {
            active: true,
            amount: data.amount,
            duration_hours: data.duration_hours,
            bonus_percent: data.bonus_percent,
            start_time: data.start_time,
            end_time: data.end_time,
            time_remaining_seconds: data.end_time - data.start_time,
        };

        // Atualiza saldo local
        balanceSatoshis -= amount;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();

        updateStakingUI();
        playSound('buy');
        announceGameStatus(`Stake realizado: ${amount.toLocaleString()} sats por ${selectedStakeDuration}h (+${(data.bonus_percent * 100).toFixed(0)}% bônus)`);

        // Adiciona ao histórico manualmente (o backend já faz, mas atualiza a UI)
        void loadStakingHistory();
    } catch (error) {
        console.error('Erro ao realizar stake.', error);
        announceGameStatus('Erro ao realizar stake. Tente novamente.');
    }
}

/**
 * Cancela um stake ativo (com penalty de 10%)
 */
async function cancelStake() {
    if (!activeRealmId || !minerName) return;
    if (!stakeState.active) return;

    // Confirmação do jogador
    const confirmed = confirm(
        `Cancelar stake de ${stakeState.amount.toLocaleString()} sats?\n\n` +
        `Penalty: 10% (${Math.floor(stakeState.amount * 0.1).toLocaleString()} sats perdidos)\n` +
        `Você receberá: ${Math.floor(stakeState.amount * 0.9).toLocaleString()} sats\n\n` +
        `Tem certeza?`
    );

    if (!confirmed) return;

    try {
        const response = await fetch(stakingUnstakeUrl(activeRealmId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: minerName,
                amount: stakeState.amount,
                duration_hours: stakeState.duration_hours,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            announceGameStatus(`Erro ao cancelar stake: ${errorData.detail || 'Falha na requisição'}`);
            return;
        }

        const data = await response.json();

        // Atualiza saldo local
        balanceSatoshis = data.new_balance;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();

        stakeState = {
            active: false,
            amount: 0,
            duration_hours: 0,
            bonus_percent: 0,
            start_time: 0,
            end_time: 0,
            time_remaining_seconds: 0,
        };

        stopStakeCountdown();
        updateStakingUI();
        playSound('orphan');
        announceGameStatus(`Stake cancelado. Recebido: ${data.returned.toLocaleString()} sats (penalty: ${data.penalty.toLocaleString()} sats)`);

        void loadStakingHistory();
    } catch (error) {
        console.error('Erro ao cancelar stake.', error);
        announceGameStatus('Erro ao cancelar stake. Tente novamente.');
    }
}

// Event listeners para staking
if (btnStakeEl) {
    btnStakeEl.addEventListener('click', performStake);
}

if (btnCancelStakeEl) {
    btnCancelStakeEl.addEventListener('click', cancelStake);
}

// Fase 3: sincroniza o <select> de duração com selectedStakeDuration (1h/6h/24h)
if (stakingDurationEl) {
    stakingDurationEl.addEventListener('change', () => {
        const hours = parseInt(stakingDurationEl.value, 10);
        if ([1, 6, 24].includes(hours)) {
            selectedStakeDuration = hours;
        }
    });
}

// Limpa estado de staking ao encerrar sessão
const originalTeardownForStaking = teardownSession;
teardownSession = function(reason) {
    const result = originalTeardownForStaking(reason);
    stopStakeCountdown();
    stakeState = {
        active: false,
        amount: 0,
        duration_hours: 0,
        bonus_percent: 0,
        start_time: 0,
        end_time: 0,
        time_remaining_seconds: 0,
    };
    updateStakingUI();
    return result;
};

/* ==========================================================================
   Mini-game Decoder — adivinhar palavra BIP39 a partir do TXID truncado
   ========================================================================== */

// Fase: Mini-game Decoder — estado
let decoderTimerInterval = null;
let decoderTimeRemaining = 30;
let decoderActive = false;
let decoderCooldownRemaining = 0;
const DECODER_TIME_LIMIT = 30; // segundos
const DECODER_ROUNDS_INTERVAL = 3; // aparece a cada 3 rodadas

// Elementos DOM do decoder
const decoderModalEl = document.getElementById('decoder-modal');
const decoderTxidEl = document.getElementById('decoder-txid');
const decoderHintLetterEl = document.getElementById('decoder-hint-letter');
const decoderTimerBarEl = document.getElementById('decoder-timer-bar');
const decoderTimerTextEl = document.getElementById('decoder-timer-text');
const decoderInputEl = document.getElementById('decoder-input');
const decoderSubmitBtnEl = document.getElementById('btn-decoder-submit');
const decoderFeedbackEl = document.getElementById('decoder-feedback');
const decoderStreakEl = document.getElementById('decoder-streak');
const decoderWinsEl = document.getElementById('decoder-wins');
const decoderCloseBtnEl = document.getElementById('btn-close-decoder');
const decoderLaunchBtnEl = document.getElementById('btn-decoder-launch');

// Verifica se o decoder está disponível a cada 3 rodadas
// Fase B1: sempre visível — quando indisponível, mostra cooldown (desabilitado)
function checkDecoderAvailability() {
    if (!sessionReady || !activeRealmId || !decoderLaunchBtnEl) return;
    const available = roundNumber % DECODER_ROUNDS_INTERVAL === 0 && !decoderActive;
    // Sempre visível (remove hidden)
    decoderLaunchBtnEl.classList.remove('hidden');
    if (available) {
        decoderLaunchBtnEl.disabled = false;
        decoderLaunchBtnEl.textContent = 'LAUNCH';
        decoderLaunchBtnEl.classList.remove('decoder-cooldown');
    } else {
        decoderLaunchBtnEl.disabled = true;
        decoderLaunchBtnEl.textContent = 'COOLDOWN';
        decoderLaunchBtnEl.classList.add('decoder-cooldown');
    }
}

// Inicia o mini-game Decoder
async function startDecoderGame() {
    if (!activeRealmId || !minerName || decoderActive) return;
    decoderActive = true;
    decoderLaunchBtnEl.classList.add('hidden');

    try {
        const url = new URL(`/api/v1/networks/${encodeURIComponent(activeRealmId)}/decoder/start`, API_BASE_URL);
        const response = await fetch(url.toString(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ username: minerName }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            if (response.status === 429) {
                decoderCooldownRemaining = parseInt(errorData.detail?.match(/\d+/)?.[0] || '180', 10);
                announceGameStatus(`Decoder: aguarde ${decoderCooldownRemaining}s para jogar novamente.`);
                decoderActive = false;
                decoderLaunchBtnEl.classList.remove('hidden');
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Popula o modal
        decoderTxidEl.textContent = data.tx_stub;
        decoderHintLetterEl.textContent = data.first_letter;
        decoderStreakEl.textContent = data.streak;
        decoderWinsEl.textContent = data.wins;
        decoderInputEl.value = '';
        decoderInputEl.disabled = false;
        decoderSubmitBtnEl.disabled = false;
        decoderFeedbackEl.hidden = true;
        decoderCloseBtnEl.hidden = true;

        // Reseta timer
        decoderTimeRemaining = DECODER_TIME_LIMIT;
        updateDecoderTimer();

        // Abre modal
        setModalState(decoderModalEl, true);
        decoderInputEl.focus();

        // Inicia timer
        clearInterval(decoderTimerInterval);
        decoderTimerInterval = setInterval(() => {
            decoderTimeRemaining--;
            updateDecoderTimer();
            if (decoderTimeRemaining <= 0) {
                clearInterval(decoderTimerInterval);
                decoderTimerInterval = null;
                handleDecoderTimeout();
            }
        }, 1000);

    } catch (error) {
        console.error('Erro ao iniciar decoder.', error);
        decoderActive = false;
        decoderLaunchBtnEl.classList.remove('hidden');
    }
}

// Atualiza a barra e o texto do timer
function updateDecoderTimer() {
    const percentage = (decoderTimeRemaining / DECODER_TIME_LIMIT) * 100;
    decoderTimerBarEl.style.width = `${percentage}%`;
    decoderTimerTextEl.textContent = `${decoderTimeRemaining}s`;

    if (decoderTimeRemaining <= 10) {
        decoderTimerBarEl.classList.add('urgent');
    } else {
        decoderTimerBarEl.classList.remove('urgent');
    }
}

// Envia resposta do decoder
async function submitDecoderAnswer() {
    const answer = decoderInputEl.value.trim();
    if (!answer || !activeRealmId || !minerName) return;

    decoderInputEl.disabled = true;
    decoderSubmitBtnEl.disabled = true;
    clearInterval(decoderTimerInterval);
    decoderTimerInterval = null;

    try {
        const url = new URL(`/api/v1/networks/${encodeURIComponent(activeRealmId)}/decoder/submit`, API_BASE_URL);
        const response = await fetch(url.toString(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ username: minerName, answer }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();

        if (data.correct) {
            // Acerto!
            decoderFeedbackEl.className = 'decoder-feedback correct';
            decoderFeedbackEl.innerHTML = iconSvg('check');
            decoderFeedbackEl.append(
                document.createTextNode(` Correto! A palavra era "${data.word}".`),
                document.createElement('br'),
                document.createTextNode(`+5.000 sats + power-up: ${data.powerup_id}`)
            );
            decoderFeedbackEl.hidden = false;

            // Animação de recompensa (guard: .decoder-content pode não existir
            // no HTML — antes lançava TypeError e interrompia o caminho de
            // sucesso: saldo +5.000, streak e syncPlayerState).
            const decoderContent = decoderModalEl.querySelector('.decoder-content');
            if (decoderContent) decoderContent.classList.add('reward');
            playSound('success');

            // Atualiza saldo local
            balanceSatoshis += 5000;
            document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();

            decoderStreakEl.textContent = data.streak;
            decoderWinsEl.textContent = data.wins;

            // Sincroniza estado do jogador
            void syncPlayerState();

        } else {
            // Erro
            decoderFeedbackEl.className = 'decoder-feedback wrong';
            decoderFeedbackEl.innerHTML = iconSvg('cross');
            decoderFeedbackEl.append(document.createTextNode(` Incorreto. A palavra era "${data.word}". Sem penalidade.`));
            decoderFeedbackEl.hidden = false;
            playSound('orphan');

            decoderStreakEl.textContent = data.streak;
        }

        decoderCloseBtnEl.hidden = false;

    } catch (error) {
        console.error('Erro ao enviar resposta do decoder.', error);
        decoderInputEl.disabled = false;
        decoderSubmitBtnEl.disabled = false;
    }
}

// Timeout do decoder
function handleDecoderTimeout() {
    decoderInputEl.disabled = true;
    decoderSubmitBtnEl.disabled = true;

    decoderFeedbackEl.className = 'decoder-feedback timeout';
    decoderFeedbackEl.innerHTML = iconSvg('timer');
    decoderFeedbackEl.append(document.createTextNode(' Tempo esgotado! Tente novamente mais tarde.'));
    decoderFeedbackEl.hidden = false;
    decoderCloseBtnEl.hidden = false;
    playSound('orphan');
}

// Fecha o modal do decoder
function closeDecoderModal() {
    clearInterval(decoderTimerInterval);
    decoderTimerInterval = null;
    decoderActive = false;
    setModalState(decoderModalEl, false);

    // Remove animação de recompensa
    const content = decoderModalEl.querySelector('.decoder-content');
    if (content) content.classList.remove('reward');

    // Mostra botão de lançamento novamente se disponível
    checkDecoderAvailability();
}

// Event listeners do decoder
if (decoderLaunchBtnEl) {
    decoderLaunchBtnEl.addEventListener('click', startDecoderGame);
}

if (decoderSubmitBtnEl) {
    decoderSubmitBtnEl.addEventListener('click', submitDecoderAnswer);
}

if (decoderCloseBtnEl) {
    decoderCloseBtnEl.addEventListener('click', closeDecoderModal);
}

// Enter no input envia resposta
if (decoderInputEl) {
    decoderInputEl.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !decoderSubmitBtnEl.disabled) {
            event.preventDefault();
            submitDecoderAnswer();
        }
    });
}

// Verifica disponibilidade do decoder quando a rodada muda
const originalPrepareNextBlock = prepareNextBlock;
prepareNextBlock = function() {
    originalPrepareNextBlock();
    checkDecoderAvailability();
};

// ============================================
// Fase 4: Skill Tree — Árvore de Habilidades
// ============================================

let skillTreeData = null;
let skillTreeLoading = false;

// Elementos da Skill Tree
const skillsPanelEl = document.getElementById('skills-panel');
const skillsHeaderEl = document.getElementById('skills-header');
const skillsPointsValueEl = document.getElementById('skills-points-value');
const skillsLevelValueEl = document.getElementById('skills-level-value');
const skillsLoadingEl = document.getElementById('skills-loading');
const skillsContentEl = document.getElementById('skills-content');

// Carrega a skill tree do backend
async function loadSkillTree() {
    if (skillTreeLoading) return;
    const sessionContext = captureSessionContext();
    skillTreeLoading = true;

    if (skillsLoadingEl) skillsLoadingEl.hidden = false;
    if (skillsContentEl) skillsContentEl.hidden = true;

    try {
        const response = await fetch(activeNetworkApiUrl(`skills/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar skill tree');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        skillTreeData = payload;
        applySkillBonuses(skillTreeData.bonuses);
        renderSkillTree();
    } catch (error) {
        console.error('Erro ao carregar skill tree:', error);
        if (skillsLoadingEl) skillsLoadingEl.textContent = 'Erro ao carregar habilidades.';
    } finally {
        if (isSessionContextCurrent(sessionContext)) {
            skillTreeLoading = false;
            if (skillsLoadingEl) skillsLoadingEl.hidden = true;
        }
    }
}

// Renderiza a UI da skill tree
function renderSkillTree() {
    if (!skillTreeData || !skillsContentEl) return;

    // O backend retorna { player_level, points_remaining, branches: { key: { name, current_level, max_level, nodes: [{ level, name, description, unlocked }] } } }
    const { branches, points_remaining, player_level } = skillTreeData;

    // Atualiza header
    if (skillsPointsValueEl) skillsPointsValueEl.textContent = points_remaining;
    if (skillsLevelValueEl) skillsLevelValueEl.textContent = player_level;

    // Limpa conteúdo anterior
    skillsContentEl.innerHTML = '';

    // Renderiza cada ramo
    for (const [branchKey, branchDef] of Object.entries(branches)) {
        const branchEl = document.createElement('div');
        branchEl.className = 'skill-branch';
        branchEl.dataset.branch = branchKey;

        const branchTitle = document.createElement('h3');
        branchTitle.className = 'skill-branch-title';
        branchTitle.textContent = branchDef.name;
        branchEl.appendChild(branchTitle);

        const branchDesc = document.createElement('p');
        branchDesc.className = 'skill-branch-desc';
        branchDesc.textContent = branchDef.description || '';
        branchEl.appendChild(branchDesc);

        const nodesContainer = document.createElement('div');
        nodesContainer.className = 'skill-nodes';

        for (const node of branchDef.nodes) {
            const nodeEl = document.createElement('div');
            nodeEl.className = 'skill-node';
            if (node.unlocked) nodeEl.classList.add('unlocked');
            // O próximo nível do ramo é o nó clicável (o backend não envia "available")
            const isNext = !node.unlocked && node.level === (branchDef.current_level || 0) + 1;
            if (isNext && points_remaining > 0) nodeEl.classList.add('available');

            const nodeIcon = document.createElement('span');
            nodeIcon.className = 'skill-node-icon';
            setSvgIcon(nodeIcon, node.unlocked ? 'check' : (isNext ? 'bolt' : 'circle'));
            nodeEl.appendChild(nodeIcon);

            const nodeInfo = document.createElement('div');
            nodeInfo.className = 'skill-node-info';

            const nodeLevel = document.createElement('span');
            nodeLevel.className = 'skill-node-level';
            nodeLevel.textContent = `Nível ${node.level}`;
            nodeInfo.appendChild(nodeLevel);

            const nodeEffect = document.createElement('span');
            nodeEffect.className = 'skill-node-effect';
            nodeEffect.textContent = node.description || node.name || '';
            nodeInfo.appendChild(nodeEffect);

            nodeEl.appendChild(nodeInfo);

            if (isNext && points_remaining > 0) {
                nodeEl.addEventListener('click', () => unlockSkill(branchKey));
            }

            nodesContainer.appendChild(nodeEl);
        }

        branchEl.appendChild(nodesContainer);
        skillsContentEl.appendChild(branchEl);
    }

    skillsContentEl.hidden = false;
}

// Desbloqueia a próxima habilidade de um ramo
async function unlockSkill(branchKey) {
    if (!skillTreeData || skillTreeData.points_remaining <= 0) return;

    try {
        const response = await fetch(activeNetworkApiUrl(`skills/${encodeURIComponent(minerName)}/upgrade`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, branch: branchKey })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao desbloquear habilidade', 'error');
            return;
        }

        playSound('success');
        showNotification('Habilidade desbloqueada!', 'success');

        // Recarrega a skill tree
        await loadSkillTree();

    } catch (error) {
        console.error('Erro ao desbloquear habilidade:', error);
        showNotification('Erro ao desbloquear habilidade', 'error');
    }
}

// Aplica bônus das habilidades no jogo
function applySkillBonuses(bonuses) {
    const miningTimeBonus = Math.max(0, Number(bonuses?.mining_time_bonus) || 0);
    const searchDiscount = Math.min(
        Math.max(0, Number(bonuses?.search_discount_percent) || 0) / 100,
        1
    );
    const rewardBonus = Math.min(
        Math.max(0, Number(bonuses?.lightning_reward_percent) || 0) / 100,
        1
    );

    skillTimeBonus = miningTimeBonus;
    baseTimeLimit = 60 + skillTimeBonus;
    hintCost = Math.round(HINT_PRICE * (1 - searchDiscount));
    skillRewardBonus = rewardBonus;
}

registerSessionInitializer('skills', async () => {
    await loadSkillTree();
});

// ============================================
// Fase 5: Energy System — Sistema de Energia
// ============================================

let energyState = createInitialEnergyState();
let energyTimerInterval = null;
let pendingEnergyRoundId = null;
let energyRefundFlushPending = false;
const ENERGY_REFUNDS_STORAGE_KEY = 'mempool-miner-energy-refunds';
const ENERGY_PENDING_SPENDS_STORAGE_KEY = 'mempool-miner-energy-pending-spends';

/**
 * Preserva metadados do status quando spend/buy retornam apenas campos mutados.
 */
function mergeEnergyState(payload) {
    return { ...energyState, ...payload };
}

function createEnergyRoundId() {
    return crypto.randomUUID();
}

function loadPendingEnergyRefunds() {
    try {
        const raw = JSON.parse(localStorage.getItem(ENERGY_REFUNDS_STORAGE_KEY) || '[]');
        if (!Array.isArray(raw)) return new Map();
        return new Map(raw
            .filter(item => item?.roundId && item?.realmId && item?.username)
            .map(item => [item.roundId, item]));
    } catch (error) {
        console.warn('Refunds de energia persistidos foram ignorados.', error);
        return new Map();
    }
}

const pendingEnergyRefunds = loadPendingEnergyRefunds();

function loadPendingEnergySpends() {
    try {
        const raw = JSON.parse(localStorage.getItem(ENERGY_PENDING_SPENDS_STORAGE_KEY) || '[]');
        if (!Array.isArray(raw)) return new Map();
        return new Map(raw
            .filter(item => item?.roundId && item?.realmId && item?.username)
            .map(item => [item.roundId, item]));
    } catch (error) {
        console.warn('Spends de energia pendentes foram ignorados.', error);
        return new Map();
    }
}

const pendingEnergySpends = loadPendingEnergySpends();

function persistPendingEnergyRefunds() {
    try {
        localStorage.setItem(
            ENERGY_REFUNDS_STORAGE_KEY,
            JSON.stringify(Array.from(pendingEnergyRefunds.values()))
        );
    } catch (error) {
        console.warn('Não foi possível persistir refunds de energia.', error);
    }
}

function persistPendingEnergySpends() {
    try {
        localStorage.setItem(
            ENERGY_PENDING_SPENDS_STORAGE_KEY,
            JSON.stringify(Array.from(pendingEnergySpends.values()))
        );
    } catch (error) {
        console.warn('Não foi possível persistir spends de energia.', error);
    }
}

function reservePendingEnergySpend(realmId, username) {
    if (pendingEnergyRoundId && pendingEnergySpends.has(pendingEnergyRoundId)) {
        return pendingEnergyRoundId;
    }
    const existing = Array.from(pendingEnergySpends.values()).find(
        item => item.realmId === realmId && item.username === username
    );
    const roundId = existing?.roundId || createEnergyRoundId();
    pendingEnergyRoundId = roundId;
    pendingEnergySpends.set(roundId, { roundId, realmId, username });
    persistPendingEnergySpends();
    return roundId;
}

function clearPendingEnergySpend(roundId) {
    pendingEnergySpends.delete(roundId);
    persistPendingEnergySpends();
    if (pendingEnergyRoundId === roundId) pendingEnergyRoundId = null;
}

async function recoverPendingEnergySpends() {
    for (const [roundId, entry] of Array.from(pendingEnergySpends.entries())) {
        try {
            const response = await fetch(networkApiUrl(
                entry.realmId,
                `energy/spend?username=${encodeURIComponent(entry.username)}&round_id=${encodeURIComponent(roundId)}`
            ), { method: 'POST', headers: { 'Content-Type': 'application/json' } });
            if (![200, 400, 409].includes(response.status)) continue;
            await queueEnergyRefund(roundId, entry.realmId, entry.username);
            clearPendingEnergySpend(roundId);
        } catch (error) {
            console.warn(`Spend de energia ${roundId} continua pendente.`, error);
        }
    }
}

async function flushPendingEnergyRefunds() {
    if (energyRefundFlushPending || pendingEnergyRefunds.size === 0) return;
    energyRefundFlushPending = true;
    try {
        for (const [roundId, entry] of pendingEnergyRefunds) {
            try {
                const response = await fetch(networkApiUrl(
                    entry.realmId,
                    `energy/refund?username=${encodeURIComponent(entry.username)}&round_id=${encodeURIComponent(roundId)}`
                ), { method: 'POST', headers: { 'Content-Type': 'application/json' } });
                if (!response.ok) {
                    if (response.status >= 400 && response.status < 500) {
                        pendingEnergyRefunds.delete(roundId);
                        persistPendingEnergyRefunds();
                    }
                    continue;
                }
                const payload = await response.json();
                if (entry.realmId === activeRealmId && entry.username === minerName) {
                    energyState = mergeEnergyState(payload);
                    updateEnergyUI();
                }
                pendingEnergyRefunds.delete(roundId);
                persistPendingEnergyRefunds();
            } catch (error) {
                console.warn(`Refund de energia pendente para ${roundId}.`, error);
            }
        }
    } finally {
        energyRefundFlushPending = false;
    }
}

async function queueEnergyRefund(roundId, realmId, username) {
    pendingEnergyRefunds.set(roundId, { roundId, realmId, username });
    persistPendingEnergyRefunds();
    await flushPendingEnergyRefunds();
}

// Elementos do Energy System
const uiEnergyBarEl = document.getElementById('ui-energy-bar');
const uiEnergyCountEl = document.getElementById('ui-energy-count');
const uiEnergyTimerEl = document.getElementById('ui-energy-timer');
const btnBuyEnergyEl = document.getElementById('btn-buy-energy');

// Carrega estado de energia do backend
async function loadEnergyState(resumeRound = true) {
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl(`energy/status?username=${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar energia');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        energyState = payload;
        updateEnergyUI();
        if (resumeRound && energyState.current > 0) {
            void requestPlayableBlockBuild();
        }
    } catch (error) {
        console.error('Erro ao carregar energia:', error);
    }
}

// Atualiza UI de energia
function updateEnergyUI() {
    if (!uiEnergyBarEl || !uiEnergyCountEl) return;

    const { current, max, next_refill_at } = energyState;
    const percent = (current / max) * 100;

    // Atualiza barra
    uiEnergyBarEl.style.width = `${percent}%`;
    uiEnergyBarEl.setAttribute('aria-valuenow', current);
    uiEnergyBarEl.setAttribute('aria-valuetext', `${current} de ${max} energia`);

    // Estado de energia baixa
    if (current <= 2) {
        uiEnergyBarEl.classList.add('low');
    } else {
        uiEnergyBarEl.classList.remove('low');
    }

    // Atualiza contador
    uiEnergyCountEl.textContent = `${current}/${max}`;

    // Atualiza timer de regeneração (next_refill_at é timestamp UNIX em segundos)
    if (next_refill_at && uiEnergyTimerEl) {
        const refillTime = new Date(next_refill_at * 1000);
        const now = new Date();
        const diff = refillTime - now;

        if (diff > 0) {
            const minutes = Math.floor(diff / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            uiEnergyTimerEl.textContent = `+1 em ${minutes}m ${seconds}s`;
        } else {
            uiEnergyTimerEl.textContent = '';
        }
    }
}

// Inicia timer de energia
function startEnergyTimer() {
    if (energyTimerInterval) clearInterval(energyTimerInterval);

    energyTimerInterval = setInterval(async () => {
        await loadEnergyState();
    }, 10000); // Atualiza a cada 10s
}

// Gasta 1 energia antes de iniciar rodada
async function spendEnergy(roundId, realmId, username) {
    const isCurrentSession = () => realmId === activeRealmId && username === minerName;
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            const response = await fetch(networkApiUrl(
                realmId,
                `energy/spend?username=${encodeURIComponent(username)}&round_id=${encodeURIComponent(roundId)}`
            ), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                if (response.status === 400) {
                    if (isCurrentSession()) {
                        showNotification('Energia insuficiente! Aguarde regeneração ou compre mais.', 'error');
                    }
                    return false;
                }
                if (response.status === 409) {
                    if (isCurrentSession()) {
                        showNotification('A tentativa anterior já foi compensada. Tente novamente.', 'error');
                    }
                    return false;
                }
                if (response.status >= 400 && response.status < 500) return false;
                throw new Error(`Falha ao gastar energia: HTTP ${response.status}`);
            }

            const payload = await response.json();
            if (isCurrentSession()) {
                energyState = mergeEnergyState(payload);
                updateEnergyUI();
            }
            return true;
        } catch (error) {
            console.error('Erro ao gastar energia:', error);
            if (attempt === 0) continue;
            if (isCurrentSession()) {
                await loadEnergyState(false);
                showNotification('Não foi possível confirmar a energia. Estado sincronizado.', 'error');
            }
            return null;
        }
    }
    return null;
}

// Compra 3 energia por 2.000 sats
async function buyEnergy() {
    if (!btnBuyEnergyEl) return;

    const originalContent = btnBuyEnergyEl.innerHTML;
    btnBuyEnergyEl.disabled = true;
    btnBuyEnergyEl.textContent = '...';

    try {
        const response = await fetch(activeNetworkApiUrl(`energy/buy?username=${encodeURIComponent(minerName)}`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao comprar energia', 'error');
            return;
        }

        energyState = mergeEnergyState(await response.json());
        updateEnergyUI();
        playSound('buy');
        showNotification('+3 Energia comprada!', 'success');
        // Fase 2: espelha o saldo retornado pelo backend (fonte de verdade)
        void loadPlayerState(activeRealmId, minerName);
        void requestPlayableBlockBuild();
    } catch (error) {
        console.error('Erro ao comprar energia:', error);
        showNotification('Erro ao comprar energia', 'error');
    } finally {
        btnBuyEnergyEl.disabled = false;
        btnBuyEnergyEl.innerHTML = originalContent;
    }
}

// Event listeners do Energy System
if (btnBuyEnergyEl) {
    btnBuyEnergyEl.addEventListener('click', buyEnergy);
}

// Carrega energia ao iniciar sessão
registerSessionInitializer('energy', async () => {
    await recoverPendingEnergySpends();
    await flushPendingEnergyRefunds();
    await loadEnergyState();
    startEnergyTimer();
});

// ============================================
// Fase 10: Season Pass — Passaporte de Temporada
// ============================================

let seasonData = null;
let seasonTimerInterval = null;

// Elementos do Season Pass
const seasonPanelEl = document.getElementById('season-panel');
const seasonIdValueEl = document.getElementById('season-id-value');
const seasonLevelValueEl = document.getElementById('season-level-value');
const seasonXpValueEl = document.getElementById('season-xp-value');
const seasonProgressBarEl = document.getElementById('season-progress-bar');
const seasonProgressFillEl = document.getElementById('season-progress-fill');
const seasonProgressTextEl = document.getElementById('season-progress-text');
const seasonTimerEl = document.getElementById('season-timer');
const btnBuySeasonPremiumEl = document.getElementById('btn-buy-season-premium');
const seasonLoadingEl = document.getElementById('season-loading');
const seasonContentEl = document.getElementById('season-content');
const seasonRewardsFreeEl = document.getElementById('season-rewards-free');
const seasonRewardsPremiumEl = document.getElementById('season-rewards-premium');

// Carrega dados da temporada do backend
async function loadSeasonData() {
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl(`season/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar temporada');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        seasonData = payload;
        renderSeasonUI();
    } catch (error) {
        console.error('Erro ao carregar temporada:', error);
        if (seasonLoadingEl) seasonLoadingEl.textContent = 'Erro ao carregar temporada.';
    }
}

// Adiciona XP à temporada (chamado a cada palavra encontrada)
async function addSeasonXP(xpAmount) {
    if (!xpAmount || xpAmount <= 0) return;
    try {
        const response = await fetch(activeNetworkApiUrl(`season/${encodeURIComponent(minerName)}/add-xp`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ xp: xpAmount })
        });
        if (!response.ok) return;
        const result = await response.json();
        // Atualiza estado local da temporada
        if (seasonData) {
            seasonData.level = result.level;
            seasonData.xp = result.xp;
            renderSeasonUI();
        }
        if (result.leveled_up) {
            showNotification(`Temporada: nível ${result.level} alcançado!`, 'success');
        }
    } catch (error) {
        console.error('Erro ao adicionar XP de temporada:', error);
    }
}

// Renderiza a UI da temporada
function renderSeasonUI() {
    if (!seasonData) return;

    const { season_id, level, xp, xp_for_next, xp_remaining, is_premium, free_rewards, premium_rewards, season_end_seconds, season_ended, claim_period_active, claim_deadline } = seasonData;

    // Atualiza header
    if (seasonIdValueEl) seasonIdValueEl.textContent = season_id;
    if (seasonLevelValueEl) seasonLevelValueEl.textContent = level;
    if (seasonXpValueEl) seasonXpValueEl.textContent = `${xp} / ${xp_for_next}`;

    // Atualiza barra de progresso
    const percent = Math.min(100, (xp / xp_for_next) * 100);
    if (seasonProgressFillEl) seasonProgressFillEl.style.width = `${percent}%`;
    if (seasonProgressBarEl) {
        seasonProgressBarEl.setAttribute('aria-valuenow', Math.round(percent));
    }
    if (seasonProgressTextEl) seasonProgressTextEl.textContent = `${Math.round(percent)}%`;

    // Atualiza timer
    if (seasonTimerEl) {
        if (season_ended && claim_period_active && claim_deadline) {
            // Fase 5.5: temporada encerrada — mostra o prazo de claim
            const deadline = new Date(claim_deadline);
            const now = new Date();
            const remainingMs = deadline.getTime() - now.getTime();
            if (remainingMs > 0) {
                const days = Math.floor(remainingMs / 86400000);
                const hours = Math.floor((remainingMs % 86400000) / 3600000);
                seasonTimerEl.innerHTML = `${iconSvg('timer')}<span>Temporada encerrada — ${days}d ${hours}h para reclamar</span>`;
            } else {
                seasonTimerEl.innerHTML = `${iconSvg('timer')}<span>Temporada encerrada</span>`;
            }
        } else if (season_end_seconds > 0) {
            const days = Math.floor(season_end_seconds / 86400);
            const hours = Math.floor((season_end_seconds % 86400) / 3600);
            seasonTimerEl.innerHTML = `${iconSvg('timer')}<span>${days}d ${hours}h restantes</span>`;
        }
    }

    // Renderiza recompensas
    renderRewards('free', free_rewards);
    renderRewards('premium', premium_rewards);

    // Atualiza botão premium
    if (btnBuySeasonPremiumEl) {
        btnBuySeasonPremiumEl.disabled = is_premium || season_ended;
        btnBuySeasonPremiumEl.innerHTML = `${iconSvg('crown')}<span>${is_premium ? 'Premium Ativo' : 'Premium (50.000 SATS)'}</span>`;
    }

    // Mostra conteúdo
    if (seasonLoadingEl) seasonLoadingEl.hidden = true;
    if (seasonContentEl) seasonContentEl.hidden = false;
}

// Renderiza lista de recompensas
function renderRewards(tab, rewards) {
    const container = tab === 'free' ? seasonRewardsFreeEl : seasonRewardsPremiumEl;
    if (!container) return;

    container.innerHTML = '';

    const levels = Object.keys(rewards).map(Number).sort((a, b) => a - b);

    for (const level of levels) {
        const reward = rewards[level];
        const item = document.createElement('div');
        item.className = 'season-reward-item';
        if (reward.claimed) item.classList.add('claimed');
        else if (reward.unlocked) item.classList.add('unlocked');
        else if (tab === 'premium' && seasonData?.is_premium) item.classList.add('available');

        const icon = document.createElement('div');
        icon.className = 'season-reward-icon';
        setSvgIcon(icon, reward.claimed ? 'check' : (reward.unlocked ? 'star' : 'circle'));
        item.appendChild(icon);

        const info = document.createElement('div');
        info.className = 'season-reward-info';

        const levelEl = document.createElement('div');
        levelEl.className = 'season-reward-level';
        levelEl.textContent = `Nível ${level}`;
        info.appendChild(levelEl);

        const nameEl = document.createElement('div');
        nameEl.className = 'season-reward-name';
        nameEl.textContent = reward.type === 'sats' ? `${reward.value.toLocaleString()} SATS` : reward.value;
        info.appendChild(nameEl);

        const typeEl = document.createElement('div');
        typeEl.className = 'season-reward-type';
        typeEl.textContent = reward.type;
        info.appendChild(typeEl);

        item.appendChild(info);

        if (!reward.claimed && (reward.unlocked || (tab === 'premium' && seasonData?.is_premium))) {
            const claimBtn = document.createElement('button');
            claimBtn.className = 'season-reward-claim';
            claimBtn.textContent = 'Reclamar';
            claimBtn.addEventListener('click', () => claimSeasonReward(level));
            item.appendChild(claimBtn);
        }

        container.appendChild(item);
    }
}

// Reclama recompensa
async function claimSeasonReward(level) {
    try {
        const response = await fetch(activeNetworkApiUrl(`season/${encodeURIComponent(minerName)}/claim/${level}`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao reclamar recompensa', 'error');
            return;
        }

        playSound('success');
        showNotification('Recompensa reclamada!', 'success');

        // Recarrega dados: season (nível/claims) + player state (saldo,
        // bônus de recompensa temporário, badge) para atualizar a UI.
        await loadSeasonData();
        await loadPlayerState(activeRealmId, minerName);
    } catch (error) {
        console.error('Erro ao reclamar recompensa:', error);
        showNotification('Erro ao reclamar recompensa', 'error');
    }
}

// Compra premium
async function buySeasonPremium() {
    if (!btnBuySeasonPremiumEl || btnBuySeasonPremiumEl.disabled) return;

    btnBuySeasonPremiumEl.disabled = true;
    btnBuySeasonPremiumEl.textContent = '...';
    let purchaseSucceeded = false;

    try {
        const response = await fetch(activeNetworkApiUrl(`season/${encodeURIComponent(minerName)}/buy-premium`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao comprar premium', 'error');
            return;
        }

        purchaseSucceeded = true;
        playSound('buy');
        showNotification('Premium ativado!', 'success');

        // Recarrega dados
        await loadSeasonData();
    } catch (error) {
        console.error('Erro ao comprar premium:', error);
        showNotification('Erro ao comprar premium', 'error');
    } finally {
        btnBuySeasonPremiumEl.disabled = purchaseSucceeded;
        if (purchaseSucceeded || seasonData?.is_premium) {
            btnBuySeasonPremiumEl.innerHTML = `${iconSvg('crown')}<span>Premium Ativo</span>`;
        } else {
            btnBuySeasonPremiumEl.innerHTML = `${iconSvg('crown')}<span>Premium (50.000 SATS)</span>`;
        }
    }
}

// Event listeners do Season Pass
if (btnBuySeasonPremiumEl) {
    btnBuySeasonPremiumEl.addEventListener('click', buySeasonPremium);
}

// Timer de atualização da temporada
function startSeasonTimer() {
    if (seasonTimerInterval) clearInterval(seasonTimerInterval);

    seasonTimerInterval = setInterval(async () => {
        await loadSeasonData();
    }, 30000); // Atualiza a cada 30s
}

// Carrega temporada ao iniciar sessão
registerSessionInitializer('season', async () => {
    await loadSeasonData();
    startSeasonTimer();
});

// ============================================
// Fase 9: Block Cards — Tokens Colecionáveis
// ============================================

let cardsData = null;
let currentCardFilter = 'all';

// Elementos do Block Cards
const cardsPanelEl = document.getElementById('cards-panel');
const cardsTotalEl = document.getElementById('cards-total');
const cardsCommonEl = document.getElementById('cards-common');
const cardsRareEl = document.getElementById('cards-rare');
const cardsEpicEl = document.getElementById('cards-epic');
const cardsLegendaryEl = document.getElementById('cards-legendary');
const cardsBonusEl = document.getElementById('cards-bonus');
const cardsLoadingEl = document.getElementById('cards-loading');
const cardsGridEl = document.getElementById('cards-grid');

// Mapeamento de raridade para ícones
const CARD_ICON_NAMES = {
    common: 'pickaxe',
    rare: 'gem',
    epic: 'orb',
    legendary: 'crown',
};

// Carrega dados dos cards do backend
async function loadCardsData() {
    try {
        const response = await fetch(activeNetworkApiUrl(`cards/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar cards');

        cardsData = await response.json();
        renderCardsUI();
    } catch (error) {
        console.error('Erro ao carregar cards:', error);
        if (cardsLoadingEl) cardsLoadingEl.textContent = 'Erro ao carregar cards.';
    }
}

// Renderiza a UI dos cards
function renderCardsUI() {
    if (!cardsData) return;

    // O backend retorna { cards, total, by_rarity, collection_bonus: { raridade: { owned, required, complete, bonus } } }
    const { cards, total, by_rarity, collection_bonus } = cardsData;

    // Atualiza stats
    if (cardsTotalEl) cardsTotalEl.textContent = total;
    if (cardsCommonEl) cardsCommonEl.textContent = by_rarity.common || 0;
    if (cardsRareEl) cardsRareEl.textContent = by_rarity.rare || 0;
    if (cardsEpicEl) cardsEpicEl.textContent = by_rarity.epic || 0;
    if (cardsLegendaryEl) cardsLegendaryEl.textContent = by_rarity.legendary || 0;

    // Atualiza bônus (collection_bonus é um objeto por raridade)
    if (cardsBonusEl && collection_bonus) {
        const complete = Object.values(collection_bonus).filter(b => b.complete);
        if (complete.length > 0) {
            const pct = (getCollectionBonus() * 100).toFixed(1).replace(/\.0$/, '');
            cardsBonusEl.innerHTML = iconSvg('gift');
            cardsBonusEl.append(document.createTextNode(` Bônus: +${pct}% recompensa (${complete.length} coleção(ões) completa(s))`));
        } else {
            cardsBonusEl.innerHTML = iconSvg('gift');
            cardsBonusEl.append(document.createTextNode(' Bônus: -'));
        }
    }

    // Renderiza grid
    renderCardsGrid(cards);

    // Mostra grid
    if (cardsLoadingEl) cardsLoadingEl.hidden = true;
    if (cardsGridEl) cardsGridEl.hidden = false;
}

// Renderiza grid de cards
function renderCardsGrid(cards) {
    if (!cardsGridEl) return;

    cardsGridEl.innerHTML = '';

    // Filtra por raridade
    const filtered = currentCardFilter === 'all' ? cards : cards.filter(c => c.rarity === currentCardFilter);

    if (filtered.length === 0) {
        const emptyState = document.createElement('p');
        emptyState.className = 'cards-empty-state';
        emptyState.textContent = 'Nenhum card encontrado.';
        cardsGridEl.appendChild(emptyState);
        return;
    }

    for (const card of filtered) {
        const cardEl = document.createElement('div');
        cardEl.className = `block-card ${card.rarity}`;

        // Ícone
        const iconEl = document.createElement('div');
        iconEl.className = 'block-card-icon';
        setSvgIcon(iconEl, CARD_ICON_NAMES[card.rarity] || 'pickaxe');
        cardEl.appendChild(iconEl);

        // Raridade
        const rarityEl = document.createElement('div');
        rarityEl.className = 'block-card-rarity';
        rarityEl.textContent = card.rarity;
        cardEl.appendChild(rarityEl);

        // Hash truncado
        const hashEl = document.createElement('div');
        hashEl.className = 'block-card-hash';
        hashEl.textContent = card.block_hash ? `${card.block_hash.slice(0, 8)}...${card.block_hash.slice(-4)}` : '-';
        cardEl.appendChild(hashEl);

        // Stats
        const statsEl = document.createElement('div');
        statsEl.className = 'block-card-stats';
        statsEl.textContent = `#${card.block_number || '?'}`;
        cardEl.appendChild(statsEl);

        // Tooltip
        const tooltipEl = document.createElement('div');
        tooltipEl.className = 'block-card-tooltip';
        tooltipEl.innerHTML = `
            <div>Hash: ${escapeHtml(card.block_hash || '-')}</div>
            <div>Bloco: #${card.block_number || '?'}</div>
            <div>Raridade: ${escapeHtml(card.rarity)}</div>
            ${card.timestamp ? `<div>Data: ${new Date(card.timestamp).toLocaleString('pt-BR')}</div>` : ''}
        `;
        cardEl.appendChild(tooltipEl);

        cardsGridEl.appendChild(cardEl);
    }
}

// Animação de pull de card (quando ganha novo card via WebSocket)
function showCardPullAnimation(card) {
    const overlay = document.createElement('div');
    overlay.className = 'card-pull-overlay';

    const cardEl = document.createElement('div');
    cardEl.className = `card-pull-card ${card.rarity}`;

    const iconEl = document.createElement('div');
    iconEl.className = 'card-pull-icon';
    setSvgIcon(iconEl, CARD_ICON_NAMES[card.rarity] || 'pickaxe');
    cardEl.appendChild(iconEl);

    const rarityEl = document.createElement('div');
    rarityEl.className = 'card-pull-rarity';
    rarityEl.textContent = card.rarity;
    cardEl.appendChild(rarityEl);

    const hashEl = document.createElement('div');
    hashEl.className = 'card-pull-hash';
    hashEl.textContent = card.block_hash || '-';
    cardEl.appendChild(hashEl);

    overlay.appendChild(cardEl);
    document.body.appendChild(overlay);

    // Remove após 3 segundos
    scheduleForSession(() => {
        overlay.classList.add('hidden');
        overlay.remove();
    }, 3000);
}

// Carrega cards ao iniciar sessão
registerSessionInitializer('cards', async () => {
    await loadCardsData();
});

// Credita o card de um bloco minerado na coleção do jogador
async function creditBlockCard(blockHash) {
    if (!blockHash || !minerName) return;
    /* Fase C5: retry em 404 — o card global é criado pelo ingestor ao
     * minerar o bloco; o evento WS pode chegar ANTES do card existir no
     * Redis (corrida). Antes, um 404 descartava o card para sempre.
     * O endpoint é idempotente (sadd no set do jogador), então retry é
     * seguro. */
    const MAX_ATTEMPTS = 3;
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
            const response = await fetch(activeNetworkApiUrl(`cards/${encodeURIComponent(minerName)}/credit`), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: minerName, block_hash: blockHash })
            });
            if (response.status === 404) {
                // card global ainda não existe — tenta de novo
                if (attempt === MAX_ATTEMPTS) {
                    console.warn('Card global ainda não existe após', MAX_ATTEMPTS, 'tentativas:', blockHash);
                    return;
                }
                await new Promise(r => setTimeout(r, 1000 * attempt));
                continue;
            }
            if (!response.ok) return; // 4xx/5xx não-404 — não tem retry
            const result = await response.json();
            if (result.new && result.card) {
                showCardPullAnimation(result.card);
                await loadCardsData();
            }
            return;
        } catch (error) {
            if (attempt === MAX_ATTEMPTS) {
                console.error('Erro ao creditar card:', error);
            } else {
                await new Promise(r => setTimeout(r, 1000 * attempt));
            }
        }
    }
}

// ============================================
// Fase 9: Mercado de Power-ups — Player-to-Player
// ============================================

let marketData = null;
let marketHistoryData = null;
let marketInventory = null;

// Elementos do Mercado
const marketPanelEl = document.getElementById('market-panel');
const marketBrowseEl = document.getElementById('market-browse');
const marketSellEl = document.getElementById('market-sell');
const marketHistoryEl = document.getElementById('market-history');
const marketFilterPowerupEl = document.getElementById('market-filter-powerup');
const btnRefreshMarketEl = document.getElementById('btn-refresh-market');

// Mapeamento de power-ups para ícones
const POWERUP_ICON_NAMES = {
    scanner: 'scanner',
    time_freeze: 'timer',
    magnet: 'magnet',
    precision: 'target',
    double_combo: 'combo',
};

const POWERUP_NAMES = {
    scanner: 'Scanner',
    time_freeze: 'Time Freeze',
    magnet: 'Magnet',
    precision: 'Precision',
    double_combo: 'Double Combo',
};

// Carrega lista do mercado
async function loadMarketList() {
    if (marketLoadingSections.has('browse')) return;
    marketLoadingSections.add('browse');
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl('market/list'), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar mercado');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        marketData = payload;
        renderMarketList();
        marketLoadedSections.add('browse');
        marketLoaded = marketLoadedSections.has('browse') && marketLoadedSections.has('inventory');
    } catch (error) {
        console.error('Erro ao carregar mercado:', error);
    } finally {
        if (isSessionContextCurrent(sessionContext)) marketLoadingSections.delete('browse');
    }
}

// Carrega histórico do mercado
async function loadMarketHistory() {
    if (marketLoadingSections.has('history')) return;
    marketLoadingSections.add('history');
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl('market/history'), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar histórico');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        marketHistoryData = payload;
        renderMarketHistory();
        marketLoadedSections.add('history');
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    } finally {
        if (isSessionContextCurrent(sessionContext)) marketLoadingSections.delete('history');
    }
}

// Carrega inventário de power-ups do jogador
async function loadMarketInventory() {
    if (marketLoadingSections.has('inventory')) return;
    marketLoadingSections.add('inventory');
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl(`powerups/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar inventário');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        marketInventory = payload.inventory || {};
        populateSellDropdown();
        marketLoadedSections.add('inventory');
        marketLoaded = marketLoadedSections.has('browse') && marketLoadedSections.has('inventory');
    } catch (error) {
        console.error('Erro ao carregar inventário:', error);
    } finally {
        if (isSessionContextCurrent(sessionContext)) marketLoadingSections.delete('inventory');
    }
}

// Renderiza lista do mercado
function renderMarketList() {
    if (!marketBrowseEl) return;

    const listings = marketData?.listings || [];
    const filter = marketFilterPowerupEl?.value || 'all';

    const filtered = filter === 'all' ? listings : listings.filter(l => l.powerup_id === filter);

    marketBrowseEl.replaceChildren();

    if (filtered.length === 0) {
        /* Fase 8 (pontas soltas): estado vazio com CTA claro — antes era
         * "Nenhum power-up à venda." (botão morto). Agora orienta o jogador
         * a vender na seção VENDER. */
        const emptyState = document.createElement('div');
        emptyState.className = 'market-empty market-empty-cta';
        const msg = document.createElement('p');
        msg.className = 'market-empty-msg';
        msg.textContent = 'Nenhum item à venda no momento.';
        const hint = document.createElement('p');
        hint.className = 'market-empty-hint';
        hint.textContent = 'Venda o seu na seção VENDER acima — ou jogue para ganhar power-ups.';
        emptyState.append(msg, hint);
        marketBrowseEl.appendChild(emptyState);
        return;
    }

    for (const listing of filtered) {
        const iconName = POWERUP_ICON_NAMES[listing.powerup_id] || 'bolt';
        const name = POWERUP_NAMES[listing.powerup_id] || listing.powerup_id;
        const isOwn = minerName && listing.seller === minerName;

        const row = document.createElement('div');
        row.className = 'market-listing';
        if (isOwn) row.classList.add('market-listing-own');

        const icon = document.createElement('div');
        icon.className = 'market-listing-icon';
        setSvgIcon(icon, iconName);

        const info = document.createElement('div');
        info.className = 'market-listing-info';
        const nameElement = document.createElement('div');
        nameElement.className = 'market-listing-name';
        nameElement.textContent = String(name);
        const seller = document.createElement('div');
        seller.className = 'market-listing-seller';
        seller.textContent = isOwn ? 'Seu listing' : `Vendedor: ${listing.seller}`;
        info.append(nameElement, seller);

        const price = document.createElement('div');
        price.className = 'market-listing-price';
        const priceValue = document.createElement('div');
        priceValue.className = 'market-listing-price-value';
        priceValue.textContent = listing.price.toLocaleString();
        const priceLabel = document.createElement('div');
        priceLabel.className = 'market-listing-price-label';
        priceLabel.textContent = 'SATS';
        price.append(priceValue, priceLabel);

        if (isOwn) {
            // Fase B4: o próprio vendedor cancela em vez de comprar
            const cancelButton = document.createElement('button');
            cancelButton.type = 'button';
            cancelButton.className = 'market-listing-cancel-btn';
            cancelButton.dataset.listingId = String(listing.listing_id);
            cancelButton.textContent = 'Cancelar';
            cancelButton.addEventListener('click', () => cancelMarketListing(cancelButton.dataset.listingId));
            row.append(icon, info, price, cancelButton);
        } else {
            const buyButton = document.createElement('button');
            buyButton.type = 'button';
            buyButton.className = 'market-listing-buy-btn';
            buyButton.dataset.listingId = String(listing.listing_id);
            buyButton.dataset.price = String(listing.price);
            buyButton.textContent = 'Comprar';
            buyButton.addEventListener('click', () => buyMarketListing(buyButton.dataset.listingId));
            row.append(icon, info, price, buyButton);
        }

        marketBrowseEl.appendChild(row);
    }
}

// Fase B4: cancela um listing próprio e devolve o power-up ao inventário
async function cancelMarketListing(listingId) {
    if (!confirm('Cancelar este listing? O power-up voltará para o seu inventário.')) return;
    try {
        const response = await fetch(activeNetworkApiUrl('market/cancel'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ listing_id: listingId, username: minerName })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao cancelar listing', 'error');
            return;
        }

        showNotification('Listing cancelado — power-up devolvido ao inventário.', 'success');
        await Promise.all([loadMarketList(), loadMarketInventory()]);
    } catch (error) {
        console.error('Erro ao cancelar listing:', error);
        showNotification('Erro ao cancelar listing', 'error');
    }
}

// Renderiza histórico
function renderMarketHistory() {
    if (!marketHistoryEl) return;

    const history = marketHistoryData?.sales || [];

    if (history.length === 0) {
        marketHistoryEl.innerHTML = '<p class="market-empty">Nenhum histórico disponível.</p>';
        return;
    }

    let html = '';
    for (const entry of history.slice(0, 20)) {
        const typeClass = entry.type === 'buy' ? '' : 'sell';
        const typeLabel = entry.type === 'buy' ? 'Compra' : 'Venda';
        const time = entry.timestamp ? new Date(entry.timestamp).toLocaleString('pt-BR') : '-';

        html += `
            <div class="market-history-item">
                <span class="market-history-type ${typeClass}">${typeLabel}</span>
                <span class="market-history-powerup">${iconSvg(POWERUP_ICON_NAMES[entry.powerup_id] || 'bolt')} ${escapeHtml(POWERUP_NAMES[entry.powerup_id] || entry.powerup_id)}</span>
                <span class="market-history-price">${entry.price?.toLocaleString() || '-'} SATS</span>
                <span class="market-history-time">${escapeHtml(time)}</span>
            </div>
        `;
    }

    marketHistoryEl.innerHTML = html;
}

// Popula dropdown de venda
function populateSellDropdown() {
    const select = document.getElementById('market-sell-select');
    if (!select || !marketInventory) return;

    select.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Selecione um power-up';
    select.appendChild(placeholder);

    let hasSellable = false;
    for (const [powerupId, count] of Object.entries(marketInventory)) {
        if (count > 0) {
            hasSellable = true;
            const name = POWERUP_NAMES[powerupId] || powerupId;
            const option = document.createElement('option');
            option.value = powerupId;
            option.textContent = `${name} (x${count})`;
            select.appendChild(option);
        }
    }

    /* Fase 8 (pontas soltas): CTA quando o inventário está vazio — antes a
     * aba VENDER era um "botão morto" (select vazio + botão inerte). */
    const emptyCta = document.getElementById('market-sell-empty');
    if (emptyCta) emptyCta.hidden = hasSellable;
}

// Compra power-up do mercado
async function buyMarketListing(listingId) {
    try {
        const response = await fetch(activeNetworkApiUrl('market/buy'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ listing_id: listingId, username: minerName })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao comprar', 'error');
            return;
        }

        playSound('buy');
        showNotification('Power-up comprado!', 'success');

        // Recarrega dados + saldo (Fase 2: backend é a fonte de verdade)
        await Promise.all([loadMarketList(), loadMarketHistory(), loadMarketInventory(), loadPlayerState(activeRealmId, minerName)]);
    } catch (error) {
        console.error('Erro ao comprar:', error);
        showNotification('Erro ao comprar power-up', 'error');
    }
}

// Vende power-up no mercado
async function sellMarketPowerup() {
    const select = document.getElementById('market-sell-select');
    const input = document.getElementById('market-sell-price');

    if (!select || !input) return;

    const powerupId = select.value;
    const price = parseInt(input.value);

    if (!powerupId) {
        showNotification('Selecione um power-up', 'error');
        return;
    }

    if (!price || price <= 0) {
        showNotification('Preço inválido', 'error');
        return;
    }

    /* Fase 6.9: valida o mínimo de 100 sats do backend no frontend — evita
     * erro 422 desnecessário ao enviar o pedido. */
    if (price < 100) {
        showNotification('Preço mínimo é 100 sats', 'error');
        return;
    }

    const btn = document.getElementById('btn-market-sell');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '...';
    }

    try {
        const response = await fetch(activeNetworkApiUrl('market/sell'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, powerup_id: powerupId, price })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao vender', 'error');
            return;
        }

        playSound('success');
        showNotification('Power-up à venda!', 'success');

        // Limpa formulário
        select.value = '';
        input.value = '';
        // Fase B3: fecha a seção de venda e reseta o botão para "VENDER"
        marketSellEl.classList.remove('market-sell-open');
        const hint = document.getElementById('market-sell-hint');
        if (hint) { hint.hidden = true; hint.textContent = ''; }

        // Recarrega dados
        await Promise.all([loadMarketList(), loadMarketHistory(), loadMarketInventory()]);
    } catch (error) {
        console.error('Erro ao vender:', error);
        showNotification('Erro ao vender power-up', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'VENDER';
        }
    }
}

// Botão de vender — Fase 8 (ponta solta da auditoria): a seção #market-sell
// estava com display:none permanente (u-inline-040), então o CTA de venda
// (market-sell-empty) nunca aparecia. Agora VENDER alterna a seção: fecha→abre
// (e popula o dropdown/CTA); já aberta→executa a venda.
// Fase B3: 2 passos explícitos — "ABRIR VENDA" (abre) → "CONFIRMAR VENDA"
// (executa). O texto do botão deixa claro o estado atual.
const btnMarketSell = document.getElementById('btn-market-sell');
if (btnMarketSell && marketSellEl) {
    btnMarketSell.addEventListener('click', () => {
        const isOpen = marketSellEl.classList.contains('market-sell-open');
        if (!isOpen) {
            marketSellEl.classList.add('market-sell-open');
            populateSellDropdown();
            updateSellHint();
            btnMarketSell.textContent = 'CONFIRMAR VENDA';
        } else {
            sellMarketPowerup();
        }
    });
}

// Fase B3: atualiza o hint de preço sugerido + taxa de 5% conforme o
// power-up selecionado. Também pré-preenche o campo de preço com a
// sugestão (o jogador pode editar).
function updateSellHint() {
    const select = document.getElementById('market-sell-select');
    const input = document.getElementById('market-sell-price');
    const hint = document.getElementById('market-sell-hint');
    if (!select || !hint) return;

    const powerupId = select.value;
    if (!powerupId) {
        hint.hidden = true;
        hint.textContent = '';
        return;
    }

    const suggested = marketData?.suggested_prices?.[powerupId];
    const name = POWERUP_NAMES[powerupId] || powerupId;
    let text = '';
    if (suggested && suggested > 0) {
        text = `Preço sugerido: ${suggested.toLocaleString()} SATS`;
        // Pré-preenche o preço apenas se o campo está vazio (não sobrescreve
        // um valor que o jogador já digitou).
        if (input && !input.value) {
            input.value = String(suggested);
        }
    } else {
        text = 'Sem histórico de vendas — defina o preço.';
    }
    // Fase B5: informa a taxa de 5% (cobrada na compra, não na venda).
    text += ' · Taxa de 5% cobrada na compra';
    hint.textContent = text;
    hint.hidden = false;
}

if (document.getElementById('market-sell-select')) {
    document.getElementById('market-sell-select').addEventListener('change', updateSellHint);
}

if (marketFilterPowerupEl) {
    marketFilterPowerupEl.addEventListener('change', renderMarketList);
}

if (btnRefreshMarketEl) {
    btnRefreshMarketEl.addEventListener('click', loadMarketList);
}

// Abre/fecha painel de mercado
const marketToggleBtn = document.getElementById('btn-market');
if (marketToggleBtn && marketPanelEl) {
    marketToggleBtn.addEventListener('click', () => {
        showTab('social');

        if (!marketLoaded) {
            loadMarketList();
            loadMarketInventory();
        }
    });
}

// Carrega mercado ao iniciar sessão
registerSessionInitializer('market', async () => {
    await loadMarketList();
    await loadMarketInventory();
});

// ============================================
// Fase 8: Eventos Globais — Banner e Lógica
// ============================================

// Elementos do banner de eventos globais
eventBannerEl = document.getElementById('global-event-banner');
const globalEventIconEl = document.getElementById('global-event-icon');
const globalEventLabelEl = document.getElementById('global-event-label');
const globalEventDescriptionEl = document.getElementById('global-event-description');
const globalEventCountdownEl = document.getElementById('global-event-countdown');
const btnDismissEventEl = document.getElementById('btn-dismiss-event');

// Descrições dos eventos
const EVENT_DESCRIPTIONS = {
    fee_spike: 'Todas as palavras são High Fee — 3× recompensa!',
    golden_rush: 'Golden Hash aparece 3× mais — 5× recompensa!',
    mempool_flood: 'Grade 15×15 obrigatória — 2× recompensa!',
    lightning_storm: 'Lightning Mode ativo para todos — 10× recompensa!',
};

// Renderiza o banner de evento global
function renderGlobalEventBanner(event, isPreannounce = false) {
    if (!eventBannerEl) return;

    const meta = EVENT_META[event.type] || { iconName: 'bolt', label: event.type, color: '#f7931a' };

    // Atualiza atributos
    eventBannerEl.setAttribute('data-event', event.type);
    eventBannerEl.setAttribute('data-status', isPreannounce ? 'preannounce' : 'active');

    // Atualiza conteúdo
    setSvgIcon(globalEventIconEl, meta.iconName);
    if (globalEventLabelEl) {
        globalEventLabelEl.textContent = isPreannounce ? `${meta.label} em breve!` : meta.label;
    }
    if (globalEventDescriptionEl) {
        globalEventDescriptionEl.textContent = EVENT_DESCRIPTIONS[event.type] || '';
    }

    // Mostra banner
    eventBannerEl.classList.remove('hidden');

    // Atualiza body para efeitos visuais
    if (!isPreannounce) {
        document.body.setAttribute('data-event-active', event.type);
    }

    // Inicia countdown
    startGlobalEventCountdown(event);
}

// Countdown do evento global
function startGlobalEventCountdown(event) {
    if (eventCountdownInterval) clearInterval(eventCountdownInterval);

    const endTime = event.endsAt ? new Date(event.endsAt).getTime() : Date.now() + (EVENT_DURATION[event.type] || 600) * 1000;

    eventCountdownInterval = setInterval(() => {
        const now = Date.now();
        const remaining = endTime - now;

        if (remaining <= 0) {
            clearInterval(eventCountdownInterval);
            hideGlobalEventBanner();
            return;
        }

        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);

        if (globalEventCountdownEl) {
            globalEventCountdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

// Esconde o banner de evento global
function hideGlobalEventBanner() {
    if (eventBannerEl) {
        eventBannerEl.classList.add('hidden');
        eventBannerEl.removeAttribute('data-event');
        eventBannerEl.removeAttribute('data-status');
    }

    if (eventCountdownInterval) {
        clearInterval(eventCountdownInterval);
        eventCountdownInterval = null;
    }

    document.body.removeAttribute('data-event-active');
    activeGlobalEvent = null;
}

// Dismiss button
if (btnDismissEventEl) {
    btnDismissEventEl.addEventListener('click', hideGlobalEventBanner);
}

// Processa eventos globais recebidos via WebSocket
function handleGlobalEventMessage(data) {
    const { event_type, action, ends_at, started_at } = data;

    if (action === 'preannounce') {
        activeGlobalEvent = {
            type: event_type,
            endsAt: ends_at,
            preannounced: true,
        };
        renderGlobalEventBanner(activeGlobalEvent, true);
    } else if (action === 'started') {
        activeGlobalEvent = {
            type: event_type,
            startedAt: started_at,
            endsAt: ends_at,
            preannounced: false,
        };
        renderGlobalEventBanner(activeGlobalEvent, false);

        // Notificação
        const meta = EVENT_META[event_type];
        if (meta) {
            showNotification(`${meta.label} iniciado!`, 'success');
        }
    } else if (action === 'ended') {
        hideGlobalEventBanner();

        const meta = EVENT_META[event_type];
        if (meta) {
            showNotification(`${meta.label} encerrado.`, 'info');
        }
    }
}

// Carrega evento ativo do backend ao iniciar sessão
async function loadActiveGlobalEvent() {
    try {
        const response = await fetch(activeNetworkApiUrl('global-events'), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar eventos globais');

        const data = await response.json();

        if (data.active_event) {
            // Normaliza o shape do REST (event_type/event_started_at/event_ends_at)
            // para o shape interno (type/startedAt/endsAt) usado pelo buildPlayableBlock
            activeGlobalEvent = {
                type: data.active_event.event_type,
                startedAt: data.active_event.event_started_at,
                endsAt: data.active_event.event_ends_at,
                preannounced: data.active_event.event_preannounced === true,
            };
            // Fase 3.2: passa o estado de pre-anúncio ao banner — antes era
            // sempre `false`, então um evento em pre-anúncio (REST com
            // event_preannounced=true) era renderizado como "ativo".
            renderGlobalEventBanner(activeGlobalEvent, activeGlobalEvent.preannounced);
        }
    } catch (error) {
        console.error('Erro ao carregar eventos globais:', error);
    }
}

// Carrega eventos globais ao iniciar sessão
registerSessionInitializer('global-events', async () => {
    await loadActiveGlobalEvent();
});

// ============================================
// Fase 5: Modo Sprint — Rodadas rápidas
// ============================================

let sprintMode = false;
let sprintTimerInterval = null;
let sprintTimeLeft = 30;
let sprintTimeLimit = 30;
let sprintWordsFound = 0;
let sprintStartTime = null;
let currentRoundWords = [];
let sprintRoundActive = false;
let sprintRoundEnding = false;
let sprintRoundStarting = false;

// Elementos do Modo Sprint
const btnSprintModeEl = document.getElementById('btn-sprint-mode');

// Toggle modo sprint
if (btnSprintModeEl) {
    btnSprintModeEl.addEventListener('click', () => {
        sprintMode = !sprintMode;
        btnSprintModeEl.classList.toggle('active', sprintMode);
        btnSprintModeEl.innerHTML = `${iconSvg('sprint')}<span>${sprintMode ? 'Sprint Ativo' : 'Sprint'}</span>`;

        if (sprintMode) {
            showNotification('Modo Sprint ativado! 30s, 4 palavras, 10×10.', 'success');
        }
    });
}

// Inicia rodada sprint
async function startSprintRound() {
    if (sprintRoundActive || sprintRoundEnding || sprintRoundStarting) return;
    const realmId = activeRealmId;
    const username = minerName;
    const generation = sessionGeneration;
    sprintRoundStarting = true;
    try {
        const response = await fetch(networkApiUrl(realmId, 'sprint/start'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        if (!response.ok) throw new Error('Falha ao iniciar sprint');

        const data = await response.json();
        if (
            generation !== sessionGeneration
            || realmId !== activeRealmId
            || username !== minerName
        ) return;

        // Configura grid sprint
        currentGridSize = data.grid_size;
        configureGridSize(currentGridSize);

        // Configura palavras
        currentRoundWords = data.words;
        wordsFoundInBlock = 0;
        currentRoundEarnings = 0;
        if (!renderWordBank()) throw new Error('Falha ao montar grade Sprint');

        // Inicia timer
        // Fase 4.3: cap em SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS (30+5=35s).
        // O backend limita skillTimeBonus a 5s; o cap garante que o frontend
        // nunca exceda o teto mesmo se o bônus vier maior (defesa em profundidade).
        const SPRINT_TIME_LIMIT = 30;
        const SPRINT_MAX_SKILL_TIME_BONUS = 5;
        sprintTimeLimit = Math.min(
            data.time_limit + skillTimeBonus,
            SPRINT_TIME_LIMIT + SPRINT_MAX_SKILL_TIME_BONUS
        );
        sprintTimeLeft = sprintTimeLimit;
        sprintWordsFound = 0;
        sprintStartTime = Date.now();
        sprintRoundActive = true;
        sprintRoundEnding = false;

        showSprintTimer();
        startSprintCountdown();

        showNotification('Modo Sprint iniciado! 30 segundos!', 'success');
    } catch (error) {
        console.error('Erro ao iniciar sprint:', error);
        showNotification('Erro ao iniciar sprint', 'error');
    } finally {
        if (generation === sessionGeneration) sprintRoundStarting = false;
    }
}

// Mostra timer de sprint
function showSprintTimer() {
    let timerEl = document.getElementById('sprint-timer-display');
    if (!timerEl) {
        timerEl = document.createElement('div');
        timerEl.id = 'sprint-timer-display';
        timerEl.className = 'sprint-timer-container';
        timerEl.innerHTML = '<div class="sprint-timer" id="sprint-timer-value">30</div>';
        document.body.appendChild(timerEl);
    }
    updateSprintTimerDisplay();
}

// Atualiza display do timer
function updateSprintTimerDisplay() {
    const timerValueEl = document.getElementById('sprint-timer-value');
    if (timerValueEl) {
        timerValueEl.textContent = sprintTimeLeft;
        timerValueEl.classList.toggle('warning', sprintTimeLeft <= 10);
    }
}

// Countdown do sprint
function startSprintCountdown() {
    if (sprintTimerInterval) clearInterval(sprintTimerInterval);

    sprintTimerInterval = setInterval(() => {
        sprintTimeLeft--;
        updateSprintTimerDisplay();

        if (sprintTimeLeft <= 0) {
            clearInterval(sprintTimerInterval);
            sprintTimerInterval = null;
            void endSprintRound('timeout');
        }
    }, 1000);
}

// Finaliza rodada sprint
async function endSprintRound(reason = 'timeout') {
    if (!sprintRoundActive || sprintRoundEnding) return;
    sprintRoundEnding = true;
    sprintRoundActive = false;
    isPlaying = false;
    clearInterval(sprintTimerInterval);
    sprintTimerInterval = null;

    const generation = sessionGeneration;
    const realmId = activeRealmId;
    const username = minerName;
    const startedAt = sprintStartTime || Date.now();
    const elapsed = (Date.now() - startedAt) / 1000;
    const timeTaken = Math.max(0.001, Math.min(sprintTimeLimit, elapsed));
    sprintTimeLeft = reason === 'completed' ? sprintTimeLeft : 0;
    updateSprintTimerDisplay();

    try {
        await submitSprintResult(
            sprintWordsFound,
            timeTaken,
            realmId,
            username,
            generation
        );
    } finally {
        if (generation === sessionGeneration) sprintRoundEnding = false;
    }
}

// Envia resultado sprint
async function submitSprintResult(
    wordsFound,
    timeTaken,
    realmId = activeRealmId,
    username = minerName,
    generation = sessionGeneration
) {
    try {
        const response = await fetch(networkApiUrl(realmId, 'sprint/submit'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username,
                words_found: wordsFound,
                time_taken: timeTaken
            })
        });

        if (!response.ok) throw new Error('Falha ao enviar resultado');

        const data = await response.json();
        if (generation !== sessionGeneration) return;
        balanceSatoshis += data.reward;
        currentRoundEarnings += data.reward;
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();
        saveSessionState();
        showSprintResult(data);
    } catch (error) {
        console.error('Erro ao enviar resultado sprint:', error);
    }
}

// Mostra resultado sprint
function showSprintResult(data) {
    const overlay = document.createElement('div');
    overlay.className = 'sprint-result-overlay';
    overlay.innerHTML = `
        <div class="sprint-result-card">
            <div class="sprint-result-title">${iconSvg('sprint')}<span>Sprint Completo!</span></div>
            <div class="sprint-result-stats">
                <div class="sprint-result-stat">
                    <span class="sprint-result-stat-label">Palavras encontradas:</span>
                    <span class="sprint-result-stat-value">${data.words_found}</span>
                </div>
                <div class="sprint-result-stat">
                    <span class="sprint-result-stat-label">Tempo:</span>
                    <span class="sprint-result-stat-value">${data.time_taken.toFixed(1)}s</span>
                </div>
                <div class="sprint-result-stat">
                    <span class="sprint-result-stat-label">Recompensa:</span>
                    <span class="sprint-result-stat-value">${data.reward.toLocaleString()} SATS</span>
                </div>
            </div>
            <button type="button" class="sprint-result-btn" id="btn-sprint-play-again">Jogar Novamente</button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Event listener para jogar novamente
    const playAgainBtn = overlay.querySelector('#btn-sprint-play-again');
    if (playAgainBtn) {
        playAgainBtn.addEventListener('click', () => {
            overlay.remove();
            startSprintRound();
        });
    }
}


// Integra com startNetworkRace existente
const originalStartNetworkRaceForSprint = startNetworkRace;
startNetworkRace = async function() {
    if (sprintMode) {
        await startSprintRound();
    } else {
        await originalStartNetworkRaceForSprint();
    }
};

// ============================================
// Fase 5: Sistema de Amigos & Co-op
// ============================================

let friendsData = null;

// Elementos dos Amigos
const friendsPanelEl = document.getElementById('friends-panel');
const friendsAddInputEl = document.getElementById('friends-add-input');
const btnFriendsAddEl = document.getElementById('btn-friends-add');
const friendsCoopBonusEl = document.getElementById('friends-coop-bonus');
const friendsLoadingEl = document.getElementById('friends-loading');
const friendsListEl = document.getElementById('friends-list');

// Carrega lista de amigos
async function loadFriendsList() {
    try {
        const response = await fetch(activeNetworkApiUrl(`friends/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar amigos');

        friendsData = await response.json();
        renderFriendsUI();
    } catch (error) {
        console.error('Erro ao carregar amigos:', error);
        if (friendsLoadingEl) friendsLoadingEl.textContent = 'Erro ao carregar amigos.';
    }
}

// Renderiza UI dos amigos
function renderFriendsUI() {
    if (!friendsData) return;

    const { friends, online_count, co_op_bonus } = friendsData;

    // Atualiza bônus co-op
    if (friendsCoopBonusEl) {
        if (co_op_bonus > 0) {
            const percent = Math.round(co_op_bonus * 100);
            friendsCoopBonusEl.innerHTML = iconSvg('gift');
            friendsCoopBonusEl.append(document.createTextNode(` Bônus Co-op: +${percent}% (${online_count} online)`));
            friendsCoopBonusEl.style.display = 'block';
        } else {
            friendsCoopBonusEl.style.display = 'none';
        }
    }

    // Renderiza lista
    renderFriendsList(friends);

    // Mostra lista
    if (friendsLoadingEl) friendsLoadingEl.hidden = true;
    if (friendsListEl) friendsListEl.hidden = false;
}

// Renderiza lista de amigos
function renderFriendsList(friends) {
    if (!friendsListEl) return;

    friendsListEl.innerHTML = '';

    if (!friends || friends.length === 0) {
        friendsListEl.innerHTML = '<p class="friends-empty">Nenhum amigo adicionado.</p>';
        return;
    }

    for (const friend of friends) {
        const item = document.createElement('div');
        item.className = `friend-item ${friend.online ? 'online' : 'offline'}`;

        const status = document.createElement('div');
        status.className = 'friend-status';
        status.title = friend.online ? 'Online' : 'Offline';
        item.appendChild(status);

        const info = document.createElement('div');
        info.className = 'friend-info';

        const name = document.createElement('div');
        name.className = 'friend-name';
        name.textContent = friend.username;
        info.appendChild(name);

        const meta = document.createElement('div');
        meta.className = 'friend-meta';
        meta.textContent = `Nível ${friend.level} • ${friend.realm_id}`;
        info.appendChild(meta);

        item.appendChild(info);

        const removeBtn = document.createElement('button');
        removeBtn.className = 'friend-remove-btn';
        removeBtn.textContent = 'Remover';
        removeBtn.addEventListener('click', () => removeFriend(friend.username));
        item.appendChild(removeBtn);

        friendsListEl.appendChild(item);
    }
}

// Adiciona amigo
async function addFriend() {
    const friendUsername = friendsAddInputEl?.value?.trim();

    if (!friendUsername) {
        showNotification('Digite o nickname do amigo', 'error');
        return;
    }

    if (friendUsername === minerName) {
        showNotification('Não pode adicionar a si mesmo', 'error');
        return;
    }

    if (!btnFriendsAddEl) return;

    btnFriendsAddEl.disabled = true;
    btnFriendsAddEl.textContent = '...';

    try {
        const response = await fetch(activeNetworkApiUrl('friends/add'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, friend_username: friendUsername })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao adicionar amigo', 'error');
            return;
        }

        playSound('success');
        showNotification(`${friendUsername} adicionado como amigo!`, 'success');

        // Limpa input
        if (friendsAddInputEl) friendsAddInputEl.value = '';

        // Recarrega lista
        await loadFriendsList();
    } catch (error) {
        console.error('Erro ao adicionar amigo:', error);
        showNotification('Erro ao adicionar amigo', 'error');
    } finally {
        if (btnFriendsAddEl) {
            btnFriendsAddEl.disabled = false;
            btnFriendsAddEl.textContent = '+';
        }
    }
}

// Remove amigo
async function removeFriend(friendUsername) {
    try {
        const response = await fetch(activeNetworkApiUrl('friends/remove'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, friend_username: friendUsername })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao remover amigo', 'error');
            return;
        }

        showNotification(`${friendUsername} removido dos amigos.`, 'info');

        // Recarrega lista
        await loadFriendsList();
    } catch (error) {
        console.error('Erro ao remover amigo:', error);
        showNotification('Erro ao remover amigo', 'error');
    }
}

// Event listener para adicionar amigo
if (btnFriendsAddEl) {
    btnFriendsAddEl.addEventListener('click', addFriend);
}

if (friendsAddInputEl) {
    friendsAddInputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            addFriend();
        }
    });
}

// Carrega amigos ao iniciar sessão
registerSessionInitializer('friends', async () => {
    await loadFriendsList();
});

// ============================================
// Fase 10: Mempool Crates — Loot Boxes
// ============================================

let crateState = createInitialCrateState();

// Elementos das Loot Boxes
const btnOpenCrateFree = document.getElementById('btn-open-crate-free');
const btnOpenCrateBuy = document.getElementById('btn-open-crate-buy');
const crateFreeCountEl = document.getElementById('crate-free-count');

// Carrega inventário de crates
async function loadCrateInventory() {
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl(`crates/inventory?username=${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar inventário de crates');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        crateState = payload;
        updateCrateUI();
    } catch (error) {
        console.error('Erro ao carregar inventário de crates:', error);
    }
}

// Atualiza UI das crates
function updateCrateUI() {
    const { free_crates } = crateState;

    // Atualiza contadores
    if (crateFreeCountEl) {
        crateFreeCountEl.textContent = `${free_crates} grátis`;
    }

    // Atualiza botões
    if (btnOpenCrateFree) {
        btnOpenCrateFree.disabled = free_crates <= 0;
        btnOpenCrateFree.textContent = free_crates > 0 ? `Abrir Grátis (${free_crates})` : 'Sem crates grátis';
    }

    if (btnOpenCrateBuy) {
        btnOpenCrateBuy.disabled = false;
    }

}

// Abre crate (grátis ou comprada)
async function openCrate(isFree = true) {
    const previousLegendaryBonus = crateState.legendary_bonus || 0;
    try {
        const response = await fetch(activeNetworkApiUrl('crates/open'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, use_free: isFree })
        });

        if (!response.ok) {
            const error = await response.json();
            showNotification(error.detail || 'Falha ao abrir crate', 'error');
            return;
        }

        const result = await response.json();
        showCrateResult(result);
        if (result.legendary_bonus > previousLegendaryBonus) {
            showNotification(`Bônus Legendário ativo: +${result.legendary_bonus * 100}%`, 'success');
        }

        // Recarrega inventário + saldo (Fase 2: backend é a fonte de verdade)
        await Promise.all([loadCrateInventory(), loadPlayerState(activeRealmId, minerName)]);
    } catch (error) {
        console.error('Erro ao abrir crate:', error);
        showNotification('Erro ao abrir crate', 'error');
    }
}

// Mostra resultado da crate com animação
function showCrateResult(result) {
    // O backend retorna { item: {type, rarity, name, icon, description, value?}, crates_remaining, legendary_bonus }
    const item = result.item || {};
    const rarity = item.rarity || 'common';
    const value = item.value;

    // Cria overlay
    const overlay = document.createElement('div');
    overlay.className = 'crate-modal-overlay';

    // Mapeia raridade para ícone e cor
    const rarityMap = {
        'common': { iconName: 'crate', class: 'rarity-common', label: 'Comum' },
        'uncommon': { iconName: 'gift', class: 'rarity-uncommon', label: 'Incomum' },
        'rare': { iconName: 'gem', class: 'rarity-rare', label: 'Raro' },
        'epic': { iconName: 'star', class: 'rarity-epic', label: 'Épico' },
        'legendary': { iconName: 'trophy', class: 'rarity-legendary', label: 'Lendário' }
    };

    const rarityInfo = rarityMap[rarity] || rarityMap['common'];
    const itemName = item.name || 'Item';

    overlay.innerHTML = `
        <div class="crate-modal-content">
            <div class="crate-icon">${iconSvg(rarityInfo.iconName)}</div>
            <div class="crate-result-title">Crate Aberta!</div>
            <div class="crate-result-item">${escapeHtml(itemName)}</div>
            <div class="crate-result-rarity ${rarityInfo.class}">${rarityInfo.label}</div>
            ${value ? `<div class="crate-result-value">+${Number(value).toLocaleString()} sats</div>` : ''}
            <button class="crate-close-btn" id="btn-close-crate">Fechar</button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Animação de revelação
    const crateIcon = overlay.querySelector('.crate-icon');
    scheduleForSession(() => {
        crateIcon.classList.add('revealed');
    }, 500);

    // Fecha ao clicar
    const btnClose = document.getElementById('btn-close-crate');
    btnClose.addEventListener('click', () => {
        document.body.removeChild(overlay);
    });

    // Fecha ao clicar fora
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });

    // Som de abertura
    playSound('success');

    // Notificação
    showNotification(`Crate aberta: ${itemName} (${rarityInfo.label})`, rarity === 'legendary' ? 'success' : 'info');
}

// Event listeners para crates
if (btnOpenCrateFree) {
    btnOpenCrateFree.addEventListener('click', () => openCrate(true));
}

if (btnOpenCrateBuy) {
    btnOpenCrateBuy.addEventListener('click', () => openCrate(false));
}

// Reclama crates grátis acumuladas (1 a cada 10 blocos minerados)
async function claimFreeCrates() {
    try {
        const response = await fetch(activeNetworkApiUrl('crates/claim'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, blocks_mined: blocksCompletedTotal })
        });
        if (!response.ok) return;
        const result = await response.json();
        if (result.crates_awarded > 0) {
            showNotification(`+${result.crates_awarded} crate(s) grátis!`, 'success');
        }
        await loadCrateInventory();
    } catch (error) {
        console.error('Erro ao reclamar crates grátis:', error);
    }
}


// Abre/fecha painel de power-ups
const powerupsToggleBtn = document.getElementById('btn-powerups-toggle');
const powerupsActiveEl = document.getElementById('powerups-active');
if (powerupsToggleBtn && powerupsActiveEl) {
    powerupsToggleBtn.addEventListener('click', () => {
        if (!sessionReady || !activeRealmId) {
            announceGameStatus('Inicie uma sessão para acessar os Power-ups.');
            return;
        }
        const isHidden = powerupsActiveEl.hidden;
        powerupsActiveEl.hidden = !isHidden;
        powerupsToggleBtn.setAttribute('aria-expanded', String(isHidden));

        if (isHidden) {
            loadPowerupsInventory();
        }
    });
}

// Carrega crates ao iniciar sessão
registerSessionInitializer('crates', async () => {
    await loadCrateInventory();
});

// ============================================
// Fase 2: Sistema de Níveis & Rank
// ============================================

let levelState = createInitialLevelState();

// Elementos da barra de nível
const levelBarContainerEl = document.getElementById('level-bar-container');
const levelIconEl = document.getElementById('level-icon');
const levelNameEl = document.getElementById('level-name');
const levelValueEl = document.getElementById('level-value');
const levelBarFillEl = document.getElementById('level-bar-fill');
const levelBarTextEl = document.getElementById('level-bar-text');

// Carrega estado de nível do backend
async function loadLevelState() {
    const sessionContext = captureSessionContext();
    try {
        const response = await fetch(activeNetworkApiUrl(`level/${encodeURIComponent(minerName)}`), {
            headers: { 'X-Abort-After': '5000' }
        });

        if (!response.ok) throw new Error('Falha ao carregar nível');

        const payload = await response.json();
        if (!isSessionContextCurrent(sessionContext)) return;
        levelState = payload;
        updateLevelUI();

        // Mostra barra de nível
        if (levelBarContainerEl) {
            levelBarContainerEl.hidden = false;
        }
    } catch (error) {
        console.error('Erro ao carregar nível:', error);
    }
}

// Atualiza UI da barra de nível
function updateLevelUI() {
    const { level, xp, xp_to_next, xp_progress, rank, bonuses } = levelState;
    levelTimeBonus = Number(bonuses?.time_bonus_seconds) || 0;

    if (!levelIconEl) return;

    // Atualiza informações
    setSvgIcon(levelIconEl, 'level');

    if (levelNameEl) {
        levelNameEl.textContent = rank.name || 'Script Kiddie';
    }

    if (levelValueEl) {
        levelValueEl.textContent = `Nível ${level}`;
    }

    // Atualiza barra de progresso
    if (levelBarFillEl) {
        levelBarFillEl.style.width = `${xp_progress}%`;
    }

    if (levelBarTextEl) {
        levelBarTextEl.textContent = `${xp} / ${xp_to_next} XP`;
    }

    // Aplica bônus passivos
    if (bonuses) {
        // Desconto de hints
        if (bonuses.hint_discount_percent) {
            window.HINT_DISCOUNT = bonuses.hint_discount_percent;
        }
    }
}

// Adiciona XP ao jogador
async function addXP(xpAmount) {
    try {
        const response = await fetch(activeNetworkApiUrl(`level/${encodeURIComponent(minerName)}/add-xp`), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ xp: xpAmount })
        });

        if (!response.ok) throw new Error('Falha ao adicionar XP');

        const result = await response.json();

        // Atualiza estado local
        levelState.level = result.level;
        levelState.xp = result.xp;
        levelState.xp_to_next = result.xp_to_next;
        /* Fase 6.8: ao fazer level-up, xp_progress deve ser 100% (não 0) —
         * o jogador completou o nível anterior e agora está no novo nível. */
        levelState.xp_progress = result.leveled_up ? 100 : (result.xp / result.xp_to_next) * 100;
        levelState.rank = result.rank;
        levelState.bonuses = result.bonuses;

        updateLevelUI();

        // Notifica level-up
        if (result.leveled_up) {
            showNotification(`Level Up! Você alcançou o nível ${result.level} — ${result.rank.name}!`, 'success');

            // Animação de level-up
            if (levelValueEl) {
                levelValueEl.classList.add('leveled-up');
                scheduleForSession(() => levelValueEl.classList.remove('leveled-up'), 600);
            }
        }

        return result;
    } catch (error) {
        console.error('Erro ao adicionar XP:', error);
        return null;
    }
}

// Calcula XP ganho por palavra
function calculateWordXP(word, comboMultiplier = 1) {
    const baseXP = word.length * 10;
    const comboBonus = comboMultiplier * 5;
    // Fase 4 (pontas soltas): XP deve ser inteiro — o comboMultiplier sobe em
    // 0.5, então baseXP + comboBonus pode ser float (ex.: 67.5). O backend
    // grava str(xp) no Redis e lê com int(), o que quebrava com float.
    return Math.round(baseXP + comboBonus);
}

// Carrega nível ao iniciar sessão
registerSessionInitializer('level', async () => {
    await loadLevelState();
});
