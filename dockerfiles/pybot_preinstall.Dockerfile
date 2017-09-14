FROM python:3.6
MAINTAINER Aleksei Kioller <avkioller@gmail.com>
ENV PYTHONUNBUFFERED 0
RUN apt-get update
RUN apt-get install -y tzdata
RUN cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime
COPY ./requirements /pybot/requirements
COPY ./tokens.py /pybot/tokens.py
WORKDIR /pybot
RUN pip3.6 install -r requirements
