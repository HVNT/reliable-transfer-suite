from rxpheader import RxPHeader
from zlib import adler32

__author__ = 'hunt'


class RxPPacket(object):
    def __init__(self, header=None, data=""):
        self.header = header or RxPHeader()

	#TODO pickle and unpickle functions
	def pickle(self):
		return None
	#def unpickle(self):
		#
	
	def _checksum(self):
		#returns checksum of packet using adler32 algorithm
		self.header.fields["checksum"] = 0
		p = str(self.pickle())
		c = adler32(p)
		return c
		

