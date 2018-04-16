FROM nginx:1.13-alpine

COPY conf.d /etc/nginx/

COPY htmlcov /coverage
