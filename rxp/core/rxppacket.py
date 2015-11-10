from rxpheader import RxPHeader

__author__ = 'hunt'


class RxPPacket(object):
    def __init__(self, header=None, data=""):
        self.header = header or RxPHeader()


