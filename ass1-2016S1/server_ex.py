import socket
import sys
import uuid
from thread import *

RECV_BUFFER = 4096
# dict with key ip:port_number and value: username, mode, polling_int
clients = dict()
# dict with key book_name_page_number
# and value: [post_id, username, line_number, post]
discussions = dict()
# dict with key username and value: [posts_id]
read_posts = dict()
push_list = []


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
            print post
            post_ids += post[0] + ';'
    except KeyError:
        return '0'
    else:
        return post_ids[:-1]


def get_ebook(book_name, page_number, id_, mode):
    """
    Get ebook from file
    :param book_name: string
    :param page_number: string
    :param id_:
    :param mode:
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


def push_notification(book_name, page_number, post_content):
    push_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for push_client in push_list:
        push_socket.connect((push_client[0], push_client[1]))
        push_socket.sendall(
            book_name + ';' + page_number + ';' + str(post_content[0]) + ';' +
            post_content[1] + ';' + str(post_content[2]) + ';' + post_content[
                3])
        push_socket.close()


def client_thread(conn_, addr_):
    """
    Spawned thread for each client
    :param conn_: client connection
    :param addr_: client address
    :return: none
    """

    # client_id = ip_address + port_number
    client_id = addr_[0] + ':' + str(addr_[1])
    while True:
        data = conn_.recv(RECV_BUFFER)
        print(client_id + ": " + data)

        data = data.split(';')
        request = data[0]

        # Setup request in format: 's', username, mode, polling_interval
        if request == 's':
            clients.update({client_id: [data[1],
                                        data[2],
                                        int(data[3])]})
            conn_.sendall('ok')
            if data[2] == 'push':
                listener_port = int(conn_.recv(RECV_BUFFER))
                push_list.append([addr_[0], listener_port])
                print(push_list)
        # Display request in format: 'd', username, book_name, page_number
        elif request == 'd':
            ebook = get_ebook(data[1], data[2], client_id,
                              clients[client_id][1])
            if not ebook:
                conn_.sendall('File not found')
            else:
                conn_.sendall(ebook)
        # Check post request in format: 'c', book_name, page_number
        elif request == 'c':
            post_ids = get_post_ids(data[1], data[2])
            conn_.sendall(post_ids)
        # Post to discussion in format: 'p', book_name, page_number,
        #                               line_number, content_of_post
        elif request == 'p':
            username = clients[client_id][0]
            post_id = str(uuid.uuid4())[:8]
            if get_ebook(data[1], data[2], client_id,
                         username[1]):
                if data[1] + data[2] in discussions:
                    discussions[data[1] + data[2]].append(
                        [post_id, username, data[3],
                         data[4]])
                else:
                    discussions[data[1] + data[2]] = [[
                        post_id,
                        username,
                        data[3],
                        data[4]]]
                print(discussions)
                conn_.sendall('Post #' + post_id + ' saved')
            if push_list:
                push_notification(data[1], data[2],
                                  [post_id, username, data[3],
                                   data[4]])

        # Get post request in format: 'g', book_name, page_number, post_id
        elif request == 'g':
            post = get_post(data[1], data[2], data[3])
            if post:
                conn_.sendall(post)
            else:
                conn_.sendall('Post not found')
        # Setup chat module
        elif request == 'chat':
            pass
        elif request == 'q':
            break
        else:
            conn_.sendall(str(data))

    print(client_id + ' is disconnected')
    conn_.close()


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
    print("The server is listening on port number " + str(server_port))
    print("The database for discussion posts has been initialised")

    while True:
        try:
            print('Ready to receive')
            conn, addr = server_socket.accept()
        except socket.timeout:
            print('Timed out waiting for a connection')
            continue

        print(addr[0] + ': ' + str(addr[1]) + ' is connected')

        start_new_thread(client_thread, (conn, addr))

    server_socket.close()
