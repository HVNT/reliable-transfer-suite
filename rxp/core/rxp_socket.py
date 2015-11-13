# from rxp_exception import RxPException
import Queue
from rxp_packet import RxPPacket
from io_loop import IOLoop
from retransmit_timer import RetransmitTimer

import socket
import logging

__author__ = 'hunt'

""" enum that describes the
connection status of a socket """


class RxPConnectionStatus:
    NONE = "no_conn"
    IDLE = "idle"
    SEND = "sending"
    RECV = "receiving"


class RxPSocket:
    def __init__(self):
        # TODO verify python version ??

        self.io_loop = IOLoop()
        self.retransmit_timer = RetransmitTimer()

        self.logger = logging.getLogger('rxp_socket')
        self.logger.setLevel(10)  # TODO set based on whether debugging enabled

        self.destination = None
        self.port_number = None

        self.dst_adr = None
        self.src_adr = None

        self.send_window = 1  # TODO appropriate defualt?
        self.recv_window = None  # TODO Packet.MAX_WINDOW_SIZE

        self.cxn_status = RxPConnectionStatus.NONE
        self.cxn_timeout = None  # TODO set

        self.seq_number = 0
        self.ack_number = 0  # ""

        self.resend_limit = 100  # TODO need? appropriate default?

        # initialize UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    """
    Takes in src address and binds UDP socket to specified port.
    Should be getting called by a client application.
    """

    def assign(self, port_number):
        if port_number:
            self.port_number = port_number

    """
    Takes in src address and binds UDP socket to specified port.
    """

    def bind(self, address):
        if address:
            self.port_number = address[1]
            self.io_loop.socket.bind(address)

    """
    For server to accept new client socket.
    """
    def accept(self):
        syn_received = False
        ack_received = False

        # NOTE: starts thread's activity. arranges for the run() method to be invoked on a separate thread of control
        self.io_loop.start()

        # wait for a syn that passes verification
        while not syn_received:
            try:
                # NOTE: 1st param blocks, 2nd is timeout (on queue.get)
                syn_packet, self.destination = self.io_loop.recv_queue.get(True, 1)
            except Queue.Empty:
                continue

            if syn_packet and self.destination:
                syn_received = self.__verify_syn(syn_packet, self.destination)

        # send SYN/ACK
        self.logger.debug('Received SYN during handshake. sending SYN/ACK to progress handshake.')
        syn_ack_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            ack_number=syn_packet.sequence_number + 1,  # use SYN recvd seq number for ACK
            ack=True,
            syn=True
        )

        self.io_loop.send_queue.put((syn_ack_packet, self.destination))
        self.seq_number += 1

        # wait for ACK from client confirming SYN/ACK received, retransmit on timeout
        while not ack_received:
            try:
                ack_packet, address = self.io_loop.recv_queue.get(True, 1)
            except Queue.Empty:  # TODO handle frequency of packet being sent..
                self.logger.debug('Timed out waiting on ack during handshake. Retransmitting SYN/ACK.')
                self.io_loop.send_queue.put((syn_ack_packet, self.destination))
                continue
            if ack_packet and address:
                # TODO checksum?
                ack_received = self.__verify_ack(ack_packet, address, syn_ack_packet.seq_number)
                if ack_received:
                    self.logger.debug('Received ACK during handshake. Client socket accepted')

    """
    For client to attempt to connect to a server.
    """
    def connect(self, dst_adr):
        self.destination = dst_adr
        syn_ack_received = False

        self.io_loop.start()

        # send SYN
        self.logger.debug('Sending SYN to initiate handshake.')
        syn_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.seq_number,
            syn=True
        )

        self.io_loop.send_queue.put((syn_packet, self.destination))
        self.seq_number += 1

        # wait for SYN/ACK, retransmit on timeout
        while not syn_ack_received:
            try:
                syn_ack_packet, address = self.io_loop.recv_queue.get(True, 1)
            except Queue.Empty:
                self.logger.debug('Timed out waiting on SYN/ACK during handshake. Retransmitting SYN.')
                self.io_loop.send_queue.put((syn_packet, self.destination))
                continue

            if syn_ack_packet and address:
                syn_ack_received = self.__verify_syn_ack(syn_ack_packet, address, syn_packet.seq_number)
                if syn_ack_received:
                    self.logger.debug('Received SYN/ACK during handshake.')

        # send ACK
        self.logger.debug('Received SYN/ACK during handshake. sending ack to finish handshake.')
        ack_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            ack_number=syn_ack_packet.sequence_number + 1,
            seq_number=self.seq_number,
            ack=True
        )
        self.io_loop.send_queue.put((ack_packet, self.destination))
        self.seq_number += 1



        #
        #
        # def listen(self):
        #
        #
        # def accept(self):
        #
        #

        #
        #
        # def recv(self):
        #
        #
        # def close(self):

    def send(self, msg):
        start = 0
        payload_size = 512
        packets = []

        # chunk data into packets
        while start < len(msg):
            if start + payload_size <= len(msg):
                payload = msg[start: start + payload_size]
            else:
                payload = msg[start:]

            data_packet = RxPPacket(
                self.port_number,
                self.destination[1],
                seq_number=self.seq_number,
                payload=payload
            )
            packets.append(data_packet)
            self.sequence_number += 1
            start += payload_size

        terminator_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.sequence_number
        )

    # def _send_control_packet(self):



    def __verify_syn(self, packet, address):
        return address == self.destination and packet.syn

    def __verify_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_syn_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.syn and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_fin_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.fin and packet.ack and packet.ack_number - 1 == sequence_number
