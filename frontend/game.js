/**
 * MEMPOOL MINER: Proof-of-Search com grade dinâmica e upgrade L2 simulado.
 */

const actx = new (window.AudioContext || window.webkitAudioContext)();

/**
 * Reproduz um efeito sonoro curto associado à ação informada.
 */
function playSound(type) {
    if (actx.state === 'suspended') actx.resume();
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
const API_URL = new URL('/api/leaderboard', API_BASE_URL).toString();

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

// Jogador e Loja
let minerName = "Anonymous";
let balanceSatoshis = 0;
let hardwareLevel = 1;
let hardwareNames = ["CPU Miner", "GPU Rig", "ASIC Antminer", "Quantum Node"];
let hardwarePrices = [0, 100000, 500000, 2000000];
let networkTimeBonus = 0; 
const HINT_PRICE = 5000;
const LIGHTNING_PRICE = 1000000;

let roundNumber = 1;
let baseReward = 500;
let wordsFoundInBlock = 0;

let networkTimeLimit = 60;
let networkTimePassed = 0;
let networkInterval;
let leaderboardInterval;
let pendingBuildTimeout;
let lastFoundTime = 0;
let comboMultiplier = 1;

const gridEl = document.getElementById('word-grid');
const svgEl = document.getElementById('lines-svg');
const bankEl = document.getElementById('word-bank-list');
const netProgressEl = document.getElementById('ui-network-progress');
const overlayEl = document.getElementById('grid-overlay');

/**
 * Sincroniza a apresentação visual e semântica de um modal.
 */
function setModalState(modal, isActive) {
    modal.classList.toggle('active', isActive);
    modal.setAttribute('aria-hidden', String(!isActive));
    if (isActive) {
        requestAnimationFrame(() => {
            (modal.querySelector('input, button') || modal).focus();
        });
    }
}

/**
 * Ajusta células e trilhas da grade à dificuldade e à largura disponível.
 */
function configureGridSize(size) {
    const preferredSize = size === 15 ? 28 : 38;
    const availableWidth = Math.max(240, Math.min(620, window.innerWidth - 48));
    const responsiveSize = Math.floor((availableWidth - ((size - 1) * 4)) / size);
    const cellSize = Math.max(14, Math.min(preferredSize, responsiveSize));
    gridEl.style.setProperty('--cell-size', `${cellSize}px`);
    gridEl.style.gridTemplateColumns = `repeat(${size}, var(--cell-size))`;
    gridEl.style.gridTemplateRows = `repeat(${size}, var(--cell-size))`;
}

/**
 * Confirma o contrato mínimo de uma transação recebida pelo WebSocket.
 */
function isValidTransactionEvent(data) {
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
            cell.setAttribute('role', 'gridcell');
            cell.setAttribute('aria-label', `Letra ${cell.innerText}`);
            gridEl.appendChild(cell);
        }
    }
    updateStoreUI();
    fetchLeaderboard();
}
initEmptyGrid();
gridEl.addEventListener('touchstart', handleTouchStart, { passive: false });
gridEl.addEventListener('touchmove', handleTouchMove, { passive: false });
window.addEventListener('resize', () => configureGridSize(currentGridSize));

/**
 * Valida o nickname, abre o WebSocket e inicia a sessão do jogador.
 */
function startSession() {
    const input = document.getElementById('miner-input').value.trim();
    const safeInput = Array.from(input)
        .filter(char => /[\p{L}\p{N}_-]/u.test(char))
        .join('')
        .slice(0, 12);
    minerName = safeInput || "Miner_" + Math.floor(Math.random() * 9999);
    
    document.getElementById('ui-miner-name').innerText = minerName;
    setModalState(document.getElementById('tutorial-modal'), false);
    
    const wsUrl = new URL('/ws/game', API_BASE_URL);
    wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => { prepareNextBlock(); };
    ws.onerror = () => { console.error("Falha na conexão WebSocket."); };
    ws.onclose = () => {
        clearInterval(networkInterval);
        clearInterval(leaderboardInterval);
        clearTimeout(pendingBuildTimeout);
        pendingBuildTimeout = undefined;
        txBuffer = [];
        isPlaying = false;
        overlayEl.classList.remove('hidden');
        const loaderText = overlayEl.querySelector('.loader-text');
        if (loaderText) loaderText.innerText = "Conexão perdida. Recarregue para reconectar.";
    };
    
    ws.onmessage = (event) => {
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
        if (data.action === "transaction_received" && !isPlaying) {
            if (!isValidTransactionEvent(data)) {
                console.warn("Evento de transação fora do contrato foi ignorado.");
                return;
            }
            if (txBuffer.length < WORDS_PER_BLOCK) {
                if (!txBuffer.find(t => t.word === data.word)) {
                    txBuffer.push({ word: data.word, isHighFee: data.is_high_fee, isGolden: data.is_golden, vsize: data.vsize });
                    const loadingText = document.getElementById('tx-loading');
                    if (loadingText) loadingText.innerText = `Aguardando transações (${txBuffer.length}/${WORDS_PER_BLOCK})...`;
                    if (txBuffer.length === WORDS_PER_BLOCK && !isTransitioning) {
                        clearTimeout(pendingBuildTimeout);
                        pendingBuildTimeout = setTimeout(() => {
                            pendingBuildTimeout = undefined;
                            buildPlayableBlock();
                        }, 500);
                    }
                }
            }
        }
        else if (data.action === "block_mined") {
            clearInterval(networkInterval);
            clearTimeout(pendingBuildTimeout);
            pendingBuildTimeout = undefined;
            txBuffer = [];
            const loadingText = document.getElementById('tx-loading');
            if (loadingText) {
                loadingText.innerText = `Aguardando transações (0/${WORDS_PER_BLOCK})...`;
            }
            if (isPlaying) {
                isPlaying = false;
                playSound('orphan');
                showResult(false, "Um novo bloco real chegou ao nó Bitcoin e encerrou esta rodada.");
            } else if (!isTransitioning && !document.getElementById('result-modal').classList.contains('active')) {
                prepareNextBlock();
            }
        }
    };
    
    clearInterval(leaderboardInterval);
    leaderboardInterval = setInterval(fetchLeaderboard, 10000);
}

/**
 * Busca e renderiza o Top 10 sem interpretar dados do servidor como HTML.
 */
async function fetchLeaderboard() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (!isValidLeaderboardPayload(data)) {
            throw new Error('Resposta do leaderboard fora do contrato');
        }
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
        });
        if (data.leaderboard.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'loading-state';
            emptyState.textContent = 'Nenhuma pontuação registrada.';
            listEl.appendChild(emptyState);
        }
    } catch (error) {
        console.error("Erro ao buscar o leaderboard.", error);
    }
}

/**
 * Envia a maior pontuação local para a API do leaderboard.
 */
async function submitScore() {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: minerName, score: balanceSatoshis })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        fetchLeaderboard();
    } catch(error) {
        console.error("Erro ao enviar a pontuação.", error);
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
        const nextPrice = hardwarePrices[hardwareLevel];
        hwTitle.innerText = `Upgrade: ${hardwareNames[hardwareLevel]}`;
        hwBtn.innerText = `${nextPrice.toLocaleString()} SATS`;
        hwBtn.disabled = balanceSatoshis < nextPrice;
    }
    
    const lnBtn = document.getElementById('btn-buy-lightning');
    if(isLightningMode) {
        lnBtn.innerText = "NODE ACTIVE"; lnBtn.disabled = true;
    } else {
        lnBtn.disabled = balanceSatoshis < LIGHTNING_PRICE || isPlaying;
    }
}

/**
 * Compra e aplica uma dica à primeira palavra ainda não encontrada.
 */
function buyHint() {
    if (balanceSatoshis >= HINT_PRICE && isPlaying) {
        const unfound = blockWords.find(w => !w.found && !w.hinted);
        if (unfound) {
            balanceSatoshis -= HINT_PRICE; document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString(); playSound('buy');
            unfound.hinted = true;
            grid[unfound.startY][unfound.startX].element.classList.add('hint-glow');
            updateStoreUI(); submitScore();
        }
    }
}

/**
 * Compra o próximo nível de hardware e amplia o tempo de rodada.
 */
function buyHardware() {
    if (hardwareLevel < hardwareNames.length) {
        const nextPrice = hardwarePrices[hardwareLevel];
        if (balanceSatoshis < nextPrice) return;
        balanceSatoshis -= nextPrice; document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString(); playSound('buy');
        networkTimeBonus += 10;
        if(isPlaying && !isLightningMode) networkTimeLimit += 10;
        document.getElementById('ui-hardware').innerText = hardwareNames[hardwareLevel];
        hardwareLevel++; updateStoreUI(); submitScore();
    }
}

/**
 * Ativa o upgrade Lightning simulado depois de debitar o saldo fictício.
 */
function buyLightning() {
    if (balanceSatoshis >= LIGHTNING_PRICE && !isLightningMode && !isPlaying && !isTransitioning) {
        isTransitioning = true;
        isLightningMode = true;
        balanceSatoshis -= LIGHTNING_PRICE; document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString(); playSound('buy');
        document.body.classList.add('lightning-theme');
        document.getElementById('result-title').style.color = "var(--lightning-blue)";
        updateStoreUI(); submitScore();
        
        const term = document.getElementById('lightning-modal');
        const termText = document.getElementById('lightning-text');
        setModalState(term, true);
        termText.textContent = "> INIT LIGHTNING_DAEMON\n";
        
        setTimeout(() => { termText.textContent += "> FINDING PEERS... [OK]\n"; }, 800);
        setTimeout(() => { termText.textContent += "> OPENING CHANNEL (SIMULADO)... [OK]\n"; }, 1600);
        setTimeout(() => {
            termText.textContent += "> ZERO-CONF SIMULADO. LIGHTNING MODE ACTIVE.\n";
            setTimeout(() => {
                setModalState(term, false);
                isTransitioning = false;
                if (!isPlaying && txBuffer.length === WORDS_PER_BLOCK) {
                    buildPlayableBlock();
                }
            }, 1500);
        }, 2500);
    }
}

/**
 * Limpa a rodada anterior e volta ao estado de coleta de transações.
 */
function prepareNextBlock() {
    clearInterval(networkInterval);
    setModalState(document.getElementById('result-modal'), false);
    selectedCells.forEach(({ cell }) => cell.classList.remove('selected'));
    selectedCells = [];
    isSelecting = false;
    isPlaying = false; txBuffer = []; wordsFoundInBlock = 0; networkTimePassed = 0; netProgressEl.style.width = '0%';
    netProgressEl.setAttribute('aria-valuenow', '0');
    bankEl.innerHTML = `<div class="loading-state" id="tx-loading">Aguardando transações (0/6)...</div>`;
    overlayEl.classList.remove('hidden'); updateStoreUI();
}

/**
 * Define a dificuldade, constrói a grade e inicia a corrida contra a rede.
 */
function buildPlayableBlock(buildAttempt = 0) {
    if (
        isTransitioning
        || !ws
        || ws.readyState !== WebSocket.OPEN
        || txBuffer.length !== WORDS_PER_BLOCK
    ) return;
    overlayEl.classList.add('hidden');
    gridEl.innerHTML = ''; svgEl.innerHTML = ''; bankEl.innerHTML = '';
    grid = []; blockWords = []; isPlaying = true;
    
    // Análise Dinâmica de Tamanho (vsize)
    const maxVsize = Math.max(...txBuffer.map(t => t.vsize));
    
    if (isLightningMode) {
        currentGridSize = 8; // Condensado
        networkTimeLimit = 20; // Ultra rápido
    } else if (maxVsize > 1000) {
        currentGridSize = 15; // Bloco pesado
        networkTimeLimit = 75 + networkTimeBonus;
    } else {
        currentGridSize = 12; // Padrão
        networkTimeLimit = 60 + networkTimeBonus;
    }
    
    configureGridSize(currentGridSize);
    
    document.getElementById('ui-block').innerText = `#${roundNumber.toLocaleString()}`;

    for (let y = 0; y < currentGridSize; y++) {
        let row = [];
        for (let x = 0; x < currentGridSize; x++) {
            const cell = document.createElement('div'); cell.className = 'cell'; cell.dataset.x = x; cell.dataset.y = y;
            cell.setAttribute('role', 'gridcell');
            cell.addEventListener('mousedown', (e) => { e.preventDefault(); startSelection(cell, x, y); });
            cell.addEventListener('mouseenter', () => continueSelection(cell, x, y));
            gridEl.appendChild(cell); row.push({ element: cell, char: '', isFound: false });
        }
        grid.push(row);
    }

    const allWordsPlaced = txBuffer.every(
        tx => injectWordInGrid(tx.word, tx.isHighFee, tx.isGolden)
    );
    if (!allWordsPlaced) {
        if (buildAttempt < 4) {
            buildPlayableBlock(buildAttempt + 1);
            return;
        }
        isPlaying = false;
        overlayEl.classList.remove('hidden');
        const loaderText = overlayEl.querySelector('.loader-text');
        if (loaderText) loaderText.innerText = "Falha ao montar a grade. Aguarde o próximo conjunto.";
        return;
    }

    for (let y = 0; y < currentGridSize; y++) {
        for (let x = 0; x < currentGridSize; x++) {
            if (grid[y][x].char === '') { grid[y][x].char = String.fromCharCode(65 + Math.floor(Math.random() * 26)); }
            grid[y][x].element.innerText = grid[y][x].char;
            grid[y][x].element.setAttribute('aria-label', `Letra ${grid[y][x].char}`);
        }
    }

    updateStoreUI();
    startNetworkRace();
}

/**
 * Posiciona uma palavra sem sobreposição e registra seu item na lista lateral.
 */
function injectWordInGrid(word, isHighFee, isGolden) {
    if (word.length > currentGridSize) word = word.substring(0, currentGridSize);
    
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
                for (let i = 0; i < word.length; i++) {
                    const cx = startX + dir[0] * i; const cy = startY + dir[1] * i;
                    grid[cy][cx].char = word[i];
                }
                blockWords.push({ word, found: false, isHighFee, isGolden, startX, startY, hinted: false });
                
                renderBankWord(word, isHighFee, isGolden);
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
                blockWords.push({ word, found: false, isHighFee, isGolden, startX: x, startY: y, hinted: false });
                renderBankWord(word, isHighFee, isGolden);
                return true;
            }
        }
    }

    console.error(`Não foi possível inserir a palavra ${word} na grade.`);
    return false;
}

/**
 * Cria o item de uma palavra usando somente APIs seguras do DOM.
 */
function renderBankWord(word, isHighFee, isGolden) {
    const item = document.createElement('div');
    const wordText = document.createElement('span');
    const tag = document.createElement('span');
    item.className = 'word-item';
    item.id = `bank-${word}`;
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
 * Inicia uma seleção a partir do primeiro toque.
 */
function handleTouchStart(e) {
    e.preventDefault(); const touch = e.touches[0]; const target = document.elementFromPoint(touch.clientX, touch.clientY);
    if (target && target.classList.contains('cell')) { startSelection(target, parseInt(target.dataset.x), parseInt(target.dataset.y)); }
}
/**
 * Continua a seleção acompanhando o dedo do jogador.
 */
function handleTouchMove(e) {
    e.preventDefault(); if (!isSelecting) return;
    const touch = e.touches[0]; const target = document.elementFromPoint(touch.clientX, touch.clientY);
    if (target && target.classList.contains('cell')) { continueSelection(target, parseInt(target.dataset.x), parseInt(target.dataset.y)); }
}
/**
 * Registra a primeira célula de uma tentativa.
 */
function startSelection(cell, x, y) {
    if(!isPlaying || cell.classList.contains('found')) return;
    isSelecting = true; selectedCells = [{ cell, x, y }]; cell.classList.add('selected'); playSound('tick');
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
        selectedCells.push({ cell, x, y }); cell.classList.add('selected'); playSound('tick');
    }
}

document.addEventListener('mouseup', endSelection);
document.addEventListener('touchend', endSelection);

/**
 * Valida a palavra selecionada, calcula a recompensa e encerra a tentativa.
 */
function endSelection() {
    if (!isSelecting) return;
    isSelecting = false;
    
    const selectedWord = selectedCells.map(c => grid[c.y][c.x].char).join('');
    const reversedWord = selectedWord.split('').reverse().join('');
    const match = blockWords.find(w => (w.word === selectedWord || w.word === reversedWord) && !w.found);
    
    if (match) {
        playSound('success'); match.found = true; wordsFoundInBlock++;
        
        const now = Date.now();
        if (lastFoundTime !== 0 && now - lastFoundTime < 8000) { comboMultiplier = Math.min(comboMultiplier + 0.5, 4.0); } 
        else { comboMultiplier = 1.0; }
        lastFoundTime = now;
        document.getElementById('ui-combo').innerText = `${comboMultiplier.toFixed(1)}×`;
        
        let points = (baseReward + (match.word.length * 50)) * comboMultiplier;
        if (match.isGolden) points *= 5; else if (match.isHighFee) points *= 3;
        if (isLightningMode) points *= 10;
        
        balanceSatoshis += Math.floor(points);
        document.getElementById('ui-balance').innerText = balanceSatoshis.toLocaleString();

        showFloatingText(selectedCells[0].cell, points, match.isHighFee, match.isGolden);
        drawAnimatedLine(selectedCells[0].cell, selectedCells[selectedCells.length - 1].cell);
        
        selectedCells.forEach(c => { c.cell.classList.remove('selected'); c.cell.classList.add('found'); c.cell.classList.remove('hint-glow'); });
        document.getElementById(`bank-${match.word}`)?.classList.add('found');
        updateStoreUI(); submitScore();

        if (wordsFoundInBlock === blockWords.length) {
            clearInterval(networkInterval);
            isPlaying = false;
            setTimeout(() => showResult(
                true,
                isLightningMode
                    ? "Rodada L2 simulada concluída."
                    : "Todas as palavras foram encontradas antes do cronômetro."
            ), 600);
        }
    } else {
        selectedCells.forEach(c => c.cell.classList.remove('selected'));
        comboMultiplier = 1.0; document.getElementById('ui-combo').innerText = `1.0×`;
    }
    selectedCells = [];
}

/**
 * Exibe uma etiqueta temporária com a recompensa obtida.
 */
function showFloatingText(cell, points, isHighFee, isGolden) {
    const floatText = document.createElement('div'); floatText.className = 'floating-text'; floatText.innerText = `+${Math.floor(points)} Sats`;
    if (isGolden) { floatText.innerText += " (GOLDEN)"; floatText.style.color = 'var(--golden-hash)'; }
    else if (isLightningMode) { floatText.innerText += " (L2 BOLT)"; floatText.style.color = 'var(--lightning-blue)'; }
    else if (isHighFee) { floatText.innerText += " (HIGH FEE)"; floatText.style.color = 'var(--high-fee)'; }
    else { floatText.style.color = 'var(--success-green)'; }
    
    const rect = cell.getBoundingClientRect(); floatText.style.left = `${rect.left}px`; floatText.style.top = `${rect.top}px`;
    document.body.appendChild(floatText); setTimeout(() => floatText.remove(), 1200);
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
 * Inicia o cronômetro visual da corrida contra a rede.
 */
function startNetworkRace() {
    clearInterval(networkInterval);
    networkInterval = setInterval(() => {
        networkTimePassed++;
        const percent = (networkTimePassed / networkTimeLimit) * 100;
        netProgressEl.style.width = `${percent}%`;
        netProgressEl.setAttribute('aria-valuenow', String(Math.min(100, Math.round(percent))));

        if (networkTimePassed >= networkTimeLimit) {
            clearInterval(networkInterval); isPlaying = false; playSound('orphan'); submitScore();
            showResult(false, "O cronômetro da rodada expirou.");
        }
    }, 1000);
}

/**
 * Apresenta o resultado final da rodada e prepara a próxima ação.
 */
function showResult(success, message) {
    const modal = document.getElementById('result-modal'); const title = document.getElementById('result-title');
    const text = document.getElementById('result-text'); const btn = document.getElementById('next-btn');
    
    updateStoreUI();
    setModalState(modal, true);
    if (success) {
        title.innerText = "Desafio concluído!"; title.style.color = isLightningMode ? "var(--lightning-blue)" : "var(--success-green)";
        text.innerText = message; btn.innerText = "Próxima rodada";
        roundNumber++;
    } else {
        title.innerText = "Rodada encerrada"; title.style.color = "var(--error-red)";
        text.innerText = message; btn.innerText = "Tentar nova rodada";
        comboMultiplier = 1.0; document.getElementById('ui-combo').innerText = `1.0×`;
    }
}
