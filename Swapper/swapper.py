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
    
    def __init__(self, name, iqueue, oqueue, conditional_conns, session_number, short_session_number, cc_dec_number):
        logging.debug("Swapper(): instantiated")
        self.name = name
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.conditional_conns = {}
        #The following will be auto-filled in the future
        self.conditional_conns = conditional_conns
        self.conditional_conns_cc_dec = {}
        
        self.session_number = session_number
        self.short_session_number = short_session_number

        cc_node_numbers = []
        cc_gw_numbers = []


        self.conditional_conns_cc_dec[cc_dec_number] = {}
        for node in self.conditional_conns[cc_dec_number]["connected_nodes"]:
            if node["role"] == "cc_node":
                logging.debug("Swapper(): set_active_conn(): found cc_node: " + str(node))
                cc_node_numbers.append(node)
            elif node["role"] == "cc_gw":
                logging.debug("Swapper(): set_active_conn(): found cc_gw: " + str(node))
                cc_gw_numbers.append(node)
        self.conditional_conns_cc_dec[cc_dec_number]["cc_node_numbers"] = cc_node_numbers
        self.conditional_conns_cc_dec[cc_dec_number]["cc_gw_numbers"] = cc_gw_numbers

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
            logging.error("Swapper(): update_connection(): looking at nodes: " + str(self.conditional_conns_cc_dec[cc_dec]))
            for node in self.conditional_conns_cc_dec[cc_dec]["cc_node_numbers"]:
                if node["number"] == active_node_number:
                    if node["node_type"] == "SWITCH":
                        self.enable_net_node(self.short_session_number, cc_dec, node)
                    else:
                        self.enable_other_node(self.session_number, cc_dec, node)
                else:
                    if node["node_type"] == "SWITCH":
                        self.disable_net_node(self.short_session_number, cc_dec, node)
                    else:
                        self.disable_other_node(self.session_number, cc_dec, node)

    def enable_other_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): enable_other_node(): instantiated")
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="ifconfig '+cc_node["cc_nic"]+' up"')
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="sh defaultroute.sh"')
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue"')
        cc_node["connected"] = True

    def disable_other_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): disable_other_node(): instantiated")
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="ifconfig '+cc_node["cc_nic"]+' down"')
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=yellow"')
        cc_node["connected"] = False

    def enable_net_node(self, short_session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): enable_net_node(): instantiated")
        #system call to enable the interface (since CORE doesn't properly remove/stop the interfaces... yet?)
        suffix = "%x.%x.%s" % (int(cc_node["number"]), int(cc_dec_number), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' up'
        p = subprocess.Popen(shlex.split(cmd))

        suffix = "%x.%x.%s" % (int(cc_dec_number), int(cc_node["number"]), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' up'
        p = subprocess.Popen(shlex.split(cmd))

        msg_ifx.send_command('-s'+short_session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue"')
        cc_node["connected"] = True

    def disable_net_node(self, short_session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): disable_net_node(): instantiated")
        #system call to enable the interface (since CORE doesn't properly remove/stop the interfaces... yet?)
        suffix = "%x.%x.%s" % (int(cc_node["number"]), int(cc_dec_number), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' down'
        p = subprocess.Popen(shlex.split(cmd))

        suffix = "%x.%x.%s" % (int(cc_dec_number), int(cc_node["number"]), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' down'
        p = subprocess.Popen(shlex.split(cmd))

        msg_ifx.send_command('-s'+short_session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue"')
        cc_node["connected"] = False
            

def short_session_id(session_number):
        logging.debug("Swapper(): short_session_id(): Instantiated")
        snum = int(session_number)
        ans = (snum >> 8) ^ (snum & ((1 << 8) - 1))
        return ("%x" % ans)

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

    sw = Swapper("swapper", omqueue, otqueue, conditional_conns, sys.argv[1], short_session_id(int(sys.argv[1])), "3")
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    
    # Get output and print to screen
    for i in xrange(60):
        omqueue.put(["3", "1", "4"])
        time.sleep(10)
        omqueue.put(["3", "1", "5"])    
        time.sleep(10)
        omqueue.put(["3", "1", "13"])    
        time.sleep(10)
        omqueue.put(["3", "1", "14"])    
        time.sleep(10)
    logging.debug("Swapper(): Completed")