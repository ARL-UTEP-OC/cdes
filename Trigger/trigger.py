import multiprocessing
from multiprocessing import TimeoutError
from Queue import Empty
import logging
import subprocess
import shlex
import threading
import time

class Trigger():
    
    def __init__(self, name, iqueue, oqueue, conditional_conns):
        logging.debug("Trigger(): instantiated")
        self.name = name
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.conditional_conns = {}
        #The following will be auto-filled in the future
        self.conditional_conns = conditional_conns
        self.cc_dec = self.conditional_conns.keys()[0]
    
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
    
    def set_active_conn(self, active_cc_node_name):
        logging.debug("Trigger(): set_active_conn(): instantiated")
        if active_cc_node_name in self.conditional_conns[self.cc_dec]["cc_nodes"]:
            logging.debug("Trigger(): set_active_conn(): setting active node: " + active_cc_node_name)
            #self.conditional_conns[self.cc_dec]["cc_nodes"][active_cc_node_name] = True
            self.oqueue.put([self.cc_dec, self.conditional_conns[self.cc_dec]["cc_gw"], active_cc_node_name])
        else:
            logging.error("Invalid Node Specified for Activation")
            raise NameError()
    
    def get_cc_node_names(self):
        logging.debug("Trigger(): get_cc_node_names(): instantiated")
        return self.conditional_conns[self.cc_dec]["cc_nodes"].keys()

    def get_cc_gw_name(self):
        logging.debug("Trigger(): get_cc_gw_name(): instantiated")
        return self.conditional_conns[self.cc_dec]["cc_gw"]

    def get_cc_decision_name(self):
        logging.debug("Trigger(): get_cc_decision_name(): instantiated")
        return self.conditional_conns.keys()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")
    
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    omqueue.put("1\n")
    omqueue.put("2\n")
    omqueue.put("3\n")
    omqueue.put("4\n")
    omqueue.put("5\n")

    conditional_conns = {"n4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }

    tp = Trigger("trigger", omqueue, otqueue, conditional_conns)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()
    
    # Get output and print to screen
    while True:
        logging.debug("OT Queue: " + otqueue.get())
    
    logging.debug("Controller(): Completed")