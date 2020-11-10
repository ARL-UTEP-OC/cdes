#!/usr/bin/python3

import optparse
import os
import socket
import sys
import logging
import subprocess

import shlex

def send_command(cmd):
    logging.debug("msg_ifx(): get_node_file(): instantiated")
    cmd = "coresendmsg " + cmd
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, encoding="utf-8")
    p.wait()
    output = p.stdout.read()
    return output

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("msg_ifx(): instantiated")
    
    res = send_command(' '.join(sys.argv[1:]))
    logging.debug("msg_ifx() output: " + str(res))
