#!/bin/sh
# session hook script; write commands here to execute on the host at the
# specified state

echo "" > /tmp/suricata-out/fast.log

if [ -f /etc/suricata/suricata-debian.yaml ]
then
  SURICATA_YAML=/etc/suricata/suricata-debian.yaml
else
  SURICATA_YAML=/etc/suricata/suricata.yaml
fi

INTERFACES=`find /sys/class/net/ -mindepth 1 -maxdepth 1 -name 'b.*' -printf '-i %f '`

echo suricata -c $SURICATA_YAML -l /tmp/suricata-out/ -S /tmp/suricata-out/rules/custom.rules $INTERFACES --pidfile /tmp/suricata.pid -D > /tmp/suricommand.txt

suricata -c $SURICATA_YAML -l /tmp/suricata-out/ -S /tmp/suricata-out/rules/custom.rules $INTERFACES --pidfile /tmp/suricata.pid -D

