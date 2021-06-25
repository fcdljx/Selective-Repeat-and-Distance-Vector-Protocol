# William Liang
# jl5825@Columbia.Edu
# Programming Assignment 2 - Selective Repeat Protocol
# CSEE 4119
# 6/24/21

from collections import OrderedDict
import socket
import threading
import sys, os
import time
import random

IP = socket.gethostbyname(socket.gethostname())


class Srnode:
    global IP

    def __init__(self, selfPort, peerPort, window, drop):
        self.self_port = int(selfPort)
        self.peer_port = int(peerPort)
        self.window = int(window)
        self.drop = drop
        self.mode = None
        self.socket = None

        self.buffer = OrderedDict()
        self.rcvBuffer = OrderedDict()
        self.acked = OrderedDict()

        self.sent = set()

        self.base = 0
        self.rcvBase = 0

        self.acc = 0
        self.dropped = 0

    def print_line(self, msg):
        """
        This function prints a line of message on the screen with associated timestamp as
        a floating point number expressed in seconds since the epoch

        :param msg: str
        :return: None
        """

        t = time.time()
        print(f'[{t}]  {msg}')

    def decision (self):
        """
        This function returns True with probability self.drop
        :return: boolean
        """
        return random.random() < float(self.drop)

    def create_and_bind(self):
        """
        This function creates the sending and listening port of the sockets and bind them to the
        IP address.
        :return: None
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP, int(self.self_port)))
        self.print_line(f'Successfully created node at {IP} port {self.self_port}')

    def ack(self, seq, address):
        """
        This function sends an ACK of sequence number seq to the address
        :param seq: int
        :param address: tuple of (IP, Port)
        :return: None
        """
        self.socket.sendto(f'{seq}%ACK'.encode('utf-8'), address)

    def process_packet(self, data, address):
        """
        This function processes the packet received by the node on its listening port.

        Packet Type:
        There are three types of possible packets received depending on the node. For
        the sender, it can receive ACK; for the receiver, it can receive packets of data
        or END packet which specifies the end of a message.

        Buffer Management:
        When an ACK is received, the associated packet is deleted in the buffer.

        Window Movement:
        For the sender window, the function only updates the window when the corresponding
        ACK is received *IN ORDER*.

        :param data: str
        :param address: tuple(IP, PORT)
        :return:
        """
        seq = int(data[0:data.find('%')])
        content = data[data.find('%')+1:]

        if content == 'ACK':
            self.acked[seq] = True
            try:
                del self.buffer[seq]
            except KeyError:
                self.print_line(f'[Summary] {self.dropped}/{self.acc} ACKs dropped, loss rate = {self.dropped/self.acc}')
                os._exit(1)
            if seq != self.base:
                pass
            else:
                self.update_window(seq)

        elif content == 'END':
            self.ack(seq, address)
            msg = ''
            for i in range(0, seq):
                msg += self.rcvBuffer[i]
            self.print_line(f'Message received: {msg}')
            self.print_line(f'[Summary] {self.dropped}/{self.acc} packets dropped, loss rate = {self.dropped / self.acc}')

        else:
            if seq in self.rcvBuffer.keys():
                self.print_line(f'duplicate packet {seq} {content} received, discarded')
                self.ack(seq, address)
            else:
                if seq != self.rcvBase:
                    self.print_line(f'packet{seq} {content} received out of order, buffered')
                    self.rcvBuffer[seq] = content
                    self.ack(seq, address)
                else:
                    self.rcvBuffer[seq] = content
                    self.ack(seq, address)

                    while self.rcvBase in self.rcvBuffer.keys():
                        self.rcvBase += 1
                    self.print_line(f'packet{seq} {content} received')
                    self.print_line(f'ACK{seq} sent, window starts at {self.rcvBase}')

    def decide_process(self, data, address):
        """
        This function decides whether to pass the received packet to upper layer processing or not.
        The actual decision depends on the mode of operation.

        :param data: str
        :param address: tuple(IP, PORT)
        :return:
        """

        seq = int(data[0:data.find('%')])
        content = data[data.find('%')+1:]

        if self.mode == 'D':
            if int(self.drop) == 0:
                self.acc += 1
                self.process_packet(data, address)
            else:
                if content == 'ACK':
                    self.acc += 1
                    if self.acc % int(self.drop) == 0:
                        self.print_line(f'ACK{seq} dropped')
                        self.dropped += 1
                    else:
                        self.process_packet(data, address)
                else:
                    self.acc += 1
                    if self.acc % int(self.drop) == 0:
                        self.print_line(f'packet{seq} {content} dropped')
                        self.dropped += 1
                    else:
                        self.process_packet(data, address)

        if self.mode == 'P':
            decision = self.decision()
            self.acc += 1

            if decision:
                self.dropped += 1
                self.print_line(f'{seq}{content} dropped')
            else:
                self.process_packet(data, address)

    def listen_to_packet(self):
        """
        This function Listens for incoming packets on the listening port and
        create a separate listening Thread for each packet received.

        :return:
        """
        while 1:
            data, client_address = self.socket.recvfrom(2048)
            data = data.decode('utf-8')
            threading.Thread(target=self.decide_process, args=[data, client_address]).start()

    def wait_and_check(self, packet, seq):
        """
        Implements Timeout Thread. If by the end of the timout the correct ACK is
        not received (packet lost), it will retransmit with the same seq number.

        :param packet: str
        :param seq: int
        :return:
        """
        time.sleep(0.5)
        if self.acked[seq]:
            pass
        else:
            self.print_line(f'packet{seq} timeout, resending')
            self.send_packet(packet, seq)

    def update_window(self, seq):
        """
        This function updates the sender window to start at 1 past next seq number
        where an ACK is received in order.

        :param seq: int
        :return:
        """
        next_seq = None
        for key, value in self.acked.items():
            if not value:
                next_seq = key
                break

        if not next_seq:
            next_seq = max(self.acked.keys())
            self.print_line(f'ACK{seq} received, window starts at {next_seq}')
            self.acked[next_seq] = False
            self.send_packet('END', next_seq)
        else:
            self.base = next_seq
            self.print_line(f'ACK{seq} received, window starts at {self.base}')
            self.send()

    def send_packet(self, packet, seq):
        """
        Implements the Send Thread. Packs the data for transmission and starts a separate timer
        for each data packet sent.

        :param packet: str
        :param seq: int
        :return:
        """
        content = packet
        packet = f'{seq}%{packet}'
        if content != 'END':
            self.print_line(f'packet{seq} {content} sent')
        self.socket.sendto(packet.encode('utf-8'), (IP, self.peer_port))
        threading.Thread(target=self.wait_and_check, args=[content, seq]).start()

    def send(self):
        """
        Send all packets within the sender window and mark them as already sent to prevent
        window overlap retransmission.
        :return:
        """
        for i in range(self.base, self.base+self.window):
            if i not in self.sent:
                self.sent.add(i)
                try:
                    self.send_packet(self.buffer[i], i)
                except KeyError:
                    pass

    def get_command(self):
        """
        Get command from the user and prepare the sender buffer and ACK table.
        :return:
        """
        while 1:

            command = input('node> ')
            if not command:
                continue
            command_header = command.lstrip()[0:4]
            msg = command[5:]

            if command_header.lower() != 'send':
                self.print_line('please use only send command')
                continue
            else:
                seq = 0
                for letter in msg:
                    self.buffer[seq] = letter
                    self.acked [seq] = False
                    seq += 1
                self.acked[seq] = True
                self.send()


if __name__ == '__main__':
    node = Srnode(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[5])
    if sys.argv[4] == '-d':
        node.mode = 'D'
    elif sys.argv[4] == '-p':
        node.mode = 'P'

    node.create_and_bind()

    l = threading.Thread(target=node.listen_to_packet)
    l.daemon = True
    l.start()

    try:
        node.get_command()
    except KeyboardInterrupt:
        node.print_line('Connection terminated')
        os._exit(1)
