FROM python:3.6
LABEL maintainer="Aleksei Kioller <avkioller@gmail.com>"
ENV PYTHONUNBUFFERED 0
RUN apt-get update\
 && apt-get install -y tzdata\
 && cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime\
 && apt-get clean\
 && rm -rf /var/lib/apt/lists/*
COPY ./requirements /pybot/requirements
WORKDIR /pybot
RUN pip3.6 install -r requirements
