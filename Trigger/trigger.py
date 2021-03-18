import multiprocessing
from multiprocessing import TimeoutError
import queue
import logging
import subprocess
import shlex
import threading
import time
import sys
from COREIfx.session_reader import SessionReader

class Trigger():
    
    def __init__(self, name, iqueue, oqueue, conditional_conns, cc_dec_number):
        logging.debug("Trigger(): instantiated")
        self.name = name
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.conditional_conns = {}
        #The following will be auto-filled in the future
        self.conditional_conns = conditional_conns
        #works for the specific cc_dec
        self.cc_dec = cc_dec_number
        self.cc_dec_name = self.conditional_conns[cc_dec_number]["name"]
        self.cc_node_numbers = []
        self.cc_dec_node_ifxs = []
    
        for node in self.conditional_conns[self.cc_dec]["connected_nodes"]:
            logging.debug("Trigger(): init(): found interface to connected node: " + str(node))
            self.cc_dec_node_ifxs.append(node["cc_dec_nic"])
            if node["role"] == "cc_node":
                logging.debug("Trigger(): init(): found cc_node: " + str(node))
                self.cc_node_numbers.append(node["number"])

    def read_input_line(self):
        logging.debug("Trigger(): read_input_line(): instantiated")
        try:                
            data = self.iqueue.get(timeout=1)
            #logging.error("T got iqueue: " + str(time.time()))
            return data
        except TimeoutError:
            logging.debug("Trigger(): process_data(): Timed out")
            return None
        except queue.Empty:
            logging.debug("Trigger(): process_data(): Timed out")
            return None

    #abstractmethod
    def process_data(self):
        raise NotImplementedError()
    
    def set_active_conn(self, active_cc_dec_nic, disable_others=True):
        logging.debug("Trigger(): set_active_conn(): instantiated")
#######TODO: need to disable_others and ensure the new queue is picked up properly###
        #check that the nic exists
        if active_cc_dec_nic in self.cc_dec_node_ifxs:
            logging.debug("Trigger(): set_active_conn(): found node to activate")
            self.oqueue.put([1, self.cc_dec, active_cc_dec_nic, disable_others])
        else:
            logging.error("Invalid DEC Interface Specified for Activation")
            raise NameError()

    def set_decnode_conns(self, active=[], deactive=[]):
        logging.debug("Trigger(): set_decnode_conns(): instantiated")
    
        #check that the nic exists
        for nic in active:
            if nic not in self.cc_dec_node_ifxs:
                logging.error("Invalid DEC Interface Specified for Activation: " + str(nic))
                raise NameError()
        for nic in deactive:
            if nic not in self.cc_dec_node_ifxs:
                logging.error("Invalid DEC Interface Specified for De-Activation: " + str(nic))
                raise NameError()
        self.oqueue.put([2, self.cc_dec, active, deactive])
        
    def get_cc_node_numbers(self):
         logging.debug("Trigger(): get_cc_node_names(): instantiated")
         return self.cc_node_numbers

    def get_cc_dec_node_ifxs(self):
         logging.debug("Trigger(): get_cc_node_names(): instantiated")
         return self.cc_dec_node_ifxs

    def get_cc_decision_number(self):
         logging.debug("Trigger(): get_cc_decision_name(): instantiated")
         return self.cc_dec

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Trigger(): Main(): instantiated")
    
    if len(sys.argv) < 2:
        logging.error("Usage: python controller.py <session-number>")
        exit()       

    sr = SessionReader(sys.argv[1])
    conditional_conns = sr.relevant_session_to_JSON()
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    omqueue.put("1\n")
    omqueue.put("2\n")
    omqueue.put("3\n")
    omqueue.put("4\n")
    omqueue.put("5\n")

    tp = Trigger("trigger", omqueue, otqueue, conditional_conns)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()
    
    # Get output and print to screen
    while True:
        logging.debug("OT Queue: " + otqueue.get())
    
    logging.debug("Trigger(): Completed")
