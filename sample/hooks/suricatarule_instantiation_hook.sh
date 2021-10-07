#!/bin/sh
# session hook script; write commands here to execute on the host at the
# specified state

#Create directories to hold suricata data
mkdir /tmp/suricata-out/
mkdir /tmp/suricata-out/rules

#Create suricata rules -- note that if too long, this will get truncated when using .imn files
cat << EOF > /tmp/suricata-out/rules/custom.rules

alert icmp 10.0.0.10 any -> any any (msg:"ICMP packet from X3"; sid:1100003; rev:1;)
alert icmp 10.0.0.11 any -> any any (msg:"ICMP packet from X2"; sid:1100002; rev:1;)
alert icmp 10.0.1.10 any -> any any (msg:"ICMP packet from X1"; sid:1100001; rev:1;)
EOF

