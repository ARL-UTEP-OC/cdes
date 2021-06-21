import multiprocessing
import shlex
import subprocess
import logging
import sys, traceback
import psutil
import os, signal 
import select
import time

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
            self.p = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE, encoding="utf-8")
            logging.debug("Monitor(): run_monitor(): starting readline loop")
            poll_obj = select.poll()
            poll_obj.register(self.p.stdout, select.POLLIN)
            while True:
                time.sleep(.1)
                if self.iqueue.empty() == False:
                    self.cleanup()
                    break
                poll_result = poll_obj.poll(0)
                if poll_result:
                    out = self.p.stdout.readline()
                    logging.debug("Monitor(): child procs: " + str(psutil.Process(self.p.pid).children(recursive=True)))
                    if out == '' and self.p.poll() != None:
                        self.cleanup()
                        logging.debug("Monitor(): run_monitor(): breaking out")
                        break
                    else: 
                        logging.debug("Monitor(): run_monitor(): adding to queue: " + out.strip())
                        # Before adding to the output queue, make sure we're not terminating
                        self.oqueue.put(out.strip())
        except Exception as e:
            if self.p != None:
                logging.error("Monitor(): run_monitor(): Terminating Monitor Process ")
                self.cleanup()
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Monitor(): run_monitor(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit()
    
    def cleanup(self):
        try:
            if self.p != None:
                logging.debug("Monitor(): run_monitor(): Terminating Monitor Process ")
                logging.debug("Monitor(): child procs: " + str(psutil.Process(self.p.pid).children(recursive=True)))
                for child in psutil.Process(self.p.pid).children(recursive=True):
                    child.terminate()
                self.p.terminate()
                if self.p.poll() == None:
                    logging.debug("Monitor(): run_monitor(): Terminating Monitor Process ")
                    logging.debug("Monitor(): child procs: " + str(psutil.Process(self.p.pid).children(recursive=True)))
                    for child in psutil.Process(self.p.pid).children(recursive=True):
                        child.terminate()
                    self.p.terminate()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Monitor(): cleanup(): An error occured ")
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            exit()


