# The Cybersecurity Deception Experimentation System (CDES)
## Table of Contents

- [Description](#description)
- [Limitations](#limitations)
   - [Issues related to CORE](#issues-related-to-core)
- [Installation](#installation)
   - [Requirements](#requirements)
   - [Linux](#linux)
- [Run a Sample Scenario](#run-a-sample-scenario)
- [Run a Sample with Suricata](#run-a-sample-with-suricata)
- [Create a New Scenario](#create-a-new-scenario)
- [Troubleshooting](#troubleshooting)

### Description
CDES is an extension to the Common Open Research Emulator. The main purpose of this system is to enable conditional connections among nodes in emulated networks. 

This system works by leveraging external calls to the CORE-daemon through use of coresendmsg as well the session-deployed.xml file that is generated by the CORE daemon. 

This system is based on the following node constructs:
* Conditional Connection Decision Node (CC_Decision Node): An address-less node that runs logic for determining which connections should be enabled/disabled based on three subcomponents: the Monitor, Trigger, and Swapper

### Limitations
* For CDES to work correctly, only a single instance of CORE and a single session is allowed. 
* When using the default Trigger, there is a short time at the start of the emulation when all conditional links will be enabled (roughly 3-4 seconds).

#### Issues related to CORE
* If a hook script contains invalid characters (like ") it will work, but will not be read/loaded properly when the .imn file is loaded.

  This becomes an issue especially when including suricata rules, since they usually contain the " character. The workaround is to recreate the suricata generation hook script (and copy/paste the rules into the hook script) every time the scenario file is loaded.
* With CORE 6.2.0, the coresendmsg handler for link (and others, like node) is broken, therefore, the link color will not change when the "swap" occurs

### Installation
CIT-GEN has been tested on:
* Ubuntu 16.04 LTE (64-bit)
* CORE (7.2+) 

##### Requirements
* [Python 3.6 ](https://www.python.org/downloads/release/python-369/)
* [CORE >= v7.2+] 
* Additional python Modules as specified in requirements.txt

##### Linux
Clone the source and then cd into the directory.

Install the dependencies
```
pip3 install -r requirements.txt
```

Copy the custom services into your CORE services folder:

For example, 
```
cp CORE_configs/myservices/* /home/username/.core/myservices/ -rf

cp CORE_configs/myconfigs/nodes.conf /home/username/.core/nodes.conf -rf
```

Now enable the custom services to run by adding the following line to /etc/core/core.conf
```
custom_services_dir = /home/username/.core/myservices
```

To run the sample scenario, follow the steps in [Run a Sample scenario](#run-a-sample-scenario).

### Run a Sample Scenario
The provided sample scenario consists of a decision node and two conditional nodes. This scenario simply switches between the two nodes (indicated by the blue and yellow link in the GUI). 

1. Run the Core Daemon if it is not yet started
```
sudo /etc/init.d/core-daemon restart
```
2. Open the scenario in the CORE-GUI
```
core-gui sample/scenario/CC_NodeTest.imn
```
3. Click on Session -> Hooks
- Modify the runtime hook (click on the wrench icon) and update the path with the directory where you have the cdes source as shown below.
```
python3 /home/username/cdes/cdes_loader.py &
```

4. Lastly, press the Start button on the GUI.

At this time, you should see the link between the CC Decision Node and the CC Nodes toggle from blue (connected) to yellow (not connected) in 60 second intervals.

Several other samples are available. They are located in the samples/scenario/ directory.

### Run a Sample with Suricata
This scenarios is an extension to the simple scenario, showing how CDES can be used to read suricata alerts and execute a trigger based on those alerts. 
*Note: For this sample to work, ensure that you have suricata installed.* 

1. On Ubuntu 16+, you can install suricata by running the following.
```
sudo apt-get install suricata
```
2. Run the Core Daemon if it is not yet started
```
sudo /etc/init.d/core-daemon restart
```
3. Open the scenario in the CORE-GUI
```
core-gui sample/scenario/CC_NodeTest_suricata.imn
```
4. Click on Session -> Hooks
- Modify the startcdes_runtime_hook.sh hook (click on the wrench icon) and update the path with the directory where you have the cdes source as shown below.
```
python3 /home/username/cdes/cdes_loader.py &
```
There are 3 other hooks (no need to modify these) that accomplish the following:

- suricatarule_instantiation_hook.sh: Creates a suricata rule that will generate an alert on any ICMP packets originating from the untrusted node (10.0.1.10). This rule written to /tmp/suricata-out/rules/custom.rules. 
- suricatastart_runtime_hook.sh: starts an instance of suricata using the rules created with the suricata_rule_hook.sh hook. Alerts are written to /tmp/suricata-out/fast.log
- suricatastop_shutdown_hook.sh: Stops the instance of suricata when the scenario is stopped.

5. Next, press the Start button on the GUI.

6. Double-click on the node labeled outclient. When the terminal appears, enter the following command to send 21 ICMP echo requests to a node in the Legitimate Network.
```
ping 10.0.1.1 -c 21
```
At this time, you should see the link between the CC Decision Node toggle to the Honey Network. Recall that a blue link indicates *connected* and yellow indicates *not connected*.

The corresponding suricata alerts are located in /tmp/suricata-out/fast.log

Several other samples are available. They are located in the samples/scenario/ directory.

### Create a New Scenario
Follow these steps to create and run a simple cdes scenario.

1. Start CORE, click on the side bar and add the following nodes to the canvas
- router x 2 (**r1**, **r2**)
- PC (**p1**)
- cc_node x 2 (**cn1**, **cn2**)
- ethernet switch (**cdes1**)
- host x 1 (**h1**)

2. Connect the nodes as follows
- r1 -> cdes1
- cdes1 -> cn1
- cdes1 -> cn2
- cn1 -> r2
- cn1 -> h1

3. Right click on the following nodes and select these services
- cdes1: **CC_DecisionNode** (Modify the MyMonitor.sh and MyTrigger.py to define custom behavior)
- cn1 and cn2: **CC_Node**

4. Load CDES into the CORE scenario by doing the following
- Click on Session -> Hooks
- Add a new runtime hook and have it load the cdes_loader.py at startup, e.g., add the line
```
python3 /home/username/cdes/cdes_loader.py &
```

5. Run the scenario by clicking on the play button

You should now see the links between the cdes1 and cdes2 nodes alternating blue and yellow every 60 seconds. Try to ping from r1 -> h1 and r1 -> r2 and notice that the connectivity is mutually exclusive.

### Troubleshooting

The CDES logs will be located in the temporary directory associated with the current CORE session.
```
/tmp/pycore.<session-number>/runtime_hook.sh.log
```
