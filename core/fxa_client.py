import sys

from rxp_socket import RxPSocket

__author__ = 'hunt'


def __dequote(target):
    return target.strip('"')


def main():
    if len(sys.argv) != 4:
        print "Invalid arguments."
        print "Command-line: FxA-client X A P."
        print "X: The port that the FxA-client's UDP socket port should bind to. " \
              "Please remember that this port number should be equal to the server's " \
              "port number minus 1."
        print "A: The IP address of NetEmu."
        print "P: The UDP port number of NetEmu."
        sys.exit(0)

    # TODO check if port number appropriate for a client..

    # get params
    client_udp_port = sys.argv[1]
    net_emu_ip = sys.argv[2]
    net_emu_udp_port = sys.argv[3]

    # TODO should we be asking for the window size here?
    window = int(raw_input("Enter a window size W: "))

    # set up client socket
    socket = RxPSocket(window, debugging=True)
    socket.bind(("0.0.0.0", int(client_udp_port)))

    # connect socket
    socket.connect((str(net_emu_ip), int(net_emu_udp_port)))

    while True:
        command = raw_input("Enter a command (get F, post F, disconnect): ")
        command = command.split()
        target = __dequote(command[1])

        if len(command) > 2:
            print "Invalid number of parameters. Please check your command."

        elif command[0] == "disconnect":
            if len(command) == 1:
                # disconnect from server
                socket.close()
                sys.exit(0)
            else:
                print "Invalid number of parameters. Please check your command."

        elif command[0] == "get":
            socket.send(target)

            print "Sending request to get the file: " + target
            read_val = socket.recv()

            print "Received file contents."
            f = open(target + "__copy", 'w')
            f.write(read_val)

            print "Saved file as: " + target + "__copy."
            f.close()

        elif command[0] == "post":
            socket.send(target)

            print "Sending file send request: " + target

            # TODO..

        else:
            print "Invalid command."


if __name__ == '__main__':
    main()
