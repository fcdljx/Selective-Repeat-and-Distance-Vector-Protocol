# William Liang
# jl5825@Columbia.Edu
# Programming Assignment 2 - Distance Vector Protocol
# CSEE 4119
# 6/24/21

from collections import defaultdict
import socket
import math
import threading
import sys, os
import json
import time
import random

IP = socket.gethostbyname(socket.gethostname())


def def_value():
    return math.inf


def initialize(node):
    if sys.argv[-1].lower() == 'last':
        node.isLast = True
        for i in range(2, len(sys.argv) - 1):
            if i % 2 == 0:
                node.table[int(sys.argv[i])] = None
                node.neighbors.append(int(sys.argv[i]))
            else:
                node.table[int(sys.argv[i - 1])] = float(sys.argv[i])

    else:
        for i in range(2, len(sys.argv)):
            if i % 2 == 0:
                node.table[int(sys.argv[i])] = None
                node.neighbors.append(int(sys.argv[i]))
            else:
                node.table[int(sys.argv[i - 1])] = float(sys.argv[i])

    node.table[int(node.port)] = 0.0
    node.print_table()


class Dvnode:
    def __init__(self, port):
        self.port = int(port)
        self.sendport = random.randint(1024, 65534)
        self.socket = None
        self.sendsocket = None
        self.table = defaultdict(def_value)
        self.hop = defaultdict(lambda: None)
        self.neighbors = []

        self.isLast = False
        self.isUpdate = False
        self.notSent = True

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

    def bellman_ford(self, new_table, source_node):
        d = self.table[source_node]
        new_table = {int(k): float(v) for k,v in new_table.items()}

        for x in new_table:
            calculated = round(min(self.table[x], d+new_table[x]), 2)
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

    def process_message(self, data):
        port, table_string = data.split('%')
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


if __name__ == '__main__':
    node = Dvnode(sys.argv[1])
    node.create_and_bind()
    initialize(node)
    try:
        if node.isLast:
            node.notSent = False
            table_string = json.dumps(node.table)
            l=threading.Thread(target=node.tell_all, args=[f'{node.port}%{table_string}'])
            l.daemon = True
            l.start()
            node.listen_to_packet()
        else:
            node.listen_to_packet()

    except KeyboardInterrupt:
        node.say('goodbye!')
        sys.exit(1)
