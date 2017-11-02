#!/usr/bin/env bash

function _log_echo {

               date +"[%d/%b/%Y:%H:%M:%S %z]: $1" 1>&2

}    # ----------  end of function _log_echo  ----------

cd /pybot

while :; do

    _log_echo "Waiting for updates"
    inotifywait -e modify ./pybot.py &>/dev/null

    _log_echo "Building new pybot"
    docker-compose build pybot &>/dev/null       \
        || _log_echo "Error while building"

    _log_echo "Creating new container for pybot"
    docker-compose create pybot &>/dev/null      \
        || _log_echo "Error while creating"

    _log_echo "Restarting pybot"
    docker-compose restart pybot &>/dev/null     \
        && _log_echo "Restarted"                 \
        || _log_echo "Error while restarting"


done

