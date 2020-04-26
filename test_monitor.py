#!/usr/bin/python3

import multiprocessing
import shlex
import subprocess
import logging
import sys, traceback
import psutil
import os, signal 
import select

from Monitor.monitor import Monitor

__author__ = "Jaime C. Acosta"
__license__ = "GPL 3.0"

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")
    imqueue = multiprocessing.Queue()
    omqueue = multiprocessing.Queue()
    cmd = "sample/code-resources/time_cont.sh"
    m = Monitor("monitor", imqueue, omqueue, cmd)
    mp = multiprocessing.Process(target=m.run_monitor)
    mp.start()
    
    # Get output and print to screen
    while True:
        logging.debug("OM Queue: " + omqueue.get())
    
    logging.debug("Monitor(): Completed")