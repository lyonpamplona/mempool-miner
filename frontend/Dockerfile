FROM nginx:1.28-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html pixel.css game.js manifest.webmanifest service-worker.js /usr/share/nginx/html/
COPY icons/ /usr/share/nginx/html/icons/
COPY fonts/ /usr/share/nginx/html/fonts/

EXPOSE 80
