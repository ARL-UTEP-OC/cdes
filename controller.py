import multiprocessing
from Trigger.timer_trigger import TimerTrigger
from Swapper.swapper import Swapper
from Monitor.monitor import Monitor
from COREIfx.session_reader import SessionReader
import imp
import logging
import time
import sys
import os
import json

class Controller():
    def __init__(self):
        logging.debug("Controller(): instantiated")   
        filepath = os.path.realpath(__file__)
        print("PATH!!!!!: " + str(filepath))
    
    def get_sorted_in_dirs(self, path, dircontains=""):
        logging.debug('Controller()" get_sorted_in_dirs(): Instantiated')
        name_list = os.listdir(path)
        dirs = []
        for name in name_list:
            fullpath = os.path.join(path,name)
            if os.path.isdir(fullpath) and (dircontains in name):
                dirs.append(fullpath)
        logging.debug('get_sorted_in_dirs(): Completed')
        if dirs != None:
            return sorted(dirs)
        return []

    def cdes_run(self, session_number=None, monitor_cmd=None, conditional_conns=None):
        logging.debug('Controller(): cdes_run(): Instantiated')
        if monitor_cmd == None:
            logging.error("Controller(): cdes_run(): No monitor command was passed in, quitting")
            exit()

        cmd = os.path.abspath(monitor_cmd)
        if session_number == None:
            logging.error("Controller(): cdes_run(): No session number was passed in, quitting")
            exit()
        sr = SessionReader(session_number)

        if conditional_conns == None:
            conditional_conns = sr.relevant_session_to_JSON()
        # For knowning when to quit
        imonitor_queue = multiprocessing.Queue()

        omonitor_queue = multiprocessing.Queue()
        
        otrigger_queue = multiprocessing.Queue()

        oswapper_queue = multiprocessing.Queue()

        m = Monitor("monitor", imonitor_queue, omonitor_queue, cmd)
        mp = multiprocessing.Process(target=m.run_monitor)
        mp.start()

        #If the user defined a custom Trigger, load it now
        #get cc_dec name
        first_cc_dec = conditional_conns.keys()[0]
        cc_dec_name = conditional_conns[first_cc_dec]["name"]
        filepath = os.path.realpath(__file__)
        file_dir = os.path.dirname(filepath)
        custom_file_path = os.path.join(file_dir,"Trigger",cc_dec_name,"MyTrigger.py")
        if os.path.exists(custom_file_path):
            DynLoadedClass = imp.load_source('MyTrigger', custom_file_path)
            tp = DynLoadedClass.MyTrigger("trigger", omonitor_queue, otrigger_queue, conditional_conns)
        else: 
            tp = TimerTrigger("trigger", omonitor_queue, otrigger_queue, conditional_conns)
        tp = multiprocessing.Process(target=tp.process_data)
        tp.start()
        
        sw = Swapper("swapper", otrigger_queue, oswapper_queue, conditional_conns, session_number)
        sw = multiprocessing.Process(target=sw.update_connection)
        sw.start()

        # Keep looping until the scenario is no longer in a Run state
        state = sr.get_session_state()
        if state == None:
            logging.error("Session "+str(session_number)+" no longer exists, exitting")
            exit()
        while "4 RUNTIME_STATE" in state:
            logging.debug("Session "+str(session_number)+" session Still running, continuing operations")
            if state == None:
                logging.error("Session "+str(session_number)+" no longer exists, exitting")
                break
            time.sleep(5)
            state = sr.get_session_state()
        
        # Logic to terminate all processes goes here
        logging.error("Cleaning up and exiting "+str(session_number))
        imonitor_queue.put("exit")
        logging.debug("Waiting for Monitor process to fininsh to gracefully exit")
        mp.join()
        # while mp.is_alive() == True:
        #     logging.debug("Waiting for process to fininsh to gracefully exit")
        #     time.sleep(3)
        logging.debug("Done.")
        mp.terminate()
        tp.terminate()
        sw.terminate()
        exit()

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Program instantiated")
    cr = Controller()

    if len(sys.argv) == 2:
        dirs = cr.get_sorted_in_dirs("/tmp/", dircontains="pycore")
        if len(dirs) == 0:
            logging.error("No sessions exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()
        mydir = dirs[0]
        session_number = mydir.split("pycore.")[1]
        logging.warning("Session Number was not passed in; will use latest: " + session_number)

    elif len(sys.argv) == 3:
        session_number = sys.argv[2]
        mydir = os.path.join("/tmp","pycore."+str(sys.argv[2]))
        if os.path.exists(mydir) == False:
            logging.error("Session "+str(sys.argv[2])+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()

    else:
        logging.error("Usage: python controller.py <monitor_process_path> [session-number]")
        exit()

    cr.cdes_run(monitor_cmd=sys.argv[1], session_number=session_number)
    
    # Get output and print to screen
    while True:
        #logging.debug("Processing...)
        time.sleep(0.1)
    
    logging.debug("Controller(): Completed")