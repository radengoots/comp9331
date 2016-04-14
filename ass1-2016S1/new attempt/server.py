import socket
import sys
import select
from thread import *
import time

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

    connection_list = []

    server_port = int(sys.argv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', server_port))
        server_socket.listen(10)
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    connection_list.append(server_socket)

    print("The server is listening on port number " + str(server_port))
    print("The database for discussion posts has been initialised")

    while True:
        # get list sockets  which are ready to read through select
        read_sockets, write_sockets, error_sockets = select.select(connection_list, [], [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                print('ready to receive')
                try:
                    conn, addr = server_socket.accept()
                except socket.timeout:
                    print('Timed out waiting for a connection')
                    continue

                connection_list.append(conn)
                print "Client (%s, %s) connected" % addr

            # Data coming from a client
            else:
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        print data
                        conn.sendall(data)
                    # connection_list.append(server_socket)
                # Client disconnected, so remove from socket list
                except:
                    print "Client (%s, %s) is offline" % addr
                    sock.close()
                    connection_list.remove(sock)
                    continue

    server_socket.close()


if __name__ == '__main__':
    main()
