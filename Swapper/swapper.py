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
        
        self.cc_dec_name = self.conditional_conns[cc_dec_number]["name"]
        self.conditional_conns_cc_dec = {}
        
        self.session_number = session_number
        self.short_session_number = short_session_number

        cc_node_numbers = []

        self.conditional_conns_cc_dec[cc_dec_number] = {}
        for node in self.conditional_conns[cc_dec_number]["connected_nodes"]:
            if node["role"] == "cc_node":
                logging.debug("Swapper(): set_active_conn(): found cc_node: " + str(node))
                cc_node_numbers.append(node)
        self.conditional_conns_cc_dec[cc_dec_number]["cc_node_numbers"] = cc_node_numbers

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
            #process depending on message type
            if isinstance(data[0], int):
                msg_type = data[0]
                logging.debug("Swapper(): msg recvd type: " + str(data[0]))
                if msg_type == 1:
                    #specify single connection using decnode's nic name
                    [cc_dec_number, active_dec_nic, disable_others] = data[1:]
                    logging.debug("Swapper(): update_connection(): looking at nodes: " + str(self.conditional_conns_cc_dec[cc_dec_number]))
                    for node in self.conditional_conns_cc_dec[cc_dec_number]["cc_node_numbers"]:
                        if node["cc_dec_nic"] == active_dec_nic:
                            self.enable_single_node(self.session_number, cc_dec_number, node)
                        else:
                            if disable_others == True:
                                logging.debug("Disabling other cc_dec: " + str(cc_dec_number) + " node: " + str(node))
                                self.disable_single_node(self.session_number, cc_dec_number, node)
                elif msg_type == 2:
                    #specify multiple on/off connections using decnode's nic names
                    [cc_dec_number, active_dec_nics, deactive_cc_dec_nics] = data[1:]
                    activate_nodes = []
                    deactivate_nodes = []
                    logging.debug("Swapper(): update_connection(): looking at nodes: " + str(self.conditional_conns_cc_dec[cc_dec_number]))
                    for node in self.conditional_conns_cc_dec[cc_dec_number]["cc_node_numbers"]:
                        if node["cc_dec_nic"] in active_dec_nics:
                            activate_nodes.append(node)
                    for node in self.conditional_conns_cc_dec[cc_dec_number]["cc_node_numbers"]:
                        if node["cc_dec_nic"] in deactive_cc_dec_nics:
                            deactivate_nodes.append(node)
                    self.set_decnode_conns(self.session_number, cc_dec_number, activate_nodes, deactivate_nodes)
                else:
                    logging.error("Swapper(): unknown message type recieved: " + str(data[0]))

    def startovs(self, session_number, cc_dec_number):
        #eventually move the ovs service start logic here... maybe
        #msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl add-port ovsbr0 '+cc_node["cc_dec_nic"]+'" --tcp')
        pass

    def enable_single_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): enable_single_node(): instantiated")
        #logging.debug("enable single node cmd: " + '-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl add-port ovsbr0 '+cc_node["cc_dec_nic"]+' --tcp')
        logging.debug("enable single node cmd: " + '-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl add-port ovsbr0 "+cc_node["cc_dec_nic"])
        #msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl add-port ovsbr0 '+cc_node["cc_dec_nic"]+'" --tcp')
        msg_ifx.run_command('-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+" -- ovs-vsctl add-port ovsbr0 "+cc_node["cc_dec_nic"])
###TODO: The following will trigger an non-fatal error on core-daemon because it claims the interface numbers need to be specified... still works though
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue" ')
        cc_node["connected"] = True

    def disable_single_node(self, session_number, cc_dec_number, cc_node):
        logging.debug("Swapper(): disable_single_node(): instantiated")
        #logging.debug("enable single node cmd: " + '-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl del-port ovsbr0 '+cc_node["cc_dec_nic"]+' --tcp')
        logging.debug("disabling single node cmd: " + '-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl del-port ovsbr0 "+cc_node["cc_dec_nic"])
        #msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl del-port ovsbr0 '+cc_node["cc_dec_nic"]+'" --tcp')
        msg_ifx.run_command('-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl del-port ovsbr0 "+cc_node["cc_dec_nic"])
###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###        
        msg_ifx.send_command('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=yellow" ')
        cc_node["connected"] = False

    def set_decnode_conns(self, session_number, cc_dec_number, activate_nodes, deactivate_nodes):
        logging.debug("Swapper(): set_decnode_conns(): instantiated")
        activate_cmd_queue = []
        deactivate_cmd_queue = []
        send_cmd_queue = []
        ###Queue up the commands; so that we can execute with little delay in-between
        for cc_node in deactivate_nodes:
            logging.debug("disabling conn to node cmd: " + '-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl del-port ovsbr0 "+cc_node["cc_dec_nic"])
            activate_cmd_queue.append('-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl del-port ovsbr0 "+cc_node["cc_dec_nic"])
            send_cmd_queue.append('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=yellow" ')
            cc_node["connected"] = False
        for cc_node in activate_nodes:
            logging.debug("activating conn to node cmd: " + '-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl add-port ovsbr0 "+cc_node["cc_dec_nic"])
            #msg_ifx.send_command('-s'+session_number+' EXECUTE NODE='+cc_dec_number+' NUMBER=1000 COMMAND="ovs-vsctl del-port ovsbr0 '+cc_node["cc_dec_nic"]+'" --tcp')
            deactivate_cmd_queue.append('-c /tmp/pycore.'+session_number+'/'+self.cc_dec_name+ " -- ovs-vsctl add-port ovsbr0 "+cc_node["cc_dec_nic"])
    ###TODO: The following does not work with CORE 6.2, there is however a fix in the latest verison of CORE###        
            send_cmd_queue.append('-s'+session_number+' LINK N1_NUMBER='+cc_dec_number+' N2_NUMBER='+cc_node["number"]+' GUI_ATTRIBUTES="color=blue" ')
            cc_node["connected"] = True
        ##execute deactivations first; since it's better to have lag than duplicates
        for cmd in deactivate_cmd_queue:
            msg_ifx.run_command(cmd)
        for cmd in activate_cmd_queue:
            msg_ifx.run_command(cmd)
        for cmd in send_cmd_queue:
            msg_ifx.send_command(cmd)