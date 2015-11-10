__author__ = 'hunt'

import socket


"""
enum that describes the connection status of a socket
"""


class RxPConnectionStatus():
    NONE = "no_conn"
    IDLE = "idle"
    SEND = "sending"
    RECV = "receiving"


class RxPSocket(object):
    def __init__(self):
        # TODO verify python version

        self.is_sender = False  # TODO appropriate default?

        self.dst_addr = None
        self.src_addr = None

        self.send_bfr = []  # TODO allocate appropriate space..
        self.recv_bfr = []  # ""

        self.send_window = 1  # TODO appropriate defualt?
        self.recv_window = None  # TODO Packet.MAX_WINDOW_SIZE

        self.cxn_status = RxPConnectionStatus.NONE
        self.cxn_timeout = None  # TODO set

        self.seq = None  # TODO need wrappable num..
        self.ack = None  # ""

        self.resend_limit = 100  # TODO need? appropriate default?

        # initialize UDP socket
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # def bind(self):
    #
    #
    # def connect(self):
    #
    #
    # def listen(self):
    #
    #
    # def accept(self):
    #
    #
    # def send(self):
    #
    #
    # def recv(self):
    #
    #
    # def close(self):
