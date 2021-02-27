#!/usr/bin/env python
import subprocess
import time
import shlex

cmd =  "sshpass -p 'passgoeshere' ssh user@ipgoeshere \"\\\"c:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe\\\"\" startvm 10.0.1.10_honey1"
print("starting: " + str(cmd))
p = subprocess.Popen(shlex.split(cmd))
p.wait()
print("done")

print("sleeping 5 seconds")
time.sleep(5)
cmd =  "sshpass -p 'passgoeshere' ssh user@ipgoeshere \"\\\"c:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe\\\"\" controlvm 10.0.1.10_honey1 savestate"
print("starting: " + str(cmd))
p = subprocess.Popen(shlex.split(cmd))
p.wait()

print("done")

