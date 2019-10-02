#!/usr/bin/python

import xml.etree.ElementTree as ET
import logging
import os
import json
import sys

class SessionReader():
    
    def __init__(self, session_number=None):
        logging.debug("Monitor(): instantiated")
        if session_number == None:
            #just get one from /tmp/pycore***
            logging.error("No session number was supplied")
            exit()

        self.filename = os.path.join("/tmp","pycore."+str(session_number),"session-deployed.xml")
        self.conditional_conns = self.relevant_session_to_JSON()

    def relevant_session_to_JSON(self):
        tree = ET.parse(self.filename)
        root = tree.getroot()
        conditional_conns = {}
        #First find a switch type node with the "yellow icon"
        for cc_node in root.find('networks').findall('network'):
            if cc_node.attrib["icon"] != "router_yellow.gif" or cc_node.attrib["type"] != "SWITCH":
                return ""
            conditional_conn = {}
            cc_node_number = cc_node.attrib["id"]            
            conditional_conn["name"] = cc_node.attrib["name"]
            logging.debug("Found node: " + str(conditional_conn))

            #now find all connected nodes and whether they're cc_gw or cc_node; store associated data
            links = root.find('links').findall('link')
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
                    connected_node["cc_nic"] = ifx.attrib["name"]
                    connected_node["cc_mac"] = ifx.attrib["mac"]
                    connected_node["cc_ip4"] = ifx.attrib["ip4"]
                    connected_node["cc_ip4_mask"] = ifx.attrib["ip4_mask"]
                    if "ip6" in ifx.attrib:
                        connected_node["cc_ip6"] = ifx.attrib["ip6"]
                        connected_node["cc_ip6_mask"] = ifx.attrib["ip6_mask"]
                    connected_node["role"] = "cc_gw"

                    #if node icon is black, we know this is a cc_node; otherwise, it's a gw
                    for device in root.find('devices').findall('device'):
                        if device.attrib["id"] == connected_node["number"] and "icon" in device.attrib and device.attrib["icon"] == "router_black.gif":
                            connected_node["role"] = "cc_node"
                            break
                                    
                    connected_node["connected"] = "False"
                    connected_nodes.append(connected_node)
            conditional_conn["connected_nodes"] = connected_nodes
            conditional_conns[cc_node.attrib["id"]] = conditional_conn["connected_nodes"]
        return conditional_conns

    def get_conditional_conns(self, cc_dec_number):
        return self.conditional_conns[cc_dec_number]

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.debug("SessionReader(): instantiated")
    
    if len(sys.argv) < 2:
        logging.error("Usage: python controller.py <session-number>")
        exit()       
    
    sr = SessionReader(sys.argv[1])
    logging.debug("Printing All")
    logging.info(json.dumps(sr.relevant_session_to_JSON(), indent=3))
    logging.debug("Printing only #4")
    logging.info(json.dumps(sr.get_conditional_conns("4"), indent=3))
    #conditional_conns = get_conditional_conns()

