import multiprocessing
from multiprocessing import TimeoutError
import queue
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
        except queue.Empty: 
            logging.debug("Swapper(): read_input(): Timed out")
            return None

    #abstractmethod
    def update_connection(self):
        logging.debug("Swapper(): update_connection(): instantiated")
        while True:
            data = self.read_input()
            if data == None:
                logging.debug("Swapper(): update_connection(): Nothing to read in queue, continuing")
                continue
            logging.debug("Swapper(): update_connection(): data pulled from queue: " + str(data))
            #get data from queue
            [cc_dec, cc_gw, active_node_number, disable_others] = data
            logging.debug("Swapper(): update_connection(): looking at nodes: " + str(self.conditional_conns_cc_dec[cc_dec]))
            for node in self.conditional_conns_cc_dec[cc_dec]["cc_node_numbers"]:
                if node["number"] == active_node_number:
                    if node["node_type"] == "SWITCH":
                        self.enable_net_node(self.short_session_number, cc_dec, node)
                    else:
                        self.enable_other_node(self.session_number, cc_dec, node)
                else:
                    if disable_others == True:
                        if node["node_type"] == "SWITCH":
                            self.disable_net_node(self.short_session_number, cc_dec, node)
                        else:
                            logging.error("Disabling other cc_dec: " + str(cc_dec) + " node: " + str(node))
                            self.disable_other_node(self.session_number, cc_dec, node)

    def enable_other_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): enable_other_node(): instantiated")
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="ifconfig '+cc_node["cc_nic"]+' up" --tcp')
        logging.error("enable other node cmd: " + '-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="ifconfig '+cc_node["cc_nic"]+' up" --tcp')
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="sh defaultroute.sh" --tcp')
###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###        
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue" --tcp')
        cc_node["connected"] = True

    def disable_other_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): disable_other_node(): instantiated")
        msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_node["number"]+' NUMBER=1000 COMMAND="ifconfig '+cc_node["cc_nic"]+' down" --tcp')
###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###        
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=yellow" --tcp')
        cc_node["connected"] = False

    def enable_net_node(self, short_session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): enable_net_node(): instantiated")
        #system call to enable the interface (since CORE doesn't properly remove/stop the interfaces... yet?)
        suffix = "%x.%x.%s" % (int(cc_node["number"]), int(cc_dec_number), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' up'
        p = subprocess.Popen(shlex.split(cmd), encoding="utf-8")

        suffix = "%x.%x.%s" % (int(cc_dec_number), int(cc_node["number"]), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' up'
        p = subprocess.Popen(shlex.split(cmd), encoding="utf-8")
###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###        
        msg_ifx.send_command('-s'+short_session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue" --tcp')
        cc_node["connected"] = True

    def disable_net_node(self, short_session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): disable_net_node(): instantiated")
        #system call to enable the interface (since CORE doesn't properly remove/stop the interfaces... yet?)
        suffix = "%x.%x.%s" % (int(cc_node["number"]), int(cc_dec_number), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' down'
        p = subprocess.Popen(shlex.split(cmd), encoding="utf-8")

        suffix = "%x.%x.%s" % (int(cc_dec_number), int(cc_node["number"]), short_session_number)
        localname = "veth" + suffix
        cmd = 'ifconfig '+ localname + ' down'
        p = subprocess.Popen(shlex.split(cmd), encoding="utf-8")
###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###
        msg_ifx.send_command('-s'+short_session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue" --tcp')
        cc_node["connected"] = False
            

def short_session_id(session_number):
        logging.debug("Swapper(): short_session_id(): Instantiated")
        snum = int(session_number)
        ans = (snum >> 8) ^ (snum & ((1 << 8) - 1))
        return ("%x" % ans)
