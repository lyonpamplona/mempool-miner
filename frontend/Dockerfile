FROM nginx:1.28-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/index.html frontend/style.css frontend/game.js /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
COPY guia-apresentacao.html /usr/share/nginx/html/apresentacao.html

EXPOSE 80
