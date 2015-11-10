__author__ = 'hunt'

import socket


class RxPSocket(object):
    def __init__(self):
        # TODO verify python version

        self.is_sender = False  # TODO appropriate default?

        self.dst_adr = None
        self.src_adr = None

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

    """ TODO fix comment
    binds socket to the given port. port is optional. If no port is given,
    self.port is used. If self.port has not been set, this method does nothing.
    """
    def bind(self, src_adr):
        if src_adr:
            self.src_adr = src_adr

        if self.src_adr:
            self._socket.bind(self.src_adr)
        # else
            # TODO raise exception

    """ TODO fix comment
    connects to destAddr given in format (ipaddr, portNum). Uses a handshake. The
    sender sends a SYN packet. The receiver sends back a SYN, ACK. The sender then
    sends an ACK and the handshake is complete.
    """
    def connect(self, dst_adr):
        if dst_adr and self.src_adr:
            self.dst_adr = dst_adr
            self.seq = 0  # TODO update when wrappable num



        # else:
            # TODO raise exception
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

    """
    enum that describes the connection status of a socket
    """
    class RxPConnectionStatus():
        NONE = "no_conn"
        IDLE = "idle"
        SEND = "sending"
        RECV = "receiving"
