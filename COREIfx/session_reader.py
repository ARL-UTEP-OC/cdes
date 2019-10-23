#!/usr/bin/python

import xml.etree.ElementTree as ET
import logging
import os
import json
import sys, traceback
from COREIfx import msg_ifx
from COREIfx.imnparser import imnparser
from pyparsing import nestedExpr, originalTextFor

#from core.api.tlv.coreapi import CoreConfMessage, CoreEventMessage

class SessionReader():
    
    def __init__(self, session_number=None):
        logging.debug("SessionReader(): instantiated")
        if session_number == None:
            #just get one from /tmp/pycore***
            logging.error("No session number was provided")
            exit()
        self.session_number = session_number
        logging.debug("SessionReader(): init(): Retrieving imn filename")
        services_resp = str(msg_ifx.send_command('-s'+self.session_number+' SESSION flags=STRING --tcp -l'))
        self.imnfilename = ""
        for line in services_resp.splitlines():
            if "FILE: " in line:
                #we know this line has the imn filename
                ###TODO### Need to make sure we get the correct filename associated with the session
                self.imnfilename = line.split("FILE: ")[1].split("|")[0]
                break
        if self.imnfilename == "":
            logging.error("No associated imn file found. Exiting")
            return
        logging.debug("SessionReader(): init(): Found filename: " + str(self.imnfilename))

        self.xmlfilename = os.path.join("/tmp","pycore."+str(session_number),"session-deployed.xml")       
        state = self.get_session_state()
        logging.debug("Current session state: " + str(state))
        if state == None:
            logging.debug("Exiting since session data is not available: " + str(state))
            exit()

        self.conditional_conns = self.relevant_session_to_JSON()

    def get_session_state(self):
        logging.debug("SessionReader(): get_session_state() instantiated")

        try:
        #check first if directory exists
            session_path = os.path.dirname(self.xmlfilename)
            session_state_path = os.path.join(session_path,"state")
            if os.path.exists(session_path) == False or os.path.exists(session_state_path) == False:
                logging.debug("SessionReader(): get_session_state() session does not exist!")
                return None
            logging.debug("SessionReader(): get_session_state() session found!")
            #read state file
            state_file_state = open(session_state_path,"r").readlines()[0]
            logging.debug("SessionReader(): get_session_state(): State: " + str(state_file_state))

            return state_file_state
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("SessionReader(): get_session_state(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit() 
        return None

    def relevant_session_to_JSON(self):
        logging.debug("SessionReader(): relevant_session_to_JSON() instantiated")
        iparser = imnparser(self.imnfilename)
        tree = ET.parse(self.xmlfilename)
        root = tree.getroot()
        conditional_conns = {}
        name_id_map = {}
        switches = []
        switch_ids = []
        links = root.find('links').findall('link')

        device_services = {}
        switch_services = {}
        #find all devices (non-switch/hub/wireless) and identify their name/id mappings and services
        logging.debug("SessionReader(): relevant_session_to_JSON(): " + "finding devices")
        for device in root.find('devices').findall('device'):
            #keep track of mappings
            name_id_map[device.attrib["name"]] = device.attrib["id"]
            services = ""
            for service in device.find('services').findall('service'):
                services += " " + str(service.attrib["name"])
            #store the services that are enabled for this device
            device_services[device.attrib["id"]] = services

        logging.debug("SessionReader(): relevant_session_to_JSON(): " + "finding switches")
        #find switch type nodes (the type "SWITCH") and then store the name/id mappings
        for node in root.find('networks').findall('network'):
            if node.attrib["type"] == "SWITCH":
                switches.append(node)
                switch_ids.append(node.attrib["id"])
                #keep track of mappings
                name_id_map[node.attrib["name"]] = node.attrib["id"]

        #now obtain the services for all switch nodes
        logging.debug("SessionReader(): relevant_session_to_JSON(): " + "obtaining services for switches")
        data = iparser.get_file_data()       
        switch_services = iparser.extract_lanswitch_services(data)

        # for node_id in node_name_services:
        #     logging.error("Iterating over switch node services" + str(node_id))
        #     #hostname = node_name
        #     #node_id = name_id_map[hostname]
        #     services = node_name_services[node_id]
        #     if services == "":
        #         continue
        #     switch_services[node_id] = services
        logging.error("switch services: " + str(switch_services)) 
        #exit()

        for node in switches:
            logging.debug("SessionReader(): relevant_session_to_JSON(): " + "traversing through switches; processing CC_DecisionNode")
            node_id = node.attrib["id"]
            #check if this is a decision node
            #if it isn't move on to the next switch
            if "CC_DecisionNode" not in switch_services[node_id]:
                continue

            #get the source code for files
            monitor_code = self.get_node_file(node, "CC_DecisionNode", "MyMonitor.sh")
            trigger_code = self.get_node_file(node, "CC_DecisionNode", "MyTrigger.py")
            swapper_code = self.get_node_file(node, "CC_DecisionNode", "MySwapper.py")
                
            #setup entry for node
            conditional_conn = {}
            cc_node_number = node.attrib["id"]            
            conditional_conn["name"] = node.attrib["name"]
            conditional_conn["MyMonitor.sh"] = monitor_code
            conditional_conn["MyTrigger.py"] = trigger_code
            conditional_conn["MySwapper.py"] = swapper_code

            logging.debug("Found node: " + str(conditional_conn))

            #now find all connected nodes and whether they're cc_gw or cc_node; store associated data
            
            connected_nodes = []
            for link in links:
                connected_node = {}
                #logging.debug("Checking:" + str(link.attrib["node_one"] + " == " + cc_node_number))
                if link.attrib["node_one"] == cc_node_number:
                    connected_node["number"] = link.attrib["node_two"]
                if link.attrib["node_two"] == cc_node_number:
                    connected_node["number"] = link.attrib["node_one"]
                if "number" not in connected_node:
                    continue

                ifx = link.find("interface_one")
                if ifx == None:
                    ifx = link.find("interface_two")
                    if ifx == None:
                        continue
                    #found a connection, now we have to add all details
                    #get the type of the node
                    if connected_node["number"] in switch_ids:
                        #switch to switch conns won't have any other useful information
                        connected_node["node_type"] = "SWITCH"
                    else:
                        #switch to node will have additional useful information
                        connected_node["node_type"] = "other"
                        connected_node["cc_nic"] = ifx.attrib["name"]
                        connected_node["cc_mac"] = ifx.attrib["mac"]
                        connected_node["cc_ip4"] = ifx.attrib["ip4"]
                        connected_node["cc_ip4_mask"] = ifx.attrib["ip4_mask"]
                        if "ip6" in ifx.attrib:
                            connected_node["cc_ip6"] = ifx.attrib["ip6"]
                            connected_node["cc_ip6_mask"] = ifx.attrib["ip6_mask"]
                    
                    #by default we consider this a cc_gw node, but we'll figure out if it's a cc_node next
                    connected_node["role"] = "cc_gw"

                    #if node has the CC_Node service enabled, then we know this is a cc_node; otherwise, it's a gw
                    ##TODO REPLACE DEVICE TRAVERSAL
                    if connected_node["number"] in device_services:
                        if "CC_Node" in device_services[connected_node["number"]]:
                            #we know this is a good node
                            connected_node["role"] = "cc_node"

                    #now check if the connected switches/nets have the CC_Node service enabled
                    if connected_node["number"] in switch_services:
                        if "CC_Node" in switch_services[connected_node["number"]]:
                            #we know this is a good node
                            connected_node["role"] = "cc_node"

                    connected_node["connected"] = "False"
                    connected_nodes.append(connected_node)
            conditional_conn["connected_nodes"] = connected_nodes
            conditional_conns[node.attrib["id"]] = conditional_conn
        return conditional_conns

    def get_conditional_conns(self, cc_dec_number):
        return self.conditional_conns[cc_dec_number]

    def get_node_file(self, node, service_name, filename):
        #First check if file exists:
        res = str(msg_ifx.send_command('-s'+self.session_number+' CONFIG NODE='+node.attrib["id"] +' OBJECT=services OPAQUE=service:'+service_name+' TYPE=1 -l --tcp'))
        file_exists = False
        for line in res.splitlines():
            if filename in line:
                file_exists = True
                break
        if file_exists == False:
            return ""
        #Get file contents
        res_code = str(msg_ifx.send_command('-s'+self.session_number+' CONFIG NODE='+node.attrib["id"] +' OBJECT=services OPAQUE=service:'+service_name+':'+filename+' TYPE=1 -l --tcp'))
        file_code = ""
        code_section = False
        for code_line in res_code.splitlines():
            if code_line.startswith("  DATA:"):
                code_section = True
                file_code += code_line.split("DATA: ")[1] + "\n"
                continue
            if "NODE: " in code_line:
                code_section = False
                break
            if code_section:
                file_code += code_line + "\n"
        return file_code

    def get_node_services(self, node):
        res_services = str(msg_ifx.send_command('-s'+self.session_number+' CONFIG NODE='+node.attrib["id"] +' OBJECT=services OPAQUE=service' +' TYPE=1 -l --tcp'))
        return res_services

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("SessionReader(): instantiated")
    
    if len(sys.argv) < 2:
        logging.error("Usage: python controller.py <session-number>")
        exit()       
    
    sr = SessionReader(sys.argv[1])
    logging.debug("Printing All")
    state = sr.get_session_state
    logging.debug("Current session state: " + str(state))
    if state == None:
        logging.debug("Exiting since session data is not available: " + str(state))
        exit()
    logging.info(json.dumps(sr.relevant_session_to_JSON(), indent=3))

    #conditional_conns = get_conditional_conns()