#!/usr/bin/python

import xml.etree.ElementTree as ET
import logging
import os

class SessionReader():
    
    def __init__(self, session_number):
        logging.debug("Monitor(): instantiated")
        self.session_number = session_number
        self.filename = os.path.join("tmp","pycore."+str(self.session_number),"session-deployed.xml")
    
#    def get_conditional_conns()

if __name__ == "__main__":
    main()
