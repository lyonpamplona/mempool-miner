FROM nginx:1.28-alpine

# Fallback standalone (opcional): serve a documentação em /docs/, espelhando
# a integração no /8010. O contexto de build é a raiz do repositório.
COPY docs/nginx.conf /etc/nginx/conf.d/default.conf
COPY docs/index.html /usr/share/nginx/html/docs/
COPY docs/api.html /usr/share/nginx/html/docs/api/index.html
COPY docs/guia-apresentacao.html /usr/share/nginx/html/docs/apresentacao/index.html
COPY docs/wiki.css /usr/share/nginx/html/docs/wiki.css
COPY docs/wiki.js /usr/share/nginx/html/docs/wiki.js
COPY docs/assets/ /usr/share/nginx/html/docs/assets/

EXPOSE 80
