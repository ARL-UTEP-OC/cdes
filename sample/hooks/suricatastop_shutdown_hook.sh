#!/bin/sh
# session hook script; write commands here to execute on the host at the
# specified state

kill `cat /tmp/suricata.pid`

