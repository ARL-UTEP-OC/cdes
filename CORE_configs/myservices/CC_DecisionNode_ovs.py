"""
Simple example for a user-defined service.
"""

from core.services.coreservices import CoreService
from core.services.coreservices import ServiceMode
import re

class MyService(CoreService):
    """
    Custom CORE Service

    :var str name: name used as a unique ID for this service and is required, no spaces
    :var str group: allows you to group services within the GUI under a common name
    :var tuple executables: executables this service depends on to function, if executable is
        not on the path, service will not be loaded
    :var tuple dependencies: services that this service depends on for startup, tuple of service names
    :var tuple dirs: directories that this service will create within a node
    :var tuple configs: files that this service will generate, without a full path this file goes in
        the node's directory e.g. /tmp/pycore.12345/n1.conf/myfile
    :var tuple startup: commands used to start this service, any non-zero exit code will cause a failure
    :var tuple validate: commands used to validate that a service was started, any non-zero exit code
        will cause a failure
    :var ServiceMode validation_mode: validation mode, used to determine startup success.
        NON_BLOCKING    - runs startup commands, and validates success with validation commands
        BLOCKING        - runs startup commands, and validates success with the startup commands themselves
        TIMER           - runs startup commands, and validates success by waiting for "validation_timer" alone
    :var int validation_timer: time in seconds for a service to wait for validation, before determining
        success in TIMER/NON_BLOCKING modes.
    :var float validation_validation_period: period in seconds to wait before retrying validation,
        only used in NON_BLOCKING mode
    :var tuple shutdown: shutdown commands to stop this service
    """
    name = "CC_DecisionNode_OVS"
    group = "Utility"
    dependencies = ()
    executables = ("ovs-ofctl", "ovs-vsctl")
    dirs = (
        "/etc/openvswitch",
        "/var/run/openvswitch",
        "/var/log/openvswitch",
    )
    startup = ("bash start_ovs.sh",)
    shutdown = ("killall ovs-vswitchd", "killall ovsdb-server")
    configs = ("MyMonitor.sh", "MyTrigger.py", "start_ovs.sh")
    validate = ()
    validation_mode = ServiceMode.NON_BLOCKING
    validation_timer = 5
    validation_period = 0.5

    @classmethod
    def on_load(cls):
        """
        Provides a way to run some arbitrary logic when the service is loaded, possibly to help facilitate
        dynamic settings for the environment.

        :return: nothing
        """
        pass

    @classmethod
    def get_configs(cls, node):
        """
        Provides a way to dynamically generate the config files from the node a service will run.
        Defaults to the class definition and can be left out entirely if not needed.

        :param node: core node that the service is being ran on
        :return: tuple of config files to create
        """
        return cls.configs

    @classmethod
    def generate_config(cls, node, filename):
        """
        Returns a string representation for a file, given the node the service is starting on the config filename
        that this information will be used for. This must be defined, if "configs" are defined.

        :param node: core node that the service is being ran on
        :param str filename: configuration file to generate
        :return: configuration file content
        :rtype: str
        """
   
        if filename == cls.configs[0]:
            cfg = "#!/bin/sh\n"
            cfg += "# auto-generated by CC_DecisionNode_OVS service\n"
            cfg += "# Call any/all scripts needed for the Monitor.\n"
            cfg += "# The stdout from this code will be given to MyTrigger.py for processing.\n"
            cfg += "# This is an example of using epoch time as the monitor data\n"
            cfg += """
while [ True ]
do
sleep 1
date +%s
done
"""
        if filename == cls.configs[1]:
            cfg = """# auto-generated by CC_DecisionNode_OVS service
# Short python to implement Trigger.
# The following three items are important:
# 1. You must write the process_data(self) function
# 2. Read the input (from the Monitor) by calling self.read_input_line()
# 3. Call the self.active_conn method with the cc node number as a parameter.
# The following is a sample that reads time information from the Monitor and 
# will swap between nodes every 15 seconds

import time
#Required import
from Trigger.trigger import Trigger

#Required class name that inherits Trigger
class MyTrigger(Trigger):  
    
    #Required function
    def process_data(self):
        #get the cc_node numbers
        nodes = self.get_cc_node_numbers()
        self.set_active_conn("eth0", disable_others=True)
        self.set_active_conn("eth1", disable_others=False)
        #use a counter to trigger call to swap
        count = 1
        #forever loop to process data
        while True:
####Modify to process Monitor's data and Trigger a switch####
            # read a line of input (from Monitor's stdout)
            data = self.read_input_line()
            print("READ: " + str(data))
            #if data yet exists, restart loop
            if data == None:
                continue
            # assuming we get one update per second
            count = count + 1
            new_time = int(data)
            #set active node every 15 seconds
            if count == 15:
                self.set_active_conn("eth0", disable_others=True)
                self.set_active_conn("eth2", disable_others=False)
            if count == 30:
                self.set_active_conn("eth0", disable_others=True)
                self.set_active_conn("eth1", disable_others=False)
                count = 1
####
"""            
        if filename == cls.configs[2]:
            cfg = "#!/bin/sh\n"
            cfg += "# auto-generated by CC_DecisionNode_OVS service\n"
            cfg += "## Start OVS service.\n"
            cfg += "/etc/init.d/openvswitch-switch start < /dev/null\n\n"
            cfg += "## create the switch\n"
            cfg += "ovs-vsctl add-br ovsbr0\n\n"

            portnum = 1
            for iface in node.get_ifaces(control=False):
                ifnumstr = re.findall(r"\d+", iface.name)
                ifnum = ifnumstr[0]

                # create virtual interfaces
                for ip4 in iface.ip4s:
                    cfg += "## Remove ipv4 address for this device.\n"
                    cfg += "ip addr del %s dev %s\n" % (ip4.ip, iface.name)
                for ip6 in iface.ip6s:
                    cfg += "## Remove ipv6 address for this device.\n"
                    cfg += "ip -6 addr del %s dev %s\n" % (ip6.ip, iface.name)

                # add interfaces to bridge
                # Make port numbers explicit so they're easier to follow in reading the script
                cfg += "## Add the interface to the bridge\n"
                cfg += (
                    "ovs-vsctl add-port ovsbr0 eth%s -- set Interface eth%s ofport_request=%d\n"
                    % (ifnum, ifnum, portnum)
                )
                portnum += 1
            cfg += "\n## Set the default device to the bridge so that it can handle where packets go\n"
            cfg += "route add -net default ovsbr0\n"
        return cfg

    @classmethod
    def get_startup(cls, node):
        """
        Provides a way to dynamically generate the startup commands from the node a service will run.
        Defaults to the class definition and can be left out entirely if not needed.

        :param node: core node that the service is being ran on
        :return: tuple of startup commands to run
        """
        return cls.startup

    @classmethod
    def get_validate(cls, node):
        """
        Provides a way to dynamically generate the validate commands from the node a service will run.
        Defaults to the class definition and can be left out entirely if not needed.

        :param node: core node that the service is being ran on
        :return: tuple of commands to validate service startup with
        """
        return cls.validate
