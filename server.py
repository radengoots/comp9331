import socket
import sys


def load_ebook(book_name, page_number):
    try:
        ebook = open(book_name + '_page' + page_number, 'r')
        print(ebook.read())
    except IOError:
        print('File not found')
    else:
        ebook.close()


def main():
    # TODO: validate number of arguments
    # input validation
    RECV_BUFFER = 4096
    server_port = int(sys.argv[1])

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', server_port))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    server_socket.listen(10)
    conn, addr = server_socket.accept()
    print("The server is listening on port number " + str(server_port))
    print("The database for discussion posts has been initialised")

    while True:
        print('Connected with ' + addr[0] + ': ' + str(addr[1]))
        request = str(conn.recv(RECV_BUFFER))
        # if not request:
        #     break
        # request = request.split(' ')
        # print(request)
        # if request[0] == 'display':
        #     load_ebook(request[1], request[2])

        print("From connected user: " + request)

        conn.send(request)

    conn.close()
    server_socket.close()


if __name__ == '__main__':
    main()
