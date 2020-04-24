#!/usr/bin/python3

from pyparsing import nestedExpr, originalTextFor
import logging
import sys, traceback
import fileinput
from COREIfx.imnparser import imnparser

if __name__ == '__main__':
    import pprint

    filename = "sample/scenario/CC_NodeTest.imn"
    parser = imnparser(filename)
    
    data = parser.get_file_data()
    
    services = parser.extract_lanswitch_services(data)
    pprint.pprint(services)
    #print("SERVICE:\n"+ str(services["6"]))
