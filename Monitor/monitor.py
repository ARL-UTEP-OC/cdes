import multiprocessing
import shlex
import subprocess
import logging
import sys, traceback

class Monitor():
    
    def __init__(self, name, oqueue, cmd):
        logging.debug("Monitor(): instantiated")
        self.name = name
        self.cmd = cmd
        self.oqueue = oqueue
    
    def run_monitor(self):
        logging.debug("Monitor(): run monitor instantiated")
        proc_name = multiprocessing.current_process().name
        logging.debug("Monitor(): run_monitor(): Running Monitor in %s for %s!" % (proc_name, self.name))
        try:
            self.p = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE)
            logging.debug("Monitor(): run_monitor(): starting readline loop")
            while True:
                out = self.p.stdout.readline()
                if out == '' and self.p.poll() != None:
                    logging.debug("Monitor(): run_monitor(): breaking out")
                    break
                else: 
                    logging.debug("Monitor(): run_monitor(): adding to queue: " + out.strip())
                    self.oqueue.put(out.strip())
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Monitor(): run_monitor(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit() 

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")

    omqueue = multiprocessing.Queue()
    cmd = "./time_cont.sh"
    m = Monitor("monitor", omqueue, cmd)
    mp = multiprocessing.Process(target=m.run_monitor)
    mp.start()
    
    # Get output and print to screen
    while True:
        logging.debug("OM Queue: " + omqueue.get())
    
    logging.debug("Controller(): Completed")