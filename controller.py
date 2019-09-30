import multiprocessing
from Trigger.timer_trigger import TimerTrigger
from Swapper.swapper import Swapper
from Monitor.monitor import Monitor
import logging
import time

if __name__ == '__main__':
   
    logging.basicConfig(level=logging.DEBUG)
    logging.debug("Controller(): instantiated")

    conditional_conns = {"4": {"cc_gw": "1", "cc_nodes": {"5": False, "2": False} } }

    omonitor_queue = multiprocessing.Queue()
    
    otrigger_queue = multiprocessing.Queue()

    oswapper_queue = multiprocessing.Queue()

    m = Monitor("monitor", omonitor_queue, "./sample/time_cont.sh")
    mp = multiprocessing.Process(target=m.run_monitor)
    mp.start()

    tp = TimerTrigger("trigger", omonitor_queue, otrigger_queue, conditional_conns)
    tp = multiprocessing.Process(target=tp.process_data)
    tp.start()
    

    sw = Swapper("swapper", otrigger_queue, oswapper_queue, conditional_conns, "1")
    sw = multiprocessing.Process(target=sw.update_connection)
    sw.start()
    
    # Get output and print to screen
    while True:
        #logging.debug("Processing...)
        time.sleep(0.1)
    
    logging.debug("Controller(): Completed")