# reliable-transfer-suite
Team Members:

	Hunter Brennick (hbrennik3@gatech.edu)
	Sherman Mathews (smathews6@gatech.edu)
	
Class: 		

	CS 3251, Section B

Date:		

	11/27/2015

Assignment:	

	Programming Assignment 2 (RxP)

Files:

	fxa_client.py:			represents an fxa_client
	fxa_server.py: 			represents an fxa_server
	io_loop.py:				a loop used for handling simultaneous sending and receiving
	retransmit_timer.py:	used to dynamically calculate retransmit timer
	rxp_exception.py:		used to handle rxp exceptions
	rxp_packet.py:			represents and rxp_packet, including header information
	rxp_socket.py:			represents an rxp_socket
	sliding_window.py:		represents a sliding window

Instructions:

	Note: This code was tested using Python 2.7 on Linux and Mac.
	
	Steps:
		1. Run NetEmu.py
		2. Run the server application
		3. Run the client application
	
	To run the server program:
		python fxa_server.py X A P
		where:
			X is the port that the FxA-server's UDP socket shoudl bind to
				(this should be an odd number)
			A is the IP address of Net Emu
			P is the UDP port number of NetEmu
		upon program start, user will be prompted for desired window size
	
	To run the client program:
		python fxa_client.py X A P
		where:
			X is the port that the FxA-client's UDP socket should bind to
				(it should be the server's port number minus 1)
			A is the IP address of Net Emu
			P is the UDP port number of NetEmu
		upon program start, user will be prompted for desired window size

Updated Protocol and API description: 
	
	TODO
	
Bugs and Limitations: 

	TODO