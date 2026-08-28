/* ============================================================
   MEMPOOL MINER // WIKI — interações (menu, busca, scrollspy)
   CSP-compatível: script externo (script-src 'self').
   ============================================================ */
(function () {
    'use strict';

    // ===== MENU LATERAL =====
    var btnMenu = document.getElementById('btn-menu');
    var sideMenu = document.getElementById('side-menu');
    var menuClose = document.getElementById('menu-close');

    function toggleMenu(open) {
        if (!sideMenu || !btnMenu) return;
        var isOpen = open !== undefined ? open : !sideMenu.classList.contains('open');
        sideMenu.classList.toggle('open', isOpen);
        document.body.classList.toggle('menu-open', isOpen);
        btnMenu.classList.toggle('active', isOpen);
        btnMenu.setAttribute('aria-expanded', String(isOpen));
    }
    if (btnMenu) btnMenu.addEventListener('click', function () { toggleMenu(); });
    if (menuClose) menuClose.addEventListener('click', function () { toggleMenu(false); });
    // Fecha o menu ao clicar em um link (mobile)
    if (sideMenu) {
        sideMenu.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () {
                if (window.innerWidth <= 900) toggleMenu(false);
            });
        });
    }
    // O índice é contextual e não deve cobrir o conteúdo ao abrir a página.
    // O usuário pode abri-lo pelo botão ÍNDICE em qualquer viewport.
    toggleMenu(false);

    // ===== SCROLL SPY (destaca a seção ativa no menu) =====
    if (sideMenu) {
        var menuLinks = Array.from(sideMenu.querySelectorAll('a[href^="#"]'));
        var sections = menuLinks.map(function (a) {
            return document.querySelector(a.getAttribute('href'));
        }).filter(Boolean);

        function updateScrollSpy() {
            var pos = window.scrollY + 100;
            var active = sections[0];
            for (var i = 0; i < sections.length; i++) {
                if (sections[i].offsetTop <= pos) active = sections[i];
            }
            menuLinks.forEach(function (a) {
                a.classList.toggle('active', a.getAttribute('href') === '#' + active.id);
            });
        }
        window.addEventListener('scroll', updateScrollSpy, { passive: true });
        updateScrollSpy();
    }

    // ===== BUSCA (filtra as seções visíveis) =====
    var searchInput = document.getElementById('wiki-search');
    var noResults = document.getElementById('no-results');
    var allBlocks = Array.from(document.querySelectorAll('.section-block'));
    var searchTimer = null;

    function doSearch() {
        if (!searchInput) return;
        var q = searchInput.value.trim().toLowerCase();
        if (!q) {
            allBlocks.forEach(function (b) { b.style.display = ''; });
            if (noResults) noResults.classList.remove('show');
            return;
        }
        var anyVisible = false;
        allBlocks.forEach(function (b) {
            var text = b.textContent.toLowerCase();
            var match = text.includes(q);
            b.style.display = match ? '' : 'none';
            if (match) anyVisible = true;
        });
        if (noResults) noResults.classList.toggle('show', !anyVisible);
    }
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(doSearch, 150);
        });
        // Atalho: "/" foca a busca; Esc limpa
        document.addEventListener('keydown', function (e) {
            if (e.key === '/' && document.activeElement !== searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
            if (e.key === 'Escape' && document.activeElement === searchInput) {
                searchInput.value = '';
                doSearch();
                searchInput.blur();
            }
        });
    }

    // ===== BACK TO TOP =====
    var backToTop = document.getElementById('back-to-top');
    if (backToTop) {
        window.addEventListener('scroll', function () {
            backToTop.classList.toggle('visible', window.scrollY > 400);
        }, { passive: true });
        backToTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
})();
