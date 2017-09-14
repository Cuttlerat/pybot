FROM pybot_preinstall
COPY ./pybot.py /pybot/pybot.py
ENTRYPOINT [ "python3.6", "pybot.py" ]
