#!/usr/bin/python3

from pyparsing import nestedExpr, originalTextFor
import logging
import sys, traceback
import fileinput

#from core.api.tlv.coreapi import CoreConfMessage, CoreEventMessage

class imnparser():
    
    def __init__(self, imnfilename):
        logging.debug("imnparser(): instantiated")
        self.imnfilename = imnfilename
        self.lanswitch_services = {}
        logging.debug("imnparser(): init(): Complete")
    
    def get_file_data(self):
        logging.debug("imnparser(): get_file_data(): instantiated")
        try:
            with open(self.imnfilename, 'r') as file:
                imndata = file.read()
            
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("imnparser(): get_file_data(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
        return imndata

    def parse_f5_config(self, config):
        """Very simple sanitizer output parser.

        This only parses "{ ... }" groups and ";" command separators.
        Everything else is treated as commands and command arguments.

        Each command is a list itself, and "{ ... }" groups are nested
        lists. Returns a list of commands.
        """

        # Normalize line endings.
        config = config.replace('\r\n', '\n')

        # Work around the sanitizer removing too much from the line when
        # removing an IP address.
        config = config.replace('servers <REMOVED>\n', 'servers {\n')

        # Standardize command separators.
        config = config.replace('\n', ';')

        # Ensure we can cleanly split on the symbols we care about.
        for symbol in ';{}':
            config = config.replace(symbol, ' %s ' % symbol)

        tokens = config.split()

        def parse_commands(pos):
            commands = []
            command = []
            while pos < len(tokens):
                token = tokens[pos]
                if token == ';':
                    if command:
                        # Avoid creating empty commands when seeing
                        # repeated command separators.
                        commands.append(command)
                        command = []
                elif token == '{':
                    nested, pos = parse_commands(pos + 1)
                    command.append(nested)
                elif token == '}':
                    if command:
                        commands.append(command)
                    return commands, pos
                else:
                    command.append(token)
                pos += 1
            if command:
                commands.append(command)
            return commands, pos

        commands, pos = parse_commands(0)

        if pos != len(tokens):
            msg = 'Could only parse %d of %d tokens' % (pos, len(tokens))
            raise RuntimeError(msg)
        return commands

    def extract_lanswitch_services(self, config):
        """Extract lanswitch_services from a sanitized F5 config.

        All lanswitch_services are returned in a mapping of node hostname to the list of
        services.
        """
        commands = self.parse_f5_config(config)

        lanswitch_services = {}

        for cmd in commands:
            islanswitch = False
            services = ""
            hostname = ""
            if cmd[0] == 'node':
                hostname = cmd[1].split("n")[1].strip()
                #print("Found Node!" + " " + str(hostname))
                parts = cmd[2]
                for p in parts:
                    if p[0] == 'type':
                        if len(p) == 2:
                            #print(str(p[1]))
                            islanswitch = True
                    if p[0] == 'services':
                        #print("Services for " + str(hostname) + ":")
                        if len(p) == 2:
                            # A pool with a list of members
                            #print(str(p[1]))
                            services = str(p[1][0])
                if islanswitch:
                    lanswitch_services[hostname] = services
        return lanswitch_services

###Not needed, but sample of how to access deeper data
    # def extract_trigger_files(self, config):
    #     """Extract lanswitch_services from a sanitized F5 config.

    #     All lanswitch_services are returned in a mapping of node hostname to the list of
    #     services.
    #     """
    #     commands = self.parse_f5_config(config)

    #     lanswitch_trigger_files = {}
    #     trigger_file = ""

    #     for cmd in commands:
    #         islanswitch = False
    #         hasTriggerFile = False
    #         hostname = ""
    #         if cmd[0] == 'node':
    #             hostname = cmd[1].split("n")[1].strip()
    #             #print("Found Node!" + " " + str(hostname))
    #             node_data = cmd[2]
    #             for p1 in node_data:
    #                 if p1[0] == 'type':
    #                     if len(p1) == 2:
    #                         #print(str(p[1]))
    #                         islanswitch = True
    #                 if p1[0] == 'custom-config':
    #                     if len(p1) > 1:
    #                         p1_custom_config = p1[1]
    #                         print("Custom config " + str(p1_custom_config))
    #                         if len(p1_custom_config[0]) > 1 and len(p1_custom_config[0][0]) > 1: #need at least custom-config-id, custom-command, and config
    #                             print("custom-config 1 level down:" + str(p1_custom_config[1][1]))
    #                             p1_filename = p1_custom_config[1][1]
    #                             if p1_filename == "MyTrigger.py":
    #                                 if len(p1_custom_config) > 2 and len(p1_custom_config[2]) > 1:
    #                                     hasTriggerFile = True
    #                                     trigger_file = str(p1_custom_config[2][1])
    #             if islanswitch and hasTriggerFile:
    #                 lanswitch_trigger_files[hostname] = trigger_file
    #     return lanswitch_trigger_files

if __name__ == '__main__':
    import pprint

    filename = "sample/scenario/CC_NodeTest.imn"
    parser = imnparser(filename)
    
    data = parser.get_file_data()
    
    services = parser.extract_lanswitch_services(data)
    pprint.pprint(services)
    #print("SERVICE:\n"+ str(services["6"]))
    