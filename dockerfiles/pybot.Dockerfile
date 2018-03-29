FROM python:3.6-alpine
LABEL maintainer="Aleksei Kioller <avkioller@gmail.com>"
ENV PYTHONUNBUFFERED 0
RUN apk add --update --no-cache tzdata \
 && cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime
COPY ./requirements /bot/requirements
WORKDIR /bot
RUN pip install -r requirements
COPY ./bot /bot
ENTRYPOINT [ "python", "main.py" ]
