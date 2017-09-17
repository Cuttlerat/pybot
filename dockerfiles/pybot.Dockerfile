FROM pybot_preinstall
MAINTAINER Aleksei Kioller <avkioller@gmail.com>
COPY ./pybot.py /pybot/pybot.py
ENTRYPOINT [ "python3.6", "pybot.py" ]
