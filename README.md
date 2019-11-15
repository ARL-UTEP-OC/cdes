# The Cybersecurity Deception and Experimentation System (CDES)
## Table of Contents
- [The Cybersecurity Deception and Experimentation System (CDES)](#the-cybersecurity-deception-and-experimentation-system-cdes)
  - [Table of Contents](#table-of-contents)
    - [Description](#description)
    - [Limitations](#limitations)
    - [Installation](#installation)
        - [Requirements](#requirements)
        - [Linux](#linux)
    - [Run a Sample Scenario](#run-a-sample-scenario)
    - [Create a New Scenario](#create-a-new-scenario)

### Description
CDES is an extension to the Common Open Research Emulator. The main purpose of this system is to enable conditional connections among nodes in emulated networks. 

This system works by leveraging external calls to the CORE-daemon through use of coresendmsg as well the session-deployed.xml file that is generated by the CORE daemon. 

This system is based on the following node constructs:
* Conditional Connection Decision Node (CC_Decision Node): An address-less node that runs logic for determining which connections should be enabled/disabled based on three subcomponents: the Monitor, Trigger, and Swapper

* Conditional Connection Node (CC_Node): A node that is connected to the CC_Decision Node. The connection to this node is dependent on the underlying logic defined in the Decision Node

* Conditional Connection Gateway (CC_GW): A node that is also connected to the CC_Decision Node, but whose connection is connected throughout the emulation. This node may be used for more complex swapping behavior, e.g., using routes, software defined networking, etc. to redirect traffic.

### Limitations

### Installation
CIT-GEN has been tested on:
* Ubuntu 16.04 LTE (64-bit)
* CORE (4.7+) 

##### Requirements
* [Python 2.x ](https://www.python.org/download/releases/2.7/)
* [CORE v4.7+](https://github.com/coreemu/core/)
* [pyparser](https://pypi.org/project/pyparser/)

##### Linux
Clone the source and then cd into the directory:
```
git clone https://github.com/raistlinJ/cdes
cd cdes
```
Install the pyparser dependency
```
pip install pyparser
```

Copy the custom services into your CORE services folder:

For example, 
```
cp CORE_configs/myservices /home/username/.core/myservices -rf

cp CORE_configs/myconfigs/nodes.conf /home/username/.core/nodes.conf -rf
```

Now enable the custom services to run by adding the following line to /etc/core/core.conf
```
custom_services_dir = /home/username/.core/myservices
```

To run the sample scenario, follow the steps in [Run a Sample scenario](#run-a-sample-scenario).

### Run a Sample Scenario
The provided sample scenario consists of a decision node and two conditional nodes. This scenario simply switches between the two nodes (indicated by the blue and yellow link in the GUI). 

The following are the steps for staring the sample:
Run the Core Daemon if it is not yet started
```
sudo /etc/init.d/core-daemon start
```
Open the scenario in the CORE-GUI
```
core-gui sample/scenario/CC_NodeTest.imn
```
Lastly, press the Start button on the GUI.

At this time, you should see the link between the CC Decision Node and the CC Nodes toggle from blue (connected) to yellow (not connected) in 10 second intervals.

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

4. Load CDES into the CORE scenario by 
- Click on Session -> Hooks
- Add a new runtime hook and have it load the cdes_loader.sh file in the folder with the cdes source

5. Run the scenario by click on the play button

You should now see the links between the cdes1 and cdes2 nodes alternating blue and yellow every 10 seconds. Try to ping from r1 -> h1 and r1 -> r2 and notice that the connectivity is mutually exclusive.
