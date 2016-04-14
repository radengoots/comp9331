import socket
import sys
from thread import *

RECV_BUFFER = 4096

def load_ebook(book_name, page_number):
    try:
        ebook_file = open(book_name + '_page' + page_number, 'r')
        ebook = ebook_file.read()
    except IOError:
        print('File not found')
        return 'File not found'
    else:
        ebook_file.close()
        return ebook


def clientThread(conn):
    # while True:
    while True:
        request = conn.recv(RECV_BUFFER)
        print("Request: " + request)
        request = request.split(' ')
        # print(request)
        if request[0] == 'display':
            ebook = load_ebook(request[1], request[2])
            conn.sendall(ebook)
        else:
            conn.sendall(str(request))

        if request[0] == 'stop':
            break

    conn.close()


def main():
    # TODO: validate number of arguments
    # TODO: check port availability

    server_port = int(sys.argv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', server_port))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    server_socket.listen(10)
    print("The server is listening on port number " + str(server_port))
    print("The database for discussion posts has been initialised")

    # conn, addr = server_socket.accept()
    while True:
        try:
            print('ready to receive')
            conn, addr = server_socket.accept()
        except socket.timeout:
            print('Timed out waiting for a connection')
            continue

        print('Got request from ' + addr[0] + ': ' + str(addr[1]))

        start_new_thread(clientThread, (conn,))
        # # while True:
        # request = conn.recv(RECV_BUFFER)
        # print("Request: " + request)
        # request = request.split(' ')
        # # print(request)
        # if request[0] == 'display':
        #     ebook = load_ebook(request[1], request[2])
        #     conn.sendall(ebook)
        # if request[0] == 'stop':
        #     print(request)
        #     # conn.close()
        #     break

        # print("Request: " + request)
        # if not request:
        #     break
        # request = request.split(' ')
        # # print(request)
        # if request[0] == 'display':
        #     ebook = load_ebook(request[1], request[2])
        #     conn.sendall(ebook)
        # conn.close()

    server_socket.close()


if __name__ == '__main__':
    main()
