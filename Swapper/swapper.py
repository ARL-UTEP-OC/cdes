import multiprocessing
from multiprocessing import TimeoutError
from Queue import Empty
import logging
import subprocess
import shlex
import threading
import time

import os
from COREIfx import msg_ifx

class Swapper():
    
    def __init__(self, name, iqueue, oqueue, conditional_conns, session_number = None):
        logging.debug("Swapper(): instantiated")
        self.name = name
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.conditional_conns = {}
        #The following will be auto-filled in the future
        self.conditional_conns = conditional_conns
        self.cc_dec = self.conditional_conns.keys()[0]
        self.session_number = session_number
    
    def read_input(self):
        logging.debug("Swapper(): read_input(): instantiated")
        try:                
            data = self.iqueue.get(timeout=1)
            return data
        except TimeoutError:
            logging.debug("Swapper(): read_input(): Timed out")
            return None
        except Empty:
            logging.debug("Swapper(): read_input(): Timed out")
            return None

    #abstractmethod
    def update_connection(self):
        logging.debug("Swapper(): update_connection(): instantiated")
        while True:
            data = self.read_input()
            if data == None:
                logging.info("Nothing read")
                continue
            logging.debug("Data: " + str(data))
            #self.oqueue.put([self.cc_dec, self.conditional_conns[self.cc_dec]["cc_gw"], active_cc_node_name])
            [cc_dec, cc_gw, active_node_name] = data
            #self.conditional_conns[self.cc_dec]["cc_nodes"][active_cc_node_name] = True
            for node in self.conditional_conns[cc_dec]["cc_nodes"].keys():
                if node == active_node_name:
                    msg_ifx.send_command('-s'+self.session_number+' EXECUTE NODE='+node+' NUMBER=1000 COMMAND="ifconfig eth0 up"')
                    msg_ifx.send_command('-s'+self.session_number+' LINK N1_NUMBER='+cc_dec+' N2_NUMBER='+node+' GUI_ATTRIBUTES="color=blue"')
                    self.conditional_conns[self.cc_dec]["cc_nodes"][node] = True
                else:
                    msg_ifx.send_command('-s'+self.session_number+' EXECUTE NODE='+node+' NUMBER=1000 COMMAND="ifconfig eth0 down"')
                    msg_ifx.send_command('-s'+self.session_number+' LINK N1_NUMBER='+cc_dec+' N2_NUMBER='+node+' GUI_ATTRIBUTES="color=yellow"')
                    self.conditional_conns[self.cc_dec]["cc_nodes"][node] = False
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Swapper(): instantiated")
    
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }

    sw = Swapper("swapper", omqueue, otqueue, conditional_conns, "1")
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    
    # Get output and print to screen
    for i in xrange(60):
        omqueue.put(["4", "1", "2"])
        time.sleep(10)
        omqueue.put(["4", "1", "5"])    
        time.sleep(10)

    logging.debug("Swapper(): Completed")