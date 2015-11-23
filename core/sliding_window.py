__author__ = 'hunt'


class SlidingWindow:
    def __init__(self, packets, window_size):
        self.packets = packets
        self.acknowledged_packets = {}
        self.window_size = window_size
        self.window_idx = 0
        self.__calculate_window()  # sets self.window[]

    def slide(self):
        if len(self.window) > 0:
            slide_distance = 1  # by default, since we know when this is called index 0 has been ACK'd
            for packet in self.window:
                # continue until reach a packet that has not yet been ACK'd
                if self.acknowledged_packets.get(packet.seq_number):
                    slide_distance += 1
                    self.acknowledged_packets.pop(packet.seq_number)  # remove as we go..
                else:
                    break

            self.window_idx += slide_distance
            already_sent = len(self.window) - slide_distance
            self.__calculate_window()
            not_sent = len(self.window) - already_sent
            return not_sent
        return 0

    def is_empty(self):
        return len(self.window) == 0

    def index_of_packet(self, target_packet):
        target_seq_number = target_packet.ack_number - 1

        if target_seq_number and len(self.window) > 0:
            for i, packet in enumerate(self.window):
                if target_seq_number == packet.seq_number:
                    return i
        return -1

    def acknowledge_packet(self, packet):
        self.acknowledged_packets[packet.seq_number] = packet

    # set self.window
    def __calculate_window(self):
        if (self.window_idx + self.window_size) < len(self.packets):
            self.window = self.packets[self.window_idx: (self.window_idx + self.window_size)]
        else:
            self.window = self.packets[self.window_idx: len(self.packets)]
