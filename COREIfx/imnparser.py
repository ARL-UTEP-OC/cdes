#!/usr/bin/python

from pyparsing import nestedExpr, originalTextFor
import logging
import sys, traceback
import fileinput

#from core.api.tlv.coreapi import CoreConfMessage, CoreEventMessage

class imnparser():
    
    def __init__(self, imnfilename):
        logging.debug("tcl_parser(): instantiated")
        self.imnfilename = imnfilename
        self.lanswitch_services = {}
        logging.debug("tcl_parser(): init(): Complete")
    
    def get_file_data(self):
        logging.debug("tcl_parser(): get_lanswitch_service instantiated")
        try:
            with open(self.imnfilename, 'r') as file:
                imndata = file.read()
            
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("SessionReader(): get_session_state(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit() 
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

if __name__ == '__main__':
    import pprint

    filename = "/home/researchdev/Desktop/myfile.imn"
    parser = imn_parser(filename)
    
    data = parser.get_file_data()
    #data = ''.join(fileinput.input())
    
    services = parser.extract_lanswitch_services(data)
    try:
        pprint.pprint(services)
    except RuntimeError as exc:
        print exc
