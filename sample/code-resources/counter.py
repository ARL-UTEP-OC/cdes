#!/usr/bin/env python
import sys
k = 0
try:
   for line in iter(sys.stdin.readline, b''):
      k = k + 1
      print(line)
except KeyboardInterrupt:
   sys.stdout.flush()
   pass
print(k)