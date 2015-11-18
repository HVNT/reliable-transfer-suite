import sys
import os.path

from rxp_socket import RxPSocket

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

    print "Server set up and accepting client sockets."

    while True:
        message = socket.recv()
        print "Accepted file request: " + message

        if message == '':
            pass
        if not os.path.isfile(message):
            print "Sorry, the file requested does not exist!"
            pass

        f = open(message, 'r')
        contents = f.read()
        print "Streaming contents of file requested."
        socket.send(contents)

        f.close()
        raw_input("Press enter to accept more connections.")  # ??


if __name__ == '__main__':
    main()
