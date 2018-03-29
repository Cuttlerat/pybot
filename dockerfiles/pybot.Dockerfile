FROM python:3.6-alpine
LABEL maintainer="Aleksei Kioller <avkioller@gmail.com>"
ENV PYTHONUNBUFFERED 0
RUN apk add --update --no-cache tzdata \
 && cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime
COPY ./requirements /pybot/requirements
WORKDIR /pybot
RUN pip install -r requirements
COPY ./bot /pybot
ENTRYPOINT [ "python", "main.py" ]
