FROM nginx:1.13-alpine

COPY conf.d /etc/nginx/conf.d

COPY htmlcov /coverage
