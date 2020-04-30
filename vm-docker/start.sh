#!/bin/bash

case "$RESOLUTION" in
    1920x*)
        echo "config.skin.primary_skin=PLi-FullHD/skin.xml" >> /etc/enigma2/settings
        ;;
    *)
        echo "config.skin.primary_skin=PLi-HD/skin.xml" >> /etc/enigma2/settings
        ;;
esac

exec x11vnc -forever
