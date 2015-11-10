import ctypes

__author__ = 'hunt'


# define binary types for use in header fields.
class RxPHeader(object):

    uint16 = ctypes.c_uint16
    uint32 = ctypes.c_uint32

    FIELDS = (
        ("src_port", uint16, 0),
        ("dst_port", uint16, 0),
        ("seq", uint32, 0),
        ("ack", uint32, 0),
        ("length", uint32, 0),
        ("window", uint16, 0),
        ("checksum", uint16, 0),
        ("ctrl", uint16, 0)  # TODO change this to less size? only needs 4 bits .. TOOD also .. header length?
    )

    def __init__(self, **kwargs):
        self.fields = {}

        # keys = kwargs.keys()

        for field in RxPHeader.FIELDS:
            field_key = field[0]
            field_val = 0

            if kwargs[field_key]:
                field_val = kwargs[field_key]

            self.fields[field_key] = field_val


