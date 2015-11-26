import sys
import os.path
import os

from rxp_socket import RxPSocket
from rxp_packet import ParseException

__author__ = 'hunt'


def main():
    if len(sys.argv) != 4:
        print "Invalid arguments."
        print "USAGE: FxA-server X A P"
        print "X: the port number at which the fxa-server's UDP socket should bind to" \
              "Please remember that this port number should be an odd number."
        print "A: the IP address of NetEmu"
        print "P: the UDP port number of NetEmu"
        sys.exit(0)

    # check if valid port
    if int(sys.argv[1]) % 2 != 1 or not (1024 <= int(sys.argv[1]) <= 65535):
        print "Invalid port. The port number must be odd and between 1024 and 65535."
        sys.exit(0)

    server_udp_port = sys.argv[1]
    net_emu_ip = sys.argv[2]
    net_emu_udp_port = sys.argv[3]

    window = int(raw_input("Enter a window size W: "))

    print "Use 'ctrl + c' to terminate."

    # set up server socket
    socket = RxPSocket(window_size=int(window), debugging=True)
    socket.bind(("", int(server_udp_port)))

    # trigger socket to begin accepting client sockets
    socket.accept()
    destination = socket.destination  # ??

    print "Client session initialized; accepting client requests."

    while True:
        message = socket.recv()

        print "connection status is: ", socket.cxn_status
        if socket.cxn_status == "no_conn":

            # TODO correct to go back into accept???
            socket.accept()
            pass

        else:
            print "Accepted file request: " + message

            if message == '':
                pass

            if not os.path.isfile(str(os.getcwd() + "/" + message)):
                print "Tried to get file from: ", str(os.getcwd() + "/" + message)
                print "Sorry, the file requested does not exist!"
                pass

            # TODO what if filename has spaces?
            message = message.split()
            if message[0] == "post" and len(message) > 1:
                read_val = socket.recv()

                message = message[1].split('.')
                filename = message[0] + "__copy." + message[1]
                i = 0
                while os.path.isfile(filename):
                    i += 1
                    filename = "%s__copy(%d).%s" % (message[0], i, message[1])
                f = open(filename, 'w')
                f.write(read_val)

                print "Saved file as: " + filename

                f.close()
            else:
                message = message[0]
                try:
                    f = open(message, 'r')
                    contents = f.read()
                    print "Streaming contents of file requested."
                    socket.send(contents)
                    f.close()

                except:  # TODO should be "excepting" things that are passed up from socket?
                    print "No file to stream. Letting client know."
                    socket.send("ERR:FILE_NOT_FOUND")
                    pass

                # raw_input("Press enter to accept more connections.")  # ??


if __name__ == '__main__':
    main()
