# reliable-transfer-suite
##Team Members:
Hunter Brennick (hbrennik3@gatech.edu)</br>
Sherman Mathews (smathews6@gatech.edu)
	
##Class: 		
CS 3251, Section B

##Date:		
11/27/2015

##Assignment:	
Programming Assignment 2 (RxP)

##Files:
	fxa_client.py:			represents an fxa_client
	fxa_server.py: 			represents an fxa_server
	io_loop.py:				a loop used for handling simultaneous sending and receiving
	retransmit_timer.py:	used to dynamically calculate retransmit timer
	rxp_exception.py:		used to handle rxp exceptions
	rxp_packet.py:			represents and rxp_packet, including header information
	rxp_socket.py:			represents an rxp_socket
	sliding_window.py:		represents a sliding window

##Instructions:
Note: This code was tested using Python 2.7 on Linux and Mac.

Steps:

	1. Run NetEmu.py
	2. Run the server application
	3. Run the client application

To run the server program:

	python fxa_server.py X A P
	where:
		X is the port that the FxA-server's UDP socket should bind to
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

##Updated Protocol and API description: 
On a high level, we implemented a Selective Repeat window-based flow control for our reliable transport protocol; however, there were some alterations in design with regards to the API in order to best meet our goals.

We made a number of changes to our packet header structure in order to add needed functionality or get rid of unnecessary parts. We added a frequency field to the header for use in dynamically calculating timeouts. We removed the packet length field, because we found kill packets to be a more effective means of designating the end of messages. Since we never found an occasion to use it, we also removed the RST control bit, leaving only: SYN, ACK, and FIN. A final minor change: we renamed header length to offset because it seemed, to us, a more intuitive description.

As for our API, we found we had a lot of redundancy between the client and server functionalities and determined that we could merge a number of items. With this in mind, we created an RxPSocket class that would house the functionalities of both, with the client using functions relevant to it, and the server using those which were relevant to it respectively. The only client-specific function in RxPSocket was connect, which the client would call in order to connect to a server. The server-specific function was accept, in which a server would initialize, accept incoming connections, and perform handshake logic in order to establish a connection. Shared functions include: bind(address) to bind the socket to a port and ip address, send(data) and receive(data) for sending packets, and close() for gracefully closing connections. We ditched the idea of a get(filename) function because we found that it was unnecessary since we could handle it with just the send and receive functions.

For handling multiplexing in our application we decided to implement an asynchronous IO loop. Each socket starts a thread upon calling accept or connect (server and client respectively). These threads manage send and receive queues which are constantly polling for incoming data.
	
##Bugs and Limitations:
Unflushed packets from receive queue occasionally cause commands to fail after a disconnect.