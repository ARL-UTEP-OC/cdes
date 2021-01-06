#!/bin/sh
# session hook script; write commands here to execute on the host at the
# specified state

#Create a blank file/clear existing
echo "" > /tmp/suricata-out/fast.log

#Depending on OS, use the default yaml, since it needs to be specified when running suricata
if [ -f /etc/suricata/suricata-debian.yaml ]
then
  SURICATA_YAML=/etc/suricata/suricata-debian.yaml
else
  SURICATA_YAML=/etc/suricata/suricata.yaml
fi

## The following will list core node interfaces (as seen from the host) for node 13 (0x0d in hex)
INTERFACES=`find /sys/class/net/ -mindepth 1 -maxdepth 1 -name 'vethd.*' -printf '-i %f '`

#for debugging purposes, write the executed command to a temporary file
echo suricata -c $SURICATA_YAML -l /tmp/suricata-out/ -S /tmp/suricata-out/rules/custom.rules $INTERFACES --pidfile /tmp/suricata.pid -D > /tmp/suricommand.txt

#run suricata
suricata -c $SURICATA_YAML -l /tmp/suricata-out/ -S /tmp/suricata-out/rules/custom.rules $INTERFACES --pidfile /tmp/suricata.pid -D

