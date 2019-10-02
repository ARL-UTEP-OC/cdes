import multiprocessing
from multiprocessing import TimeoutError
from Queue import Empty
import logging
import subprocess
import shlex
import threading
import time
import sys
import os
from COREIfx.session_reader import SessionReader
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
        self.conditional_conns_cc_dec = {}
        
        self.session_number = session_number

        cc_node_numbers = []
        cc_gw_numbers = []

        for cc_dec in self.conditional_conns.keys():
            self.conditional_conns_cc_dec[cc_dec] = {}
            for node in self.conditional_conns[cc_dec]:
                if node["role"] == "cc_node":
                    logging.debug("Swapper(): set_active_conn(): found cc_node: " + str(node))
                    #self.conditional_conns[self.cc_dec]["cc_nodes"][active_cc_node_number] = True
                    #self.cc_node_numbers.append((node["cc_mac"], node["number"], node["cc_nic"], node["cc_ip4_mask"], node["cc_ip6_mask"], node["cc_ip4"], node["role"], node["cc_ip6"], node["connected"])
                    cc_node_numbers.append(node)
                elif node["role"] == "cc_gw":
                    logging.debug("Swapper(): set_active_conn(): found cc_gw: " + str(node))
                    #self.conditional_conns[self.cc_dec]["cc_nodes"][active_cc_node_number] = True
                    cc_gw_numbers.append(node)
            self.conditional_conns_cc_dec[cc_dec]["cc_node_numbers"] = cc_node_numbers
            self.conditional_conns_cc_dec[cc_dec]["cc_gw_numbers"] = cc_gw_numbers

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
            #get data from queue
            [cc_dec, cc_gw, active_node_number] = data
            for node in self.conditional_conns_cc_dec[cc_dec]["cc_node_numbers"]:
                if node["number"] == active_node_number:
                    msg_ifx.send_command('-s'+self.session_number+' EXECUTE NODE='+node["number"]+' NUMBER=1000 COMMAND="ifconfig '+node["cc_nic"]+' up"')
                    msg_ifx.send_command('-s'+self.session_number+' LINK N1_NUMBER='+cc_dec+' N2_NUMBER='+node["number"]+' GUI_ATTRIBUTES="color=blue"')
                    node["connected"] = True
                else:
                    msg_ifx.send_command('-s'+self.session_number+' EXECUTE NODE='+node["number"]+' NUMBER=1000 COMMAND="ifconfig '+node["cc_nic"]+' down"')
                    msg_ifx.send_command('-s'+self.session_number+' LINK N1_NUMBER='+cc_dec+' N2_NUMBER='+node["number"]+' GUI_ATTRIBUTES="color=yellow"')
                    node["connected"] = False
            
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Swapper(): instantiated")
    
    if len(sys.argv) < 2:
        logging.error("Usage: python controller.py <session-number>")
        exit()       

    #conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }
    sr = SessionReader(sys.argv[1])
    conditional_conns = sr.relevant_session_to_JSON()

    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    sw = Swapper("swapper", omqueue, otqueue, conditional_conns, sys.argv[1])
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    
    # Get output and print to screen
    for i in xrange(60):
        omqueue.put(["4", "1", "2"])
        time.sleep(10)
        omqueue.put(["4", "1", "5"])    
        time.sleep(10)

    logging.debug("Swapper(): Completed")