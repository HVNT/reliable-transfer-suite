__author__ = 'sherm'

class RxPException(Exception):
	""" Exceptions for RxP errors """
	CONNECTION_TIMEOUT 	= 1
	INVALID_CHECKSUM 	= 2
	INVALID_SEQNO		= 3
	INVALID_SOURCE 		= 4
	INVALID_TYPE 		= 5	
	RESEND_LIMIT 		= 6
	#TODO add/remove exception types as needed
	
	MESSAGE = {
		CONNECTION_TIMEOUT: "connection timeout",
		INVALID_CHECKSUM:	"invalid checksum",
		INVALID_SEQNO:		"unexpected sequence number",
		INVALID_SOURCE:		"packet not from expected source",
		INVALID_TYPE:		"unexpected packet type"
		RESEND_LIMIT:		"resend limit exceeded",
	}
	
	def __init__(self, type_, message=None, innerException=None):
		self.type = type_
		self.inner = innerException
		if message = None:
			self.msg = RxPException.MESSAGE[type_]
		else:
			self.msg = msg
	
	def __str__(self):
		return self.msg