__author__ = 'hunt'

import math


class ParseException(Exception):
    pass


class RxPPacket:
    def __init__(
            self,
            src_port,
            dst_port,
            seq_number=0,
            payload='',
            ack_number=0,
            frequency=1,
            ack=False,
            syn=False,
            fin=False,
            rst=False,
            window_size=1024
    ):
        self.src_port = src_port
        self.dst_port = dst_port
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.frequency = frequency
        self.ack = ack
        self.syn = syn
        self.fin = fin
        self.rst = rst
        self.data_offset = int(math.ceil(1.0 * len(payload) / 4))
        self.checksum = 0
        self.window_size = window_size
        self.payload = payload

        # TODO
        # self.checksum = self.__class__.calculate_checksum(self.serialize())

    @classmethod
    def calculate_checksum(self, raw_packet):
        return 1

    # TODO  pickle ("serialize")

    """
    unpickle = "parsing"
    """
    @classmethod
    def unpickle(self, raw_packet):
        # 20 bytes of headers min req
        if len(raw_packet) < 20:
            raise ParseException

        # essentially here we are "parsing" the checksum to verify it quick before we return the initialized packet..
        # grabbing raw checksum from packet.. step into checksum byte index
        # according to new RxPPacket header structure checksum should be 2 bytes starting @byte17
        raw_checksum = (ord(raw_packet[18]) << 8) | ord(raw_packet[19])
        zeroed_packet = raw_packet[0: 18] + chr(0) + chr(0)
        calculated_checksum = self.calculate_checksum(zeroed_packet)

        if raw_checksum != calculated_checksum:
            raise ParseException

        raw_packet = map(ord, raw_packet)

        # TODO check unary logic parsing out ctrl bits && payload set
        return RxPPacket(
            (raw_packet[0] << 8) | raw_packet[1],
            (raw_packet[2] << 8) | raw_packet[3],
            seq_number=raw_packet[4] << 24 | raw_packet[5] << 16 | raw_packet[6] << 8 | raw_packet[7],
            ack_number=raw_packet[8] << 24 | raw_packet[9] << 16 | raw_packet[10] << 8 | raw_packet[11],
            window_size=raw_packet[12] << 24 | raw_packet[13] << 16 | raw_packet[14] << 8 | raw_packet[15],
            frequency=raw_packet[16] >> 3,
            ack=(raw_packet[16] & 4) == 4,
            syn=(raw_packet[16] & 2) == 2,
            fin=(raw_packet[16] & 1) == 1,
            rst=(raw_packet[17] & 256) == 256,
            payload=raw_packet[20:]
        )
