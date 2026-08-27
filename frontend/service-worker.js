'use strict';

const CACHE_PREFIX = 'mempool-miner-shell-';
// IMPORTANTE: incrementar a cada deploy que altere pixel.css, game.js,
// index.html ou service-worker.js — senão o cache-first serve a versão
// antiga para quem já tem o shell PWA instalado (bug de layout 20/08/2026).
const CACHE_VERSION = 'v53';
const CACHE_NAME = `${CACHE_PREFIX}${CACHE_VERSION}`;
const SHELL_ASSETS = [
    './',
    './pixel.css',
    './game.js',
    './manifest.webmanifest',
    './fonts/jetbrains-mono-latin.woff2',
    './fonts/press-start-2p-latin.woff2',
    './fonts/vt323-latin.woff2',
    './icons/ui-sprite.svg',
    './icons/icon-192.svg',
    './icons/icon-512.svg'
];
const STATIC_URLS = new Set(
    SHELL_ASSETS.map(asset => new URL(asset, self.location.href).href)
);
const APP_ENTRY_PATHS = new Set([
    new URL('./', self.location.href).pathname,
    new URL('./index.html', self.location.href).pathname
]);

function isSensitiveRequest(url) {
    return (
        url.pathname === '/api'
        || url.pathname.startsWith('/api/')
        || url.pathname === '/ws'
        || url.pathname.startsWith('/ws/')
        || url.pathname === '/openapi.json'
        || url.pathname.startsWith('/backend-docs')
    );
}

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_ASSETS))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys
                    .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('message', event => {
    if (event.data?.type === 'SKIP_WAITING') {
        void self.skipWaiting();
    }
});

self.addEventListener('fetch', event => {
    const { request } = event;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);
    if (url.origin !== self.location.origin || isSensitiveRequest(url)) return;

    if (request.mode === 'navigate') {
        if (!APP_ENTRY_PATHS.has(url.pathname)) return;
        event.respondWith(
            fetch(request).catch(async () => {
                const cache = await caches.open(CACHE_NAME);
                return cache.match('./');
            })
        );
        return;
    }

    if (!STATIC_URLS.has(url.href)) return;
    event.respondWith(
        caches.open(CACHE_NAME).then(async cache => (
            (await cache.match(request)) || fetch(request)
        ))
    );
});
