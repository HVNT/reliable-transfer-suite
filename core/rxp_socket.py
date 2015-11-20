# from rxp_exception import RxPException
from io_loop import IOLoop
from rxp_packet import RxPPacket
from sliding_window import SlidingWindow
from retransmit_timer import RetransmitTimer

import Queue
import socket
import logging
import time

__author__ = 'hunt'

""" enum that describes the
connection status of a socket """

logging.basicConfig()


class RxPConnectionStatus:
    NONE = "no_conn"
    IDLE = "idle"
    SEND = "sending"
    RECV = "receiving"


class RxPSocket:
    def __init__(self, window_size=10, debugging=False):
        # TODO verify python version ??
        self.window_size = window_size
        self.io = IOLoop()

        # TODO should we put on the io_loop? so it can just keep track of itself?
        self.cxn_status = RxPConnectionStatus.NONE

        self.retransmit_timer = RetransmitTimer()

        # for python module logging msgs.. enable if debugger param toggled
        self.logger = logging.getLogger('rxp_socket')
        self.logger.setLevel(0)
        if debugging:
            self.logger.setLevel(10)

        self.destination = None
        self.port_number = None

        self.seq_number = 0
        self.ack_number = 0  # ""

        self.resend_limit = 100  # TODO need? appropriate default?

    """
    Takes in src address and binds UDP socket to specified port.
    """

    def bind(self, address):
        if address:
            self.port_number = address[1]
            self.io.socket.bind(address)

    """
    For server to accept new client socket.
    """
    # TODO handle SYN flooding
    def accept(self):
        syn_received = False
        ack_received = False

        # NOTE: starts thread's activity. arranges for the run() method to be invoked on a separate thread of control
        self.io.start()

        # wait for a syn that passes verification
        while not syn_received:
            # TODO self.cxn_status
            try:
                # NOTE: 1st param blocks, 2nd is timeout (on queue.get)
                self.logger.debug('About to attempt to receive a SYN packet.')
                syn_packet, self.destination = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                continue

            if syn_packet and self.destination:
                syn_received = self.__verify_syn(syn_packet, self.destination)

        # send SYN/ACK
        self.logger.debug('Received SYN during handshake; sending SYN/ACK to progress handshake.')
        syn_ack_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            ack_number=syn_packet.seq_number + 1,  # use SYN recvd seq number for ACK
            ack=True,
            syn=True
        )

        # TODO self.cxn_status
        self.io.send_queue.put((syn_ack_packet, self.destination))
        self.seq_number += 1

        # wait for ACK from client confirming SYN/ACK received, TODO retransmit on timeout
        while not ack_received:
            try:
                ack_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                self.logger.debug('Timed out waiting on ack during handshake; retransmitting SYN/ACK.')
                syn_ack_packet.frequency += 1
                syn_ack_packet.update_checksum()
                # TODO retransmit timer, time out
                self.io.send_queue.put((syn_ack_packet, self.destination))
                continue

            if ack_packet and address:
                ack_received = self.__verify_ack(ack_packet, address, syn_ack_packet.seq_number)
                if ack_received:
                    self.logger.debug('Received ACK during handshake; client socket accepted')

        self.cxn_status = RxPConnectionStatus.IDLE

    """
    For client to attempt to connect to a server.
    """

    def connect(self, dst_adr):
        self.destination = dst_adr
        syn_ack_received = False

        self.io.start()

        # send SYN
        self.logger.debug('Sending SYN to initiate handshake.')
        syn_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.seq_number,
            syn=True
        )

        self.io.send_queue.put((syn_packet, self.destination))
        self.seq_number += 1

        # wait for SYN/ACK
        while not syn_ack_received:
            try:
                syn_ack_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                self.logger.debug('Timed out waiting on SYN/ACK during handshake; retransmitting SYN.')
                syn_packet.frequency += 1
                syn_packet.update_checksum()
                # TODO retransmit timer, time out
                self.io.send_queue.put((syn_packet, self.destination))
                continue

            if syn_ack_packet and address:
                syn_ack_received = self.__verify_syn_ack(syn_ack_packet, address, syn_packet.seq_number)
                if syn_ack_received:
                    self.logger.debug('Received SYN/ACK during handshake.')

        # TODO resending ACK if another SYN/ACK is received? AKA server never gets the clients ACK
        # send ACK
        self.logger.debug('Sending ACK to finish handshake.')
        ack_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            ack_number=syn_ack_packet.seq_number + 1,
            seq_number=self.seq_number,
            ack=True
        )
        self.io.send_queue.put((ack_packet, self.destination))
        self.seq_number += 1

        self.cxn_status = RxPConnectionStatus.IDLE

    """
    For client or server to send a msg. The 'kill_packet' is used
    to inform client and server can know when we done sending.
    """
    # TODO get window size available from client and respond appropriately
    def send(self, msg):
        floor = 0
        payload_size = 512
        packets = []

        # chunk data into packets
        while floor < len(msg):
            if floor + payload_size <= len(msg):
                payload = msg[floor: floor + payload_size]
            else:
                payload = msg[floor:]

            data_packet = RxPPacket(
                self.port_number,
                self.destination[1],
                seq_number=self.seq_number,
                payload=payload
            )
            packets.append(data_packet)
            self.seq_number += 1
            floor += payload_size

        kill_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.seq_number
        )
        packets.append(kill_packet)  # put that shit at the end after we've added all the other packets
        self.seq_number += 1
        self.kill_seq_number = self.seq_number
        self.kill_sent_number = 0  # TODO need?

        self.logger.debug('Placing packets in window to be sent now...')
        window = SlidingWindow(packets, self.window_size)
        time_sent = time.time()
        time_remaining = self.retransmit_timer.timeout

        for data_packet in window.window:
            self.io.send_queue.put((data_packet, self.destination))

        while not window.is_empty():
            try:
                ack_packet, address = self.io.recv_queue.get(True, time_remaining)
            except Queue.Empty:
                # timeout, currently GO-BACK-N TODO refactor to SR
                self.logger.debug('Timed out waiting for ack during data transmission; retransmitting window.')
                time_sent = time.time()
                time_remaining = self.retransmit_timer.timeout

                for data_packet in window.window:
                    if self.kill_seq_number == data_packet.seq_number:
                        self.kill_sent_number += 1
                        if self.kill_sent_number > 3:  # if retransmitted the
                            self.logger.debug('Unable to end connection; killing now.')
                            return

                    data_packet.frequency += 1
                    # TODO recalc checksum now that frequency increased
                    self.io.send_queue.put((data_packet, self.destination))
                continue

            # if still getting SYN/ACK, retransmit ACK
            if self.__verify_syn_ack(ack_packet, address, 1):
                self.logger.debug('Received SYN/ACK retransmission; retransmitting ACK.')
                ack_packet = RxPPacket(
                    self.port_number,
                    self.destination[1],
                    ack_number=ack_packet.seq_number + 1,
                    seq_number=2,
                    ack=True
                )
                self.io.send_queue.put((ack_packet, self.destination))
                time_remaining = 0

            # if first packet in pipeline is acknowledged, slide the window
            elif self.__verify_ack(ack_packet, address, window.window[0].seq_number):
                self.retransmit_timer.update(ack_packet.frequency, time.time() - time_sent)
                self.logger.debug('Updated retransmit timer; timeout is now ' + str(self.retransmit_timer.timeout))

                window.slide()

                # TODO confusing
                if not window.has_room():
                    self.io.send_queue.put((window.window[-1], self.destination))
                    self.seq_number += 1
                    # print "executing"

            # otherwise, update time remaining
            else:
                time_remaining -= time.time() - time_sent / 4  # decay
                if time_remaining < time.time():
                    time_remaining = .5
                self.logger.debug('Trash packet receive; time remaining before timeout: ' + str(time_remaining))

    # TODO communicate window size available.. keep track of window size available..
    def recv(self):
        kill_received = False
        read_kill = False
        packets = {}
        frequencies = {}

        # until connection is closed, read data
        while not read_kill:
            try:
                data_packet, address = self.io.recv_queue.get(True, 1)
                data_packet.print_packet()
            except Queue.Empty:
                continue

            if address == self.destination:
                # TODO just get frequency of data_packet ??
                if frequencies.get(data_packet.seq_number):
                    frequencies[data_packet.seq_number] += 1
                else:
                    frequencies[data_packet.seq_number] = 1
                # print data_packet.seq_number

                packets[data_packet.seq_number] = data_packet
                self.logger.debug('Sending ack during data transfer.')
                ack_packet = RxPPacket(
                    self.port_number,
                    self.destination[1],
                    seq_number=self.seq_number,
                    ack_number=data_packet.seq_number + 1,
                    frequency=frequencies[data_packet.seq_number],
                    ack=True
                )
                self.io.send_queue.put((ack_packet, self.destination))
                self.seq_number += 1

                if data_packet.is_killer():
                    kill_received = True
                    self.logger.debug('Kill packet detected.')

                if kill_received:
                    sorted_pkeys = sorted(packets.keys())
                    read_kill = sorted_pkeys == range(sorted_pkeys[0], sorted_pkeys[0] + len(sorted_pkeys))

        # for key in packets.keys():
        #    print packets[key].payload
        # print "Packet.keys length: " + str(len(packets.keys()))

        return ''.join(map(lambda packet: packet.payload, map(lambda sequence_number: packets[sequence_number], sorted(packets.keys()))))

    def close(self):
        fin_ack_received = False

        self.logger.debug('Sending FIN to initiate close.')
        fin_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.seq_number,
            fin=True
        )
        self.io.send_queue.put((fin_packet, self.destination))
        self.seq_number += 1

        # TODO handle when just fin received.. more than this one case.. what if they both FIN at the same time..
        while not fin_ack_received:
            try:
                fin_ack_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                self.logger.debug('Timed out waiting for FIN/ACK during close; closing...')
                break

            if self.__verify_fin_ack(fin_ack_packet, address, fin_packet.seq_number):
                fin_ack_received = True
                self.logger.debug('Received FIN/ACK during close; sending ACK to finish close.')
                ack_packet = RxPPacket(
                    self.port_number,
                    self.destination[1],
                    seq_number=self.seq_number,
                    ack_number=fin_ack_packet.sequence_number + 1,
                    ack=True
                )
                self.io.send_queue.put((ack_packet, self.destination))
                self.seq_number += 1

    def __verify_syn(self, packet, address):
        return address == self.destination and packet.syn

    def __verify_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_syn_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.syn and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_fin_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.fin and packet.ack and packet.ack_number - 1 == sequence_number
