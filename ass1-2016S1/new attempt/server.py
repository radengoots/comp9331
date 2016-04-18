import Queue
import select
import socket
import sys

RECV_BUFFER = 4096


def get_ebook(book_name, page_number):
    try:
        ebook_file = open(book_name + '_page' + page_number, 'r')
        ebook = ebook_file.read()
    except IOError:
        print('File not found')
        return False
    else:
        ebook_file.close()
        return ebook


def display(username, mode, book_name, page_number):
    ebook = get_ebook(book_name, page_number)

    if not ebook:
        pass
    else:
        return 'File not found'


def main():
    # TODO: validate number of arguments
    # TODO: check port availability

    connection_list = []
    # [username, mode, polling_interval, ip, port]
    connected_clients = []
    message_queues = {}
    outputs = []

    server_port = int(sys.argv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setblocking(0)
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
        read_sockets, write_sockets, error_sockets = select.select(
            connection_list, outputs, [])

        for sock in read_sockets:
            # New connection
            if sock == server_socket:
                print('ready to receive')
                try:
                    conn, addr = server_socket.accept()
                    conn.setblocking(0)
                except socket.timeout:
                    print('Timed out waiting for a connection')
                    continue

                connection_list.append(conn)
                print "Client (%s, %s) is connected" % addr
                message_queues[conn] = Queue.Queue()

            # Data coming from a client
            else:
                try:
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        print data
                        data = str(data).split(',')
                        if data[0] == 'd':
                            print(addr)
                            conn.sendall(addr)
                        elif data[0] == 's':
                            # data[0]: code, [1]: username,[2]: mode, [3]: polling_interval
                            connected_clients.append(
                                [data[1], data[2], int(data[3]), addr[0],
                                 addr[1]])
                            print(
                                data[1], data[2], int(data[3]), addr[0],
                                addr[1])
                            message_queues[sock].put('ok')
                            if sock not in outputs:
                                outputs.append(sock)
                                # conn.sendall('ok')

                # Client disconnected, so remove from socket list
                except:
                    print "Client (%s, %s) is offline" % addr
                    sock.close()
                    connection_list.remove(sock)
                    continue

        for sock in write_sockets:
            try:
                next_msg = message_queues[sock].get_nowait()

            except Queue.Empty:
                outputs.remove(sock)
            else:
                sock.send(next_msg)

    server_socket.close()


if __name__ == '__main__':
    main()
