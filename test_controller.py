import multiprocessing
from Trigger.timer_trigger import TimerTrigger
from Swapper.swapper import Swapper
from Monitor.monitor import Monitor
from COREIfx.session_reader import SessionReader
import imp
import logging
import time
import sys
import os
import json
from Controller import Controller

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Program instantiated")
    cr = Controller()

    if len(sys.argv) == 2:
        dirs = cr.get_sorted_in_dirs("/tmp/", dircontains="pycore")
        if len(dirs) == 0:
            logging.error("No sessions exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()
        mydir = dirs[0]
        session_number = mydir.split("pycore.")[1]
        logging.warning("Session Number was not passed in; will use latest: " + session_number)

    elif len(sys.argv) == 3:
        session_number = sys.argv[2]
        mydir = os.path.join("/tmp","pycore."+str(sys.argv[2]))
        if os.path.exists(mydir) == False:
            logging.error("Session "+str(sys.argv[2])+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()

    else:
        logging.error("Usage: python controller.py <monitor_process_path> [session-number]")
        exit()

    cr.cdes_run(monitor_cmd=sys.argv[1], session_number=session_number)
    
    # Get output and print to screen
    while True:
        #logging.debug("Processing...)
        time.sleep(0.1)
    
    logging.debug("Controller(): Completed")
