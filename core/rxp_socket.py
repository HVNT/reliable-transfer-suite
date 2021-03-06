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
    CLSG = "closing"


class RxPSocket:
    def __init__(self, window_size=10, debugging=False):
        self.window_size = window_size
        self.io = IOLoop()
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
        self.ack_number = 0

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
    def accept(self):
        syn_received = False
        ack_received = False

        # NOTE: starts thread's activity. arranges for the run() method to be invoked on a separate thread of control
        if not self.io.isAlive():
            self.io.start()

        # wait for a syn that passes verification
        while not syn_received:
            try:
                # NOTE: 1st param blocks, 2nd is timeout (on queue.get)
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

        self.io.send_queue.put((syn_ack_packet, self.destination))
        self.seq_number += 1

        # wait for ACK from client confirming SYN/ACK received
        while not ack_received:
            try:
                ack_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                self.logger.debug('Timed out waiting on ack during handshake; retransmitting SYN/ACK.')
                syn_ack_packet.frequency += 1
                syn_ack_packet.update_checksum()
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
        ack_sent = False
        ack_confirmed = False
        syn_ack_timeout = 1

        # wait for SYN/ACK
        while not (syn_ack_received and ack_confirmed):
            syn_ack_packet = None
            try:
                syn_ack_packet, address = self.io.recv_queue.get(True, syn_ack_timeout)
            except Queue.Empty:
                if syn_ack_packet == None and ack_sent:
                    ack_confirmed = True
                    break

                self.logger.debug('Timed out waiting on SYN/ACK during handshake; retransmitting SYN.')
                syn_packet.frequency += 1
                syn_packet.update_checksum()
                self.io.send_queue.put((syn_packet, self.destination))
                continue

            if syn_ack_packet and address:
                syn_ack_received = self.__verify_syn_ack(syn_ack_packet, address, syn_packet.seq_number)

                if syn_ack_received:
                    self.logger.debug('Received SYN/ACK during handshake; sending ACK to finish handshake.')
                    ack_sent = True
                    syn_ack_timeout = 4
                    ack_packet = RxPPacket(
                        self.port_number,
                        self.destination[1],
                        seq_number=self.seq_number,
                        ack_number=syn_ack_packet.seq_number + 1,
                        ack=True
                    )
                    self.io.send_queue.put((ack_packet, self.destination))

        self.seq_number += 1
        self.cxn_status = RxPConnectionStatus.IDLE

    """
    For client or server to send a msg. The 'kill_packet' is used
    to inform client and server can know when we done sending.
    """
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
        kills_sent = 0  # allow to be sent 3 times before dropping client cxn
        kill_seq_number = kill_packet.seq_number
        packets.append(kill_packet)  # put that shit at the end after we've added all the other packets
        self.seq_number += 1

        self.logger.debug('Placing packets in window to be sent now...')
        window = SlidingWindow(packets, self.window_size)
        time_sent = time.time()
        time_remaining = self.retransmit_timer.timeout

        self.cxn_status = RxPConnectionStatus.SEND
        for data_packet in window.window:
            self.io.send_queue.put((data_packet, self.destination))

        while not window.is_empty():
            try:
                ack_packet, address = self.io.recv_queue.get(True, time_remaining)

            # resend entire send window (all packets that weren't yet ACK'd by the receiver)
            except Queue.Empty:
                self.logger.debug(
                    'Timed out waiting for ack during data transmission; retransmitting unacknowledged packets.')
                time_sent = time.time()
                time_remaining = self.retransmit_timer.timeout

                for data_packet in window.window:
                    if kill_seq_number == data_packet.seq_number:
                        kills_sent += 1
                        if kills_sent > 3:  # if retransmitted 3 times already, kill cxn with client
                            self.logger.debug(
                                'Kill packet failed to be acknowledged; unable to end connection, closing now.')
                            return

                    if not window.acknowledged_packets.get(data_packet.seq_number):
                        data_packet.frequency += 1
                        data_packet.update_checksum()
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

            # if a packet in window is acknowledged, slide the window past said received packet
            elif self.__verify_is_ack(ack_packet, address) and window.index_of_packet(ack_packet) >= 0:
                self.retransmit_timer.update(ack_packet.frequency, time.time() - time_sent)
                self.logger.debug(
                    'ACK received. Updated retransmit timer; timeout is now ' + str(self.retransmit_timer.timeout))
                window.acknowledge_packet(ack_packet)

                if self.__verify_ack(ack_packet, address, window.window[0].seq_number):
                    additions = window.slide()
                    # send newly added packets if they were added
                    if additions > 0:
                        while additions > 0:
                            self.io.send_queue.put((window.window[-additions], self.destination))
                            self.seq_number += 1
                            additions -= 1

            # otherwise, update time remaining
            else:
                time_remaining -= time.time() - time_sent / 4  # decay
                if time_remaining < time.time():
                    time_remaining = .5
                self.logger.debug('Trash packet receive; time remaining before next timeout: ' + str(time_remaining))

        self.cxn_status = RxPConnectionStatus.IDLE

    def recv(self):
        kill_received = False
        read_kill = False
        packets = {}
        frequencies = {}

        self.cxn_status = RxPConnectionStatus.RECV
        # until connection is closed, read data
        while not read_kill:
            try:
                data_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                if self.cxn_status == RxPConnectionStatus.CLSG:
                    break
                continue

            if address == self.destination:
                if frequencies.get(data_packet.seq_number):
                    frequencies[data_packet.seq_number] += 1
                else:
                    frequencies[data_packet.seq_number] = 1

                packets[data_packet.seq_number] = data_packet

                # if we got a fin, send fin ack back
                if data_packet.fin:
                    self.logger.debug('Sending FIN/ACK during data transfer.')
                    fin_ack_packet = RxPPacket(
                        self.port_number,
                        self.destination[1],
                        seq_number=self.seq_number,
                        ack_number=data_packet.seq_number + 1,
                        frequency=frequencies[data_packet.seq_number],
                        ack=True,
                        fin=True
                    )
                    self.io.send_queue.put((fin_ack_packet, self.destination))
                    self.seq_number += 1
                    self.cxn_status = RxPConnectionStatus.CLSG

                # if we get an ack while closing, we've gracefully closed
                elif data_packet.ack and self.cxn_status == RxPConnectionStatus.CLSG:
                    self.logger.debug('Received Final ACK. Closing..')
                    self.cxn_status = RxPConnectionStatus.NONE
                    return "CONNECTION CLOSED"

                else:
                    self.logger.debug('Sending ACK during data transfer.')
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

        response = ''.join(
            map(
                lambda packet: packet.payload,
                map(lambda sequence_number: packets[sequence_number], sorted(packets.keys()))
            ))
        self.cxn_status = RxPConnectionStatus.IDLE
        return response

    def close(self):
        clean_close = False

        self.logger.debug('Sending FIN to initiate close.')
        fin_packet = RxPPacket(
            self.port_number,
            self.destination[1],
            seq_number=self.seq_number,
            fin=True
        )
        self.io.send_queue.put((fin_packet, self.destination))
        fins_sent = 1
        self.seq_number += 1

        while not clean_close:
            try:
                fin_response_packet, address = self.io.recv_queue.get(True, 1)
            except Queue.Empty:
                if fins_sent < 3:
                    self.logger.debug('Timed out waiting for FIN/ACK during close; sending another FIN.')
                    fin_packet = RxPPacket(
                        self.port_number,
                        self.destination[1],
                        seq_number=self.seq_number,
                        fin=True
                    )
                    self.io.send_queue.put((fin_packet, self.destination))
                    fins_sent += 1
                    continue
                else:
                    self.logger.debug(
                        'Timed out waiting for FIN/ACK during close. Already attempted to close 3 times, closing now without acknowledgement.')
                    self.cxn_status = RxPConnectionStatus.NONE
                    break

            # if FIN received after FIN sent, verify with ACK and close
            if self.__verify_fin(fin_response_packet, address):
                clean_close = True
                self.logger.debug('Received FIN during close; sending ACK to finish close.')
                ack_packet = RxPPacket(
                    self.port_number,
                    self.destination[1],

                    seq_number=self.seq_number,
                    ack_number=fin_response_packet.seq_number + 1,
                    ack=True
                )
                self.io.send_queue.put((ack_packet, self.destination))
                self.seq_number += 1
                time.sleep(5)
                self.cxn_status = RxPConnectionStatus.NONE

                # received ACK for FIN sent, so FIN packet sent corrupted, resend fin packet
            if self.__verify_ack(fin_response_packet, address, fin_packet.seq_number):
                self.logger.debug('Received ACK for FIN during close; resending FIN to progress close.')
                self.io.send_queue.put((fin_packet, self.destination))

                # if FIN/ACK received then progress with closing handshake
            if self.__verify_fin_ack(fin_response_packet, address, fin_packet.seq_number):
                clean_close = True
                self.logger.debug('Received FIN/ACK during close; sending ACK to finish close.')
                ack_packet = RxPPacket(
                    self.port_number,
                    self.destination[1],
                    seq_number=self.seq_number,
                    ack_number=fin_response_packet.seq_number + 1,
                    ack=True
                )
                self.io.send_queue.put((ack_packet, self.destination))
                self.seq_number += 1
                time.sleep(5)
                self.cxn_status = RxPConnectionStatus.NONE

    def __verify_syn(self, packet, address):
        return address == self.destination and packet.syn

    def __verify_is_ack(self, packet, address):
        return address == self.destination and packet.ack

    def __verify_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_syn_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.syn and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_fin_ack(self, packet, address, sequence_number):
        return address == self.destination and packet.fin and packet.ack and packet.ack_number - 1 == sequence_number

    def __verify_fin(self, packet, address):
        return address == self.destination and packet.fin and not packet.ack
