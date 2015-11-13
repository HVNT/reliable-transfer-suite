import Queue
import socket
from threading import Thread
from rxp_packet import RxPPacket
from rxp_packet import ParseException

__author__ = 'hunt'


class IOLoop(Thread):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.daemon = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.01)

        self.send_queue = Queue.Queue()
        self.recv_queue = Queue.Queue()

    def run(self):
        while True:
            try:
                packet, address = self.send_queue.get(True, 0.1)
                self.socket.sendto(packet.serialize(), address)
            except Queue.Empty:
                pass

            try:
                packet, address = self.socket.recvfrom(4096)
                packet = RxPPacket.unpickle(packet)
                self.recv_queue.put((packet, address))
            except (socket.timeout, ParseException), e:
                pass
