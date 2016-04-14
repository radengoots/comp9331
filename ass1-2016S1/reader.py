import socket
import sys


def get_available_port():
    c_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c_s.bind(('', 0))
    port = c_s.getsockname()[1]
    c_s.close()
    return port


def main():
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
    server_port_number = int(sys.argv[5])

    available_port = get_available_port()

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind(('', available_port))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    print('Socket bind complete (Port ' + str(available_port) + ')')

    try:
        server_ip = socket.gethostbyname(server_name)
    except socket.gaierror:
        # could not resolve
        print('Hostname could not be resolved. Exiting')
        sys.exit()

    client_socket.connect((server_ip, server_port_number))

    print('Socket connected to ' + server_name + ' on IP ' + server_ip)

    current_book = ''

    #   client_socket.send('intro')
    # client_socket.send(mode + ' ' + polling_interval + ' ' + user_name)

    while 1:
        user_command = str(raw_input(''))
        command = user_command.split(' ')[0]

        if command == 'display':
            print(user_command)
            current_book = user_command.split(' ')[1]
            try:
                client_socket.sendall(user_command + ' ' + user_name)
                print('request sent')
            except socket.error, msg:
                # Send failed
                print('Error code: ' + str(msg[0]) +
                      ' , Error message: ' + msg[1])
                sys.exit()

            server_response = client_socket.recv(1024)
            print(server_response)
            # client_socket.sendall('stop')

        elif command == 'post_to_forum':
            continue
        elif command == 'read_post':
            continue
        elif command == 'q':
            break
        else:
            print("Incorrect command, please try again")

    client_socket.close()

if __name__ == '__main__':
    main()
