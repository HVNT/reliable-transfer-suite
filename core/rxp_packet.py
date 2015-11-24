import math
import hashlib
import zlib

__author__ = 'hunt'


class ParseException(Exception):
    pass


class RxPPacket:
    def __init__(
            self,
            src_port,
            dst_port,
            seq_number=0,
            ack_number=0,
            window_size=1024,
            frequency=1,
            ack=False,
            syn=False,
            fin=False,
            payload=''
    ):
        self.src_port = src_port
        self.dst_port = dst_port
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.window_size = window_size
        self.frequency = frequency
        self.ack = ack
        self.syn = syn
        self.fin = fin
        self.payload = payload or ''
        self.data_offset = int(math.ceil(1.0 * len(payload) / 4))  # TODO ?? shouldnt this be static?
        self.checksum = 0
        self.checksum = self.__class__.calculate_checksum(self.serialize())

    @classmethod
    def calculate_checksum(self, raw_packet):
        checksum_algorithm = hashlib.md5()
        checksum_algorithm.update(raw_packet)
        return int(checksum_algorithm.hexdigest(), 16) & int(math.pow(2, 16) - 1)

    @classmethod
    def parse(self, data):
        # 20 bytes of headers min req
        if len(data) < 20:
            raise ParseException

        # essentially here we are "parsing" the checksum to verify it quick before we return the initialized packet..
        # grabbing raw checksum from packet.. index into checksum bytes
        # according to new RxPPacket header structure checksum should be 2 bytes starting @byte17
        raw_checksum = (ord(data[18]) << 8) | ord(data[19])
        zeroed_packet = data[0: 18] + chr(0) + chr(0) + data[20:]
        calculated_checksum = self.calculate_checksum(zeroed_packet)

        if raw_checksum != calculated_checksum:
            print "Checksums don't match"
            raise ParseException

        raw_packet = map(ord, data)

        packet = RxPPacket(
            (raw_packet[0] << 8) | raw_packet[1],
            (raw_packet[2] << 8) | raw_packet[3],
            seq_number=raw_packet[4] << 24 | raw_packet[5] << 16 | raw_packet[6] << 8 | raw_packet[7],
            ack_number=raw_packet[8] << 24 | raw_packet[9] << 16 | raw_packet[10] << 8 | raw_packet[11],
            window_size=raw_packet[12] << 24 | raw_packet[13] << 16 | raw_packet[14] << 8 | raw_packet[15],
            frequency=raw_packet[16] >> 3,
            ack=(raw_packet[16] & 4) == 4,
            syn=(raw_packet[16] & 2) == 2,
            fin=(raw_packet[16] & 1) == 1,
            payload=data[20: 20 + raw_packet[17] * 4]  # data offset..
        )

        return packet

    def serialize(self):
        BIT_MASK_4 = 255 << 24
        BIT_MASK_3 = 255 << 16
        BIT_MASK_2 = 255 << 8
        BIT_MASK_1 = 255

        # each index = 32 bits
        words = [
            (self.src_port << 16) + self.dst_port,
            self.seq_number,
            self.ack_number,
            self.window_size,
            (self.frequency << 27) + (int(self.ack) << 26) + (int(self.syn) << 25) + (int(self.fin) << 24) +
            (self.data_offset << 16) + self.checksum,
        ]
        byte_array = []

        for word in words:
            byte_array.append((word & BIT_MASK_4) >> 24)
            byte_array.append((word & BIT_MASK_3) >> 16)
            byte_array.append((word & BIT_MASK_2) >> 8)
            byte_array.append(word & BIT_MASK_1)

        serialized_packet = ''.join(map(chr, byte_array)) + self.payload
        return serialized_packet

    def update_checksum(self):
        self.checksum = 0
        self.checksum = self.__class__.calculate_checksum(self.serialize())

    def is_killer(self):
        return not self.syn \
               and not self.ack \
               and not self.fin \
               and self.payload == ''

    def print_packet(self):
        print "src port: " + str(self.src_port) + \
              " | dst port: " + str(self.dst_port)
        print "seq #: " + str(self.seq_number) + \
              " | ack #: " + str(self.ack_number)
        print "is ack: " + str(self.ack) + \
              " | is syn: " + str(self.syn) + \
              " | is fin: " + str(self.fin)
        print "frequency : " + str(self.frequency) + \
              " | data offset: " + str(self.data_offset)
        print "checksum: " + str(self.checksum) + \
              " | window size: " + str(self.window_size)
        # print "payload: " + str(self.payload)


