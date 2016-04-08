import sys
import socket
# total = len(sys.argv)
# cmdargs = str(sys.argv)
#
# from socket import *
# serverName = str(sys.argv[1]);
# serverPort = 12000 #change this port number if required
# clientSocket = socket(AF_INET, SOCK_STREAM)
# clientSocket.connect((serverName, serverPort))
# sentence = raw_input('Input lowercase sentence:')
# clientSocket.send(sentence)
# modifiedSentence = clientSocket.recv(1024)
# print 'From Server:', modifiedSentence
# clientSocket.close()


def get_open_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.bind(('', 0))
        client_socket.listen(1)
        return client_socket.getsockname()[1]


def Main():
    # TODO: Validate user input
    # mode: push or pull
    # polling_interval: integer
    # user_name: string
    # server_name: string
    # server_port_number: integer 1024-65535
    mode = str(sys.argv[1])
    polling_interval = int(sys.argv[2])
    user_name = str(sys.argv[3])
    server_name = str(sys.argv[4])
    server_port_number = sys(sys.argv[5])

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_name, server_port_number))

    while True:
        command = input()
        if command == 'display':
            continue
        elif command == 'post_to_forum':
            continue
        elif command == 'read_post':
            continue
        else:
            print("Input error, please try again")
    #     client_socket.sendto(bytes(message, "utf-8"), (host, port))
    #     data = client_socket.recv(1024).decode()
    #
    #     print('Received from server: ' + data)
    #
    #     message = input(" -> ")

    client_socket.close()

if __name__ == '__main__':
    print(get_open_port())
    # Main()