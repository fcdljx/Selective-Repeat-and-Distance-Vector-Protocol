# William Liang
# jl5825@Columbia.Edu
# Programming Assignment 2 - Cnnode
# CSEE 4119
# 6/24/21

from dvnode import *
from collections import defaultdict, OrderedDict
import socket
import math
import threading
import sys, os
import json
import time
import random

IP = socket.gethostbyname(socket.gethostname())

random.seed(time.time())

class Cnnode:
    def __init__(self, port):
        self.port = int(port)
        self.sendport = random.randint(1024, 65534)
        self.socket = None
        self.sendsocket = None
        self.table = defaultdict(def_value)
        self.hop = defaultdict(lambda: None)
        self.neighbors = []

        self.send_to = []
        self.receive_from = []

        self.drop = defaultdict(lambda: 0.0)
        self.acc = defaultdict(lambda: [0, 0, 0.0])

        self.isLast = False
        self.isUpdate = False
        self.notSent = True
        self.isReady = False
        self.isAck = {}

    def say(self, msg):
        t = time.time()
        print(f'[{t}]  {msg}')

    def print_table(self):
        self.say(f'Node {self.port} Routing Table')
        for node in [nodes for nodes in self.table.keys() if nodes != self.port]:
            if self.hop[node]:
                print(f'- ({self.table[node]}) -> Node {node}; Next hop -> Node {self.hop[node]}')
            else:
                print(f'- ({self.table[node]}) -> Node {node}')

    def create_and_bind(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sendsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, int(self.port)))
        self.sendsocket.bind((IP, int(self.sendport)))

    def recalculate_cost(self):
        for k,v in self.acc.items():
            v[2] = round(v[0]/v[1],2)

    def wait_and_check(self, port):
        time.sleep(0.5)
        if self.isAck[port]:
            self.acc[port][1] += 1
        else:
            self.acc[port][0] += 1
            self.acc[port][1] += 1

        self.recalculate_cost()

    def schedule_table_update(self):
        threading.Timer(5.0, self.schedule_table_update).start()
        for k,v, in self.acc.items():
            if k in self.table.keys():
                self.table[k] = v[2]

        self.tell_all(f'{self.port}%{json.dumps(self.table)}')

    def schedule_send_probe(self):
        threading.Timer(0.6, self.schedule_send_probe).start()
        for x in self.send_to:
            self.isAck[x] = False
            self.sendsocket.sendto(f'{self.port}%PROBE'.encode('utf-8'), (IP, x))
            threading.Thread(target=self.wait_and_check, args=[x]).start()

    def schedule_print_loss(self):
        threading.Timer(1.0, self.schedule_print_loss).start()
        for k, v in self.acc.items():
            self.say(f'Link to {k}: {v[1]} packets sent, '
                     f'{v[0]} packets lost, loss rate {v[2]}')

    def bellman_ford(self, new_table, source_node):
        d = self.table[source_node]
        new_table = {int(k): float(v) for k, v in new_table.items()}

        for x in new_table:
            calculated = round(min(self.table[x], d + new_table[x]), 2)
            if calculated != self.table[x]:
                self.table[x] = calculated

                if not self.hop[source_node]:
                    self.hop[x] = source_node
                else:
                    self.hop[x] = self.hop[source_node]

                self.isUpdate = True

        if self.isUpdate:
            self.notSent = False
            self.isUpdate = False
            self.print_table()
            self.tell_all(f'{self.port}%{json.dumps(self.table)}')
        else:
            self.print_table()

    def decide(self, port):
        """
        This function returns True with probability self.drop
        :return: boolean
        """
        return random.random() < float(self.drop[int(port)])

    def process_message(self, data):
        self.isReady = True

        port, table_string = data.split('%')
        port = int(port)

        if table_string == 'PROBE':
            is_fail = self.decide(port)
            if not is_fail:
                self.socket.sendto(f'{self.port}%ACK'.encode('utf-8'), (IP, int(port)))
        elif table_string == 'ACK':
            self.isAck[port] = True
        else:
            table = json.loads(table_string)

            self.say(f'Message received at Node {self.port} from Node {port}')

            self.bellman_ford(table, int(port))

            if self.notSent:
                self.tell_all(f'{self.port}%{json.dumps(self.table)}')
                self.notSent = False

    def listen_to_packet(self):
        while 1:
            data, client_address = self.socket.recvfrom(2048)
            data = data.decode('utf-8')
            self.process_message(data)

    def tell_all(self, msg):
        for neighbors in self.neighbors:
            if int(neighbors) != int(self.port):
                self.say(f'Message sent from Node {self.port} to Node {neighbors}')
                self.sendsocket.sendto(msg.encode('utf-8'), (IP, int(neighbors)))


def def_value():
    return math.inf


def initialize(node, receive, send):
    i = 0
    while i < len(receive):
        x = int(receive[i])
        node.table[x] = 0.0
        node.neighbors.append(x)
        node.drop[x] = float(receive[i+1])
        node.receive_from.append(x)

        i += 2

    for x in send:
        x = int(x)
        node.table[x] = 0.0
        node.neighbors.append(x)
        node.send_to.append((x))

    node.table[int(node.port)] = 0.0
    node.print_table()


if __name__ == '__main__':
    args = sys.argv
    node = Cnnode(sys.argv[1])

    if sys.argv[-1] == 'last':
        node.isLast = True
        args.pop()

    index = args.index('send')
    receive = args[3:index]
    send = [int(x) for x in args[index + 1:]]
    initialize(node, receive, send)

    node.create_and_bind()

    try:
        if node.isLast:
            node.notSent = False
            table_string = json.dumps(node.table)

            l = threading.Thread(target=node.listen_to_packet)
            l.daemon = True
            l.start()
            node.tell_all(f'{node.port}%{table_string}')

        l = threading.Thread(target=node.listen_to_packet)
        l.daemon = True
        l.start()

        while 1:
            if node.isReady:
                node.schedule_send_probe()
                node.schedule_table_update()
                node.schedule_print_loss()
                break

    except KeyboardInterrupt:
        node.say('goodbye!')
        sys.exit(1)
