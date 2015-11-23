__author__ = 'hunt'


class SlidingWindow:
    def __init__(self, packets, window_size):
        self.packets = packets
        self.window_size = window_size
        self.window_idx = 0
        self.__calculate_window()  # sets self.window[]

    def slide_past(self, packet):
        packet_idx = self.index_of_packet(packet)
        if packet_idx >= 0:
            self.window_idx += packet_idx + 1
            self.__calculate_window()
        else:
            print "shit fucked in SLIDE_PAST"

    def is_empty(self):
        return len(self.window) == 0

    def is_emptying(self):
        return len(self.window) < self.window_size

    def index_of_packet(self, target_packet):
        target_seq_number = target_packet.ack_number - 1

        if target_seq_number and len(self.window) > 0:
            for i, packet in enumerate(self.window):
                if target_seq_number == packet.seq_number:
                    return i
        return -1

    # set self.window
    def __calculate_window(self):
        if (self.window_idx + self.window_size) < len(self.packets):
            self.window = self.packets[self.window_idx: (self.window_idx + self.window_size)]
        else:
            self.window = self.packets[self.window_idx: len(self.packets)]
