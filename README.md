<img alt="Logo" height="400" src="https://github.com/flaat/TaskMAS_test_framework/blob/master/img/TaskMAS.png" width="400"/>

# AA-UAV test framework

## Goals

This package has been developed in order to allow fixed path communication in ad-hoc mesh network to tests the _AA-UAV_ framework in different real-world scenarios.
The protocol used is B.A.T.M.A.N. [^1], a layer 2 protocol for ad-hoc network. Our goal is to force packets through a pre-fixed path in the network.


## Requisites
- **Python3**  
- **sshpass**[^2]  
- **fuser**[^3]  
- **socket** (python)

- **B.A.T.M.A.N.** ad-hoc network up and running  

## Implementation details

The python script should run on each device participating in the network. It can run in 3 modes: **relay, sender, receiver**.  
The relay mode sets up a server to receive the data sent by another relay or a sender. It does resend data immediately toward the next hop.
The sender mode try to establish a connection with the next hop in the chain. When the connection is established the sender start to send the data towards the next node. The receiver mode instead sets up a server to receive the data.  
All the nodes can operate in all the modes at the same time, it is sufficient to start another session.  
**It is important to have at least 2 nodes: a source and a destination**. You can add as many relay as you want.


## Usage example
In order to make the script works you must download the package into each device connected to the network.  
To run a test you need to execute the script _outdoor_test.py_. **Before launch the script** it is very important to properly modify the _config.py_ file in the 
utilities folder, (for more details see docs) and correctly synchronize the time between nodes (running the script _sync\_nodes.sh_ in the folder  ```../node_sync ```)

In the image below there is a possible scenario with two different targets (warning signal) and 4 drones. The .json configuration for this scenario is
 ``` ../src/network_configs/outdoor_network_config/TaskMAS_example_config_4_targets.json```


<img alt="Config_example" height="320" src="https://github.com/flaat/AA-UAV-Outdoor/blob/master/img/config_example.png" width="300"/>

The tests run as follows:
First of all, a configuration provided by the optimizer is read from the configs available, then it is coverted in a framework-friendly format.
For each test repetition all the connections are initialized sequentially. Finally, a thread waits for all the results from the nodes and put them into
a dictionary.

[^1]: https://www.open-mesh.org/projects/open-mesh/wiki/BATMANConcept
[^2]: https://linux.die.net/man/1/sshpass
[^3]: https://linux.die.net/man/1/fuser
