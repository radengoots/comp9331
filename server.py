import socket
import sys


def Main():
    # input validation
    server_port = int(sys.argv[1])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', server_port))

    server_socket.listen(1)
    print("The server is listening on port number " + str(server_port))
    print("The database for discussion posts has been initialised")

    while True:
        conn, addr = server_socket.accept()
        data = conn.recv(1024).decode()
        if not data:
            break
        print("From connected user: " + str(data))

        data = str(data).upper()
        print("Sending: " + str(data))
        conn.send(data.encode())

    conn.close()


if __name__ == '__main__':
    Main()
