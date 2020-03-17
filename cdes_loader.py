import multiprocessing
import imp
import shlex
import subprocess
from Trigger.timer_trigger import TimerTrigger
from Swapper.swapper import Swapper
from Monitor.monitor import Monitor
from COREIfx.session_reader import SessionReader
import sys, traceback
import logging
import time
import sys
import os
import json
import shutil

def get_sorted_in_dirs(path, dircontains=""):
    logging.debug("CDES_Loader(): get_sorted_in_dirs(): Instantiated")
    name_list = os.listdir(path)
    dirs = []
    for name in name_list:
        fullpath = os.path.join(path,name)
        if os.path.isdir(fullpath) and (dircontains in name):
            dirs.append(fullpath)
    logging.debug("CDES_Loader():get_sorted_in_dirs(): Completed")
    if dirs != None:
        return sorted(dirs)
    return []

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("CDES_Loader(): instantiated")

###Get session if supplied, otherwise, get the latest###
    if len(sys.argv) == 1:
        dirs = get_sorted_in_dirs("/tmp/", dircontains="pycore")
        if len(dirs) == 0:
            logging.error("CDES_Loader(): Main(): No sessions exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()
        scen_dir = dirs[0]
        session_number = scen_dir.split("pycore.")[1]
        logging.warning("CDES_Loader(): Main(): Session Number was not passed in; will use latest: " + session_number)

    elif len(sys.argv) == 2:
        session_number = sys.argv[1]
        scen_dir = os.path.join("/tmp","pycore."+str(sys.argv[1]))
        if os.path.exists(scen_dir) == False:
            logging.error("CDES_Loader(): Main(): Session "+str(sys.argv[1])+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()

    else:
        logging.error("Usage: python cdes_loader.py [session-number]")
        exit()
###Get absolute path where this current script exists
    try:
        filepath = os.path.realpath(__file__)
        cdes_dir = os.path.dirname(filepath)
        cdes_scen_dir = os.path.join(scen_dir,"cdes")
        if os.path.exists(cdes_scen_dir):
            logging.debug("CDES_Loader(): Main(): Path EXISTS SO REMOVING " + str(cdes_scen_dir))
            shutil.rmtree(cdes_scen_dir)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error("CDES_Loader(): Main(): An error occured ")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        exit() 

###Copy cdes source to the current session's folder
    try:
        shutil.copytree(cdes_dir, cdes_scen_dir)
    # Directories are the same
    except shutil.Error as e:
        logging.error("CDES_Loader(): Main(): Directory not copied. Error: %s" % e)
        exit()
    # Any error saying that the directory doesn't exist
    except OSError as e:
        logging.error("CDES_Loader(): Main(): Directory not copied. Error: %s" % e)
        exit()

###Get node states
    sr = SessionReader(session_number)
    # First check to make sure the session is in a running state
    state = sr.get_session_state()
    if state == None:
        logging.error("CDES_Loader(): Main(): Session "+str(session_number)+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
        exit()
    while "4 RUNTIME_STATE" not in state:
        logging.warning("CDES_Loader(): Main(): Session "+str(session_number)+" Is not yet in the running state... waiting and then trying again")
        if state == None:
            logging.error("CDES_Loader(): Main(): Session "+str(session_number)+" does not exist, make sure core-daemon is running. \n You can start it by running /etc/init.d/core-daemon start")
            exit()
        time.sleep(3)
        state = sr.get_session_state()

    # Get the current topology
    conditional_conns = sr.relevant_session_to_JSON()

###Create a subfolder for all CC_DecisionNodes and write their custom files there
###Get absolute path where this current script exists
    try:
        #Create directories for each node
        cdes_scen_dir_monitor_code = os.path.join(cdes_scen_dir,"Monitor")
        cdes_scen_dir_trigger_code = os.path.join(cdes_scen_dir,"Trigger")
        cdes_scen_dir_swapper_code = os.path.join(cdes_scen_dir,"Swapper")
        for node in conditional_conns.keys():
            print ("NODE: " + str(node))
            monitor_file_node_path = os.path.join(cdes_scen_dir,cdes_scen_dir_monitor_code,conditional_conns[node]["name"])
            trigger_file_node_path = os.path.join(cdes_scen_dir,cdes_scen_dir_trigger_code,conditional_conns[node]["name"])
            swapper_file_node_path = os.path.join(cdes_scen_dir,cdes_scen_dir_swapper_code,conditional_conns[node]["name"])
            os.makedirs(monitor_file_node_path)
            os.makedirs(trigger_file_node_path)
            os.makedirs(swapper_file_node_path)
            #Get file data and write it to the node's path
            if "MyMonitor.sh" in conditional_conns[node]:
                open(os.path.join(monitor_file_node_path,"__init__.py"),"w+").close()
                monitor_file_path = os.path.join(monitor_file_node_path,"MyMonitor.sh")
                monitor_file = open(monitor_file_path,"w+")
                monitor_file.write(conditional_conns[node]["MyMonitor.sh"])
                monitor_file.close()
                os.chmod(monitor_file_path, 0o555)
            if "MyTrigger.py" in conditional_conns[node]:
                open(os.path.join(trigger_file_node_path,"__init__.py"),"w+").close()
                trigger_file = open(os.path.join(trigger_file_node_path,"MyTrigger.py"),"w+")
                trigger_file.write(conditional_conns[node]["MyTrigger.py"])
                trigger_file.close()
            if "MySwapper.py" in conditional_conns[node]:
                open(os.path.join(swapper_file_node_path,"__init__.py"),"w+").close()
                swapper_file = open(os.path.join(swapper_file_node_path,"MySwapper.py"),"w+")
                swapper_file.write(conditional_conns[node]["MySwapper.py"])
                swapper_file.close()

###Instantiate the new module via a system call

        #cmd = "python "+os.path.join(cdes_scen_dir,"controller.py")+" " +os.path.join(monitor_file_node_path,"MyMonitor.sh")+" "+session_number
        #p = subprocess.Popen(shlex.split(cmd), cwd=cdes_scen_dir)
        controller = imp.load_source('Controller', os.path.join(cdes_scen_dir,"controller.py"))
        cr = controller.Controller()
        cr.cdes_run(monitor_cmd=os.path.join(monitor_file_node_path,"MyMonitor.sh"), session_number=session_number, conditional_conns=conditional_conns)
    
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error("CDES_Loader(): Main(): An error occured ")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        exit() 
    
    logging.debug("CDES_Loader(): Main(): Completed")