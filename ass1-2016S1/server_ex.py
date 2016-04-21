import pickle
import socket
import sys
import time
import uuid
from thread import *

RECV_BUFFER = 4096
# dict with key ip:port_number and value: username, mode, polling_int, chat_port
clients = dict()
# key: book_name+page_number
# value: [post_id, username, line_number, post]
discussions = dict()
# dict with key username and value: [posts_id]
read_posts = dict()
# [ip_address, port_number, username]
push_list = []

requester = ()
target = ()
target_acceptance = False


def get_post(book_name, page_number, post_id):
    """
    Get specific post based on post_id
    :param book_name:
    :param page_number:
    :param post_id:
    :return: (array) post
    """
    for post in discussions[book_name + page_number]:
        if post[0] == post_id:
            return ';'.join(post)
    else:
        return '0'


def get_post_ids(book_name, page_number):
    """
    Get post ids associated with book_name + page_number
    :param book_name:
    :param page_number:
    :return: (array) post ids
    """
    try:
        posts = discussions[book_name + page_number]
        post_ids = ''
        for post in posts:
            post_ids += post[0] + ';'
    except KeyError:
        return '0'
    else:
        return post_ids[:-1]


def get_ebook(book_name, page_number):
    """
    Get ebook from file
    :param book_name: string
    :param page_number: string
    :return: (string) ebook
    """
    try:
        ebook_file = open(book_name + '_page' + page_number, 'r')
        ebook = ebook_file.read()
    except IOError:
        print('File not found')
        return False
    else:
        ebook_file.close()
        return ebook


def push_notification(book_name, page_number, post):
    """
    Send notification to all push_list client
    :param book_name:
    :param page_number:
    :param post:
    :return:
    """
    push_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for client_ip_address, client_port_listener, username in push_list:
        push_socket.connect((client_ip_address, client_port_listener))
        push_socket.sendall(
            book_name + ';' + page_number + ';' + str(post[0]) + ';' +
            post[1] + ';' + str(post[2]) + ';' + post[3])
        push_socket.close()
        print('New post pushed to ' + username + '.')


def client_thread(client_conn, client_addr):
    """
    Spawned thread for each client
    :param client_conn: client connection
    :param client_addr: client address
    :return: none
    """

    global requester
    global target
    global target_acceptance

    # client_id = ip_address + port_number
    client_id = client_addr[0] + ':' + str(client_addr[1])
    client_ip_address = client_addr[0]
    client_port_number = client_addr[1]
    chat_port = 0
    username = ''
    mode = ''

    while True:
        data = client_conn.recv(RECV_BUFFER)
        if client_id in clients:
            print(clients[client_id][0] + ": " + data)

        data = data.split(';')
        request = data[0]

        # Setup request.
        # Format: 's', username, mode, polling_interval, chat_port
        if request == 's':
            username, mode, polling_interval, chat_port = data[1:]
            clients[client_id] = [username,
                                  mode,
                                  int(polling_interval),
                                  int(chat_port)]

            client_conn.sendall('ok')

            print(client_id + ' identified as ' +
                  username + ' [' + mode + ' mode]')

            if mode == 'push':
                notification_port = int(client_conn.recv(RECV_BUFFER))

                discussions_string = pickle.dumps(discussions)

                client_conn.sendall(discussions_string)
                data = client_conn.recv(RECV_BUFFER)

                if data == 'ok':
                    push_list.append(
                        [client_ip_address, notification_port, username])
                    print('Discussion data successfully sent to ' + username)
                    print(push_list)
                else:
                    print('Failed to send new posts')
        # Display request.
        # Format: 'd', book_name, page_number
        elif request == 'd':
            ebook = get_ebook(data[1], data[2])
            if not ebook:
                client_conn.sendall('File not found')
            else:
                client_conn.sendall(ebook)
        # Get all post_ids for book_name + page_number request.
        # Format: 'c', book_name, page_number
        elif request == 'c':
            post_ids = get_post_ids(data[1], data[2])
            client_conn.sendall(post_ids)
        # Post to discussion.
        # Format: 'p', book_name, page_number, line_number, content_of_post
        elif request == 'p':
            username = clients[client_id][0]
            post_id = str(uuid.uuid4())[:8]
            book_name, page_number, line_number, content = data[1:]
            post = [post_id, username, line_number, content]

            if get_ebook(book_name, page_number):
                if (book_name + page_number) in discussions:
                    discussions[book_name + page_number].append(post)
                else:
                    discussions[book_name + page_number] = [post]
                client_conn.sendall('Post #' + post_id + ' saved')

            print('New post received from ' + username + '.')
            print('Post added to the database and given serial number ' +
                  post_id + '.')

            # Push notification to push clients
            if push_list:
                push_notification(book_name, page_number, post)
            else:
                print('Push list empty. No action required.')
        # Get post detail for post_id.
        # Format: 'g', book_name, page_number, post_id
        elif request == 'g':
            post = get_post(data[1], data[2], data[3])
            if post:
                client_conn.sendall(post)
            else:
                client_conn.sendall('Post with ' + data[3] + 'not found')
        # Setup chat module
        # Format: 'chat', username
        elif request == 'chat':
            requester = (client_ip_address, client_port_number,
                         chat_port, username)
            target_username = data[1]

            print('Chat request from ' + username +
                  ' to talk to ' + target_username)

            for client in clients:
                client_detail = clients[client]
                if client_detail[0] == target_username:
                    target = (client_id.split(':')[0], client_detail[3])
                    chat_request = socket.socket(socket.AF_INET,
                                                 socket.SOCK_STREAM)
                    chat_request.connect(target)
                    chat_request.sendall(clients[client_id][0])
                    print('Chat request to ' + target_username +
                          ' has been sent')
                    chat_request.close()
                    break
            else:
                client_conn.sendall('0')
                continue

            # Wait for reply from target user
            time.sleep(10.0)

            if target_acceptance:
                print(target_username + ' accepted the chat request from ' +
                      username)
                client_conn.sendall(target[0] + ';' + str(target[1]))
            else:
                client_conn.sendall('0')
        # Target accept chat request
        elif request == 'y':
            target_acceptance = True
            client_conn.sendall(requester[0] + ';' + str(requester[2]) + ';' +
                                requester[3])
        # Target refuse chat request
        elif request == 'n':
            target_acceptance = False
        elif request == 'q':
            break
        else:
            client_conn.sendall(str(data))

    print(client_id + ' is disconnected.')

    # Remove disconnected push_list client
    if mode == 'push':
        for index in range(len(push_list)):
            if push_list[index][2] == username:
                print(push_list.pop(index)[2] + ' is removed from push list')
                break

    client_conn.close()


if __name__ == '__main__':
    server_port = int(sys.argv[1])

    if server_port < 1024:
        print('Reserved port, please pick another port number.')
        sys.exit()

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', server_port))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    server_socket.listen(10)
    print("The server is listening on port number " + str(server_port) + '.')
    print("The database for discussion posts has been initialised.")

    while True:
        try:
            conn, addr = server_socket.accept()
        except socket.timeout:
            print('Timed out waiting for a connection.')
            continue

        print(addr[0] + ':' + str(addr[1]) + ' is connected.')

        start_new_thread(client_thread, (conn, addr))

    server_socket.close()
