import multiprocessing
import logging
import subprocess
import shlex
import threading
import time
import sys
import os
from COREIfx.session_reader import SessionReader
from COREIfx import msg_ifx
from Swapper.swapper import Swapper

__author__ = "Jaime C. Acosta"
__license__ = "GPL 3.0"

def short_session_id(session_number):
    logging.debug("Controller(): short_session_id(): Instantiated")
    snum = int(session_number)
    ans = (snum >> 8) ^ (snum & ((1 << 8) - 1))
    return ("%x" % ans)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Swapper(): instantiated")
    #Assuming we're using CC_NodeTest.imn
    cc_dec_node = "13"

    if len(sys.argv) < 2:
        logging.error("Usage: python test_swapper.py <session-number>")
        exit()       

    #conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }
    sr = SessionReader(sys.argv[1])
    conditional_conns = sr.relevant_session_to_JSON()
    
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    sw = Swapper("swapper", omqueue, otqueue, conditional_conns, sys.argv[1], short_session_id(int(sys.argv[1])), cc_dec_node)
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    #[cc_dec, cc_gw, active_node_number, disable_others]
    # Get output and print to screen
    for i in range(60):
        omqueue.put([cc_dec_node, "2", "3", True])
        time.sleep(10)
        omqueue.put([cc_dec_node, "2", "6", True])
        time.sleep(10)
    logging.debug("Swapper(): Completed")
