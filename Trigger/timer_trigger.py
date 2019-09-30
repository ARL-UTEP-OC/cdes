import multiprocessing
from multiprocessing import TimeoutError
from Queue import Empty
import logging
import subprocess
import shlex
import threading
import time
from trigger import Trigger

class TimerTrigger(Trigger):  

    #Implemented abstractmethod
    def process_data(self):

        while True:
            data = self.read_input_line()
            if data == None:
                logging.info("Nothing read")
                continue
            logging.debug("Data: " + data)
            new_time = int(data)
            nodes = self.get_cc_node_names()
            #set active node every 10 seconds
            if new_time % 10 == 0:
                logging.debug("10 sec mark")
                if new_time %20 == 0:
                    self.set_active_conn(nodes[0])
                else:
                    self.set_active_conn(nodes[1])
    
if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")
    
    omqueue = multiprocessing.Queue()
    otqueue = multiprocessing.Queue()

    conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }

    tp = TimerTrigger("trigger", omqueue, otqueue, conditional_conns)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()
    
    # Get output and print to screen
    for i in xrange(60):
        omqueue.put(str(i)+"\n")
        time.sleep(.1)
    
    logging.debug("Controller(): Completed")