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
            logging.error("SessionReader(): init(): No session number was provided")
            return None
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
            logging.error("SessionReader(): init(): No associated imn file found. Exiting")
            return None
        logging.debug("SessionReader(): init(): Found filename: " + str(self.imnfilename))

        self.xmlfilename = os.path.join("/tmp","pycore."+str(session_number),"session-deployed.xml")       
        state = self.get_session_state()
        logging.debug("SessionReader(): init(): Current session state: " + str(state))
        if state == None:
            logging.error("SessionReader(): init(): Session state is not available: " + str(state))
            return None

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
            return None

    def relevant_session_to_JSON(self):
        logging.debug("SessionReader(): relevant_session_to_JSON() instantiated")
        try:
            try:
                iparser = imnparser(self.imnfilename)
            except Exception:
                logging.error("SessionReader(): relevant_session_to_JSON(): imn scenario file not found: " + str(self.imnfilename))
                logging.error("SessionReader(): relevant_session_to_JSON(): " + self.session_number + " and ensure the imn file exists and is loaded in CORE")
                return None
            try:
                tree = ET.parse(self.xmlfilename)
            except Exception:
                logging.error("SessionReader(): relevant_session_to_JSON(): XML file not found: " + str(self.imnfilename))
                logging.error("SessionReader(): relevant_session_to_JSON(): " + self.session_number + " has been run at least once or is running." )
                return None

            root = tree.getroot()
            conditional_conns = {}
            name_id_map = {}
            switches = []
            switch_ids = []
            links = root.find('links').findall('link')

            device_services = {}
            switch_services = {}
            switch_service_configurations = {}
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

            #find service files for switch type nodes and then store them
            services = root.find('service_configurations').findall('service')
            node_num = ""
            service_name = ""
            filename = ""
            file_code = ""
            for service in services:
                #Pulling service name and node id from tags
                node_num = service.attrib["node"]
                service_name = service.attrib["name"]
                if node_num in switch_ids:
                    service_name = service.attrib["name"]
                    #Pulling filenames from tags
                    files = service.find("files").findall("file")
                    for filenode in files:
                        filename = filenode.attrib["name"]
                        #Pulling source code from tags
                        file_code = filenode.text
                        switch_service_configurations[(node_num, service_name, filename)] = file_code

            #now obtain the services for all switch nodes
            logging.debug("SessionReader(): relevant_session_to_JSON(): " + "obtaining enabled services for switches")
            data = iparser.get_file_data()       
            switch_services = iparser.extract_lanswitch_services(data)

            logging.debug("SessionReader(): relevant_session_to_JSON():Switch services found: " + str(switch_services)) 

            #Iterating through all switch nodes to consolidate source files and conditional connections
            for node in switches:
                logging.debug("SessionReader(): relevant_session_to_JSON(): " + "traversing through switches; processing CC_DecisionNode")
                node_id = node.attrib["id"]
                #check if this is a decision node
                #if it isn't move on to the next switch
                if "CC_DecisionNode" not in switch_services[node_id]:
                    continue

                #get the source code for files
                if (node_id, "CC_DecisionNode", "MyMonitor.sh") not in switch_service_configurations:
                    monitor_code = ""
                else: monitor_code = switch_service_configurations[(node_id, "CC_DecisionNode", "MyMonitor.sh")]
                if (node_id, "CC_DecisionNode", "MyTrigger.py") not in switch_service_configurations:
                    trigger_code = ""
                else: trigger_code = switch_service_configurations[(node_id, "CC_DecisionNode", "MyTrigger.py")]
                if (node_id, "CC_DecisionNode", "MySwapper.py") not in switch_service_configurations:
                    swapper_code = ""
                else: swapper_code = switch_service_configurations[(node_id, "CC_DecisionNode", "MySwapper.py")]
                    
                #setup entry for node
                conditional_conn = {}
                cc_node_number = node.attrib["id"]            
                conditional_conn["name"] = node.attrib["name"]
                conditional_conn["MyMonitor.sh"] = monitor_code
                conditional_conn["MyTrigger.py"] = trigger_code
                conditional_conn["MySwapper.py"] = swapper_code

                logging.debug("SessionReader(): relevant_session_to_JSON(): Processing node: " + str(conditional_conn))

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
        except Exception:
            logging.error("SessionReader(): relevant_session_to_JSON(): Error in relevant_session_to_JSON(): An error occured ")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            return None


    def get_conditional_conns(self, cc_dec_number):
        logging.debug("SessionReader(): get_conditional_conns(): instantiated")
        return self.conditional_conns[cc_dec_number]

    def get_node_services(self, node):
        logging.debug("SessionReader(): get_node_services(): instantiated")
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
