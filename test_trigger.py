import multiprocessing
from multiprocessing import TimeoutError
import logging
import subprocess
import shlex
import threading
import time
import sys
from COREIfx.session_reader import SessionReader
from Trigger.trigger import Trigger
from Trigger.timer_trigger import TimerTrigger

__author__ = "Jaime C. Acosta"
__license__ = "GPL 3.0"

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Trigger(): Main(): instantiated")
    
    if len(sys.argv) < 3:
        logging.error("Usage: python test_trigger.py <session-number> <cc-decision-node-number>")
        exit()       

    sr = SessionReader(sys.argv[1])
    cc_dec_node = sys.argv[2]
    conditional_conns = sr.relevant_session_to_JSON()
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    tp = TimerTrigger("trigger", omqueue, otqueue, conditional_conns, cc_dec_node)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()

    numItems = 1000
    for i in range(1,numItems):
        omqueue.put(str(i) + "\n")
        time.sleep(1)

    # Get output and print to screen
    while True:
        logging.debug("OT Queue: " + str(otqueue.get()))
    
    logging.debug("Trigger(): Completed")
