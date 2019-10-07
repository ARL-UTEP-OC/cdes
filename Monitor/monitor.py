import multiprocessing
import shlex
import subprocess
import logging
import sys, traceback

class Monitor():
    
    def __init__(self, name, iqueue, oqueue, cmd):
        logging.debug("Monitor(): instantiated")
        self.name = name
        self.cmd = cmd
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.p = None
    
    def run_monitor(self):
        logging.debug("Monitor(): run monitor instantiated")
        proc_name = multiprocessing.current_process().name
        logging.debug("Monitor(): run_monitor(): Running Monitor in %s for %s!" % (proc_name, self.name))
        try:
            logging.debug("Monitor(): run_monitor: running " + str(self.cmd))
            self.p = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE)
            logging.debug("Monitor(): run_monitor(): starting readline loop")
            while True:
                out = self.p.stdout.readline()
                if out == '' and self.p.poll() != None:
                    logging.debug("Monitor(): run_monitor(): breaking out")
                    break
                else: 
                    logging.debug("Monitor(): run_monitor(): adding to queue: " + out.strip())
                    # Before adding to the output queue, make sure we're not terminating
                    if self.iqueue.empty() == False:
                        if self.p.poll() == None:
                            logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                            self.p.terminate()
                        break
                    self.oqueue.put(out.strip())
        except Exception as e:
            if self.p != None:
                logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                self.p.terminate()
                if self.p.poll() == None:
                    logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                    self.p.terminate()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Monitor(): run_monitor(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit()
    
    def cleanup(self):
        try:
            if self.p != None:
                logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                self.p.terminate()
                if self.p.poll() == None:
                    logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                    self.p.terminate()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Monitor(): cleanup(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit()

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")

    omqueue = multiprocessing.Queue()
    cmd = "sample/time_cont.sh"
    m = Monitor("monitor", omqueue, cmd)
    mp = multiprocessing.Process(target=m.run_monitor)
    mp.start()
    
    # Get output and print to screen
    while True:
        logging.debug("OM Queue: " + omqueue.get())
    
    logging.debug("Monitor(): Completed")