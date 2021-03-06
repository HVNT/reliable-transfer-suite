import sys
import os

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

    # check if valid port
    if int(sys.argv[1]) % 2 != 0 or not (1024 <= int(sys.argv[1]) <= 65535):
        print "Invalid port. The port number must be even and between 1024 and 65535."
        sys.exit(0)

    # get params
    client_udp_port = sys.argv[1]
    net_emu_ip = sys.argv[2]
    net_emu_udp_port = sys.argv[3]

    window = int(raw_input("Enter a window size W: "))
    debugger = int(raw_input("Enable debugger? (1 or 0) "))

    # set up client socket
    socket = RxPSocket(window, debugging=debugger)
    socket.bind(("0.0.0.0", int(client_udp_port)))

    # connect socket
    socket.connect((str(net_emu_ip), int(net_emu_udp_port)))

    while True:
        command = raw_input("Enter a command (get F, post F, disconnect): ")
        command = command.split()

        if len(command) > 1:
            target = __dequote(command[1])

        if len(command) > 2 or len(command) == 0:
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

            if read_val == "ERR:FILE_NOT_FOUND":
                print target + " not found."
            else:
                print "Received file contents."
                target = target.split('.')

                filename = target[0] + "__copy." + target[1]
                i = 0
                while os.path.isfile(filename):
                    i += 1
                    filename = "%s__copy(%d).%s" % (target[0], i, target[1])
                f = open(filename, 'w')
                f.write(read_val)

                print "Saved file as: " + filename
                f.close()

        elif command[0] == "post":
            if os.path.isfile(command[1]):
                socket.send("post " + target)
                print "Sending file send request: " + target
                f = open(command[1], 'r')
                contents = f.read()
                socket.send(contents)
                f.close()
            else:
                print "File not found to post!"

        else:
            print "Invalid command."


if __name__ == '__main__':
    main()
