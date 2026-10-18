FROM nginx:1.29-alpine

# O contexto de build é a raiz do repositório: os assets do jogo estão em
# frontend/ e a documentação integrada em /docs/ está em docs/.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/index.html frontend/pixel.css frontend/game.js frontend/manifest.webmanifest frontend/service-worker.js /usr/share/nginx/html/
COPY frontend/icons/ /usr/share/nginx/html/icons/
COPY frontend/fonts/ /usr/share/nginx/html/fonts/

# Landing page da apresentação e capturas reais do fluxo do jogo.
COPY land_page.html /usr/share/nginx/html/land_page.html
COPY assets/guide/ /usr/share/nginx/html/assets/guide/

# Documentação técnica e apresentação, servida em /docs/ pelo mesmo nginx.
COPY docs/index.html /usr/share/nginx/html/docs/
COPY docs/api.html /usr/share/nginx/html/docs/api/index.html
COPY docs/guia-apresentacao.html /usr/share/nginx/html/docs/apresentacao/index.html
COPY docs/wiki.css /usr/share/nginx/html/docs/wiki.css
COPY docs/wiki.js /usr/share/nginx/html/docs/wiki.js
COPY docs/assets/ /usr/share/nginx/html/docs/assets/

EXPOSE 80
