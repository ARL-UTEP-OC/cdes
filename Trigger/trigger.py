import multiprocessing
from multiprocessing import TimeoutError
from Queue import Empty
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
        self.cc_gw_numbers = []
        self.cc_node_numbers = []
    
        for node in self.conditional_conns[self.cc_dec]["connected_nodes"]:
            if node["role"] == "cc_node":
                logging.debug("Trigger(): set_active_conn(): found cc_node: " + str(node))
                self.cc_node_numbers.append(node["number"])
            elif node["role"] == "cc_gw":
                logging.debug("Trigger(): set_active_conn(): found cc_gw: " + str(node))
                self.cc_gw_numbers.append(node["number"])

    def read_input_line(self):
        logging.debug("Trigger(): read_input_line(): instantiated")
        try:                
            data = self.iqueue.get(timeout=1)
            return data
        except TimeoutError:
            logging.debug("Trigger(): process_data(): Timed out")
            return None
        except Empty:
            logging.debug("Trigger(): process_data(): Timed out")
            return None

    #abstractmethod
    def process_data(self):
        raise NotImplementedError()
        # while True:
        #     data = self.read_input_line()
        #     if data != None:
        #         logging.info("Data: " + data)
        #     else:
        #         logging.info("Nothing read")
    
    def set_active_conn(self, active_cc_node_number):
        logging.debug("Trigger(): set_active_conn(): instantiated")

        #find the node to activate
        if active_cc_node_number in self.cc_node_numbers:
            logging.debug("Trigger(): set_active_conn(): found node to activate")
            self.oqueue.put([self.cc_dec, self.cc_gw_numbers, active_cc_node_number])
        else:
            logging.error("Invalid Node Specified for Activation")
            raise NameError()

    def get_cc_node_numbers(self):
         logging.debug("Trigger(): get_cc_node_names(): instantiated")
         return self.cc_node_numbers

    def get_cc_gw_numbers(self):
         logging.debug("Trigger(): get_cc_gw_name(): instantiated")
         return self.cc_gw_numbers

    def get_cc_decision_number(self):
         logging.debug("Trigger(): get_cc_decision_name(): instantiated")
         return self.cc_dec

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")
    
    if len(sys.argv) < 2:
        logging.error("Usage: python controller.py <session-number>")
        exit()       

    #conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }
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
    
    logging.debug("Controller(): Completed")