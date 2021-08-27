# Programming Assignment 2 - William Liang (jl5825)

This assignment implements the Selective Repeat protocol and Distance Vector protocol using Python3.
The implement includes three parts: srnode.py, dvnode.py, and cnnode.py. 

## 💫 Quick Start


All three of srnode.py, dvnode.py, and cnnode.py is built entirely using tools that come with Python3.6 
with no externally installed libraries to make the testing and running easy. To run the program, simply
follow the steps below. 

<strong>srnode.py</strong>

srnode.py implements the selective repeat protocol between one sending node and another receiving node. 
To emulate an actual network environment where packets can be dropped, srnode.py supports two modes of 
operation: deterministic and probabilistic. 

To run the program in deterministic mode where the node drops one out of n packets, issue the following
command: 

```bash
python3 srnode.py <self-port> <peer-port> <window-size> -d <value-of-n>
```

To run the program in probabilistic mode where each packet is dropped with a probability of p, issue the following
command: 

```bash
python3 srnode.py <self-port> <peer-port> <window-size> -p <value-of-p>
```

<strong> dvnode.py </strong>

dvnode.py implements the distance vector routing protocol using the Bellman-Ford equation. To run the program,
use the command:
<br>
```bash
 python3 dvnode.py <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]
 ```
The [last] symbol is optional at the end. It is used to indicate the last node being initiated in the network which is
the first node to start the convergence process.
<br>

<strong> cnnode.py </strong>

cnnode.py combines the selective repeat protocol and the distance vector routing algorithm
to simulate a network environment with dynamic link costs. To run the program:
```bash
 python3 cnnode.py <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... <neighborM-port>

<loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... <neighborN-port> [last]
 ```


## ⚙ Selective Repeat Implementation   
### `Data Structures `
I use a dictionary of { Seq No: Packet } as the sender buffer and the receiver buffer. 
To prevent excessive retransimission of packets due to the overlap between windows, 
I used a set to indicate all packets that have already been transmitted. When the window 
updates, these packets will not be sent again if they were previously 

## ⚙ Distance Vector Implementation   
### `Data Structures `
I use DefaultDict to implement the distance table and the hop table; together they form 
the routing table. For each dictionary, the key is the destination node from the current
node itself, and the value is the distance or the next hop to the destination, respectively.
For the distance table, default value is infinity if the node is not
a neighbor. For hop table, the default value is None, which means direct link to the node without
hopping. The rest of the implementation follows the distance vector protocol.

### `Convergence`
The program will stop executing once the distance vectors converge to equilibrium. This is 
implemented by issuing the blocking listening thread each time the node is run. If the system
is at equilibrium, no information is exchanged among the nodes, and thus the listening thread
will block the execution of all nodes.

## ⚙ Combination Implementation   
### `Data Structures `
I use array to store the nodes to which the current node will send probe packets to, and the nodes
it receives packet from.

I use DefaultDict to store the parameters for dropping probability and the accumulated 
packet number. For the node.drop table, it has the structure {port number: drop rate} to indicate 
the probability of dropping a packet received from the port number. For the node.acc table, 
it has the structure of {port number: [#packet dropped, #total packet, loss rate] } 

### `Scheduling and Link Cost`
Scheduling of events, such as sending a probe packet every n seconds, is implemented with 
the Threading module using timer. The system is tested to show that the link costs vary but
will converge to the indicated loss probability after a sufficient amount of time (usually around 
1 minute). The system itself has no information of the loss probability parameter when constructing 
the link costs. All costs are calculated strictly by the sender node.




## 📖 Project Wiki

 ### 🔧 Known Issue

`` Lack of poisoned reverse in cnnode.py``

Poisoned reverse is not implemented in cnnode.py. Consequently, because the link costs 
are initiated to be 0.0 everywhere, the link cost from a recepient node to a sender node
may not be updated according to the Bellman-Ford equation since the sender does not drop
ACK packets. In another word, the link cost is not bidirectional. However, this implementation
is still arguably consistent with the description of part 4, specifically with regard to Figure 4
where the link costs are shown above links with clear directions marked.



<p align="center">
    ~ Thank You ~
</p>