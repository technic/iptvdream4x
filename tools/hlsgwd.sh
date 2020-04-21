#!/bin/sh
#
# Simple script to daemonize hlsgw.py
#

NAME=hlsgw.py
DAEMON=/usr/bin/$NAME

test -x "$DAEMON" || exit 1

case "$1" in
  # busybox realization of start-stop-daemon requires -x argument
  # otherwise it does not detect already running process
  start)
    start-stop-daemon -S -q -n "$NAME" -x /usr/bin/python -a "$DAEMON" -b
    retval=$?
    if test $retval -eq 0; then
        echo "started $NAME"
    fi
    exit $retval
    ;;
  stop)
    start-stop-daemon -K -n "$NAME" -x /usr/bin/python
    ;;
  restart)
    $0 stop && $0 start
    ;;
  *)
    echo "Usage: $0 {start|stop|restart}" >&2
    exit 1
    ;;
esac

exit 0
