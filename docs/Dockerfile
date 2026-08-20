FROM nginx:1.28-alpine

COPY docs/nginx.conf /etc/nginx/conf.d/default.conf
COPY docs/index.html docs/site.css /usr/share/nginx/html/
COPY docs/api.html /usr/share/nginx/html/api/index.html
COPY docs/assets/ /usr/share/nginx/html/assets/
COPY guia-apresentacao.html /usr/share/nginx/html/apresentacao/index.html

EXPOSE 80
