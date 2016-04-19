import copy
import socket
import sys
from thread import *
from threading import Timer

RECV_BUFFER = 4096

cur_book = ''
read_posts = {}
unread_posts = {}
old_unread_posts = {}
client_socket = ''
pull_thread = ''
push_thread = ''
chat_peer = ()


class RepeatingTimer:
    def __init__(self, t, h_function):
        self.t = t
        self.hFunction = h_function
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


def get_available_port():
    """
    Find avaialble port on the client
    :return: (int) available port number
    """
    c_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c_s.bind(('', 0))
    port = c_s.getsockname()[1]
    c_s.close()
    return port


def pull_mode():
    update_post()
    if not cmp(old_unread_posts, unread_posts):
        # print('No new post')
        pass
    else:
        print('There are new posts.')


def post_to_forum(line_number, pos):
    """
    Send a request to post to forum
    :param line_number:
    :param pos:
    :return: none
    """
    try:
        client_socket.sendall(
            'p;' + cur_book + ';' + cur_page_number + ';' + line_number + ';' + pos)

        # wait for server response
        response = client_socket.recv(RECV_BUFFER)
        print(response + '\n')
    except socket.error, msg_:
        # Send failed
        print('Error code: ' + str(msg_[0]) +
              ' , Error message: ' + msg_[1])
        sys.exit()


def update_post():
    """
    Update database discussion on a particular book and page
    :return:
    """
    try:
        # request all post ids associated with the book
        # and page number
        client_socket.sendall(
            'c;' + cur_book + ';' + cur_page_number)

        post_ids = client_socket.recv(RECV_BUFFER)
        if post_ids != '0':
            post_ids = str(post_ids).split(';')
            for post_id in post_ids:
                if (cur_book + cur_page_number) in read_posts:
                    # Check whether the post already read by user
                    for read_post in read_posts[
                                cur_book + cur_page_number]:
                        if read_post[0] == post_id:
                            break
                    else:
                        # Request post detail for unread post id
                        client_socket.sendall(
                            'g;' + cur_book + ';' + cur_page_number + ';' + post_id)

                        post = client_socket.recv(RECV_BUFFER)
                        post = str(post).split(';')

                        if (cur_book + cur_page_number) in unread_posts:
                            for unread_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if unread_post[0] == post_id:
                                    break
                            else:
                                unread_posts[
                                    cur_book + cur_page_number].append(
                                    post)
                        else:
                            unread_posts[
                                cur_book + cur_page_number] = [post]
                # No entry in read_post for cur_book and page_number
                else:
                    client_socket.sendall(
                        'g;' + cur_book + ';' + cur_page_number + ';' + post_id)

                    post = client_socket.recv(RECV_BUFFER)
                    post = str(post).split(';')

                    if (cur_book + cur_page_number) in unread_posts:
                        for unread_post in unread_posts[
                                    cur_book + cur_page_number]:
                            if unread_post[0] == post_id:
                                break
                        else:
                            unread_posts[
                                cur_book + cur_page_number].append(
                                post)
                    else:
                        unread_posts[
                            cur_book + cur_page_number] = [post]
    except socket.error, msg:
        # Send failed
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()


def push_listener(port_number):
    try:
        push_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        push_socket.bind(('', port_number))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    push_socket.listen(1)

    while True:
        try:
            conn, addr = push_socket.accept()
        except socket.timeout:
            print('Timed out waiting for a connection')
            continue

        push_update = conn.recv(RECV_BUFFER)

        book_name, page_number, post_id, username, line_number, post_content = str(
            push_update).split(';')

        if (book_name + page_number) in unread_posts:
            unread_posts[
                book_name + page_number].append(
                [post_id, user_name, line_number, post_content])
        else:
            unread_posts[
                book_name + page_number] = [[post_id, user_name, line_number,
                                             post_content]]

        # print(unread_posts)

        if cur_book and cur_page_number:
            if cur_book == book_name and cur_page_number == page_number:
                print('There are new posts.')

        conn.close()

        # print(addr[0] + ': ' + str(addr[1]) + ' is connected')

    push_socket.close()


def chat_request_listener(port_number):
    try:
        chat_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_request.bind(('', port_number))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    chat_request.listen(1)

    while True:
        try:
            conn, addr = chat_request.accept()
        except socket.timeout:
            print('Timed out waiting for a connection')
            continue

        username = conn.recv(RECV_BUFFER)
        print('Chat request from ' + username + '. Accept? [y/n]')

        break

    chat_request.close()


def chat_receiver(port_number):
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chat_socket.bind(('', port_number))
    while 1:
        message, sender_address = chat_socket.recvfrom(RECV_BUFFER)
        print(message)
        # reply = raw_input('')
        # if reply == 'stop':
        #     break
        # chat_receiver.sendto(reply, sender_address)




if __name__ == '__main__':
    # TODO: Validate user input
    # mode: push or pull
    # polling_interval: integer
    # user_name: string
    # server_name: string
    # server_port_number: integer 1024-65535

    mode = str(sys.argv[1])
    polling_interval = str(sys.argv[2])
    user_name = str(sys.argv[3])
    server_name = str(sys.argv[4])
    server_port_number = int(sys.argv[5])

    available_port = get_available_port()

    ch_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the client to available port
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

    chat_port = get_available_port()
    start_new_thread(chat_request_listener, (chat_port,))

    # Identify client
    client_socket.sendall(
        's;' + user_name + ';' + mode + ';' + polling_interval + ';' + str(
            chat_port))
    server_response = client_socket.recv(RECV_BUFFER)

    if server_response != 'ok':
        sys.exit()
    else:
        print('Login as ' + user_name + '\n')

    if mode == 'push':
        listener_port = get_available_port()
        client_socket.sendall(str(listener_port))
        start_new_thread(push_listener, (listener_port,))

    while 1:
        user_command = str(raw_input(''))
        user_command = user_command.split(' ')

        request = user_command[0].upper()

        if request == 'DISPLAY':
            if mode == 'pull':
                cur_book, cur_page_number = user_command[1], user_command[2]
                try:
                    client_socket.sendall(
                        'd;' + cur_book + ';' + cur_page_number)

                    ebook = str(client_socket.recv(RECV_BUFFER))

                    update_post()

                    i = 1
                    display_ebook = ''
                    for line in ebook.splitlines():
                        if (cur_book + cur_page_number) in unread_posts:
                            for unread_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if int(unread_post[2]) == i:
                                    line = 'n' + line[1:]
                                    display_ebook += line + '\n'
                                    break
                            else:
                                if (cur_book + cur_page_number) in read_posts:
                                    for read_post in read_posts[
                                                cur_book + cur_page_number]:
                                        if int(read_post[2]) == i:
                                            line = 'm' + line[1:]
                                            display_ebook += line + '\n'
                                            break
                                    else:
                                        display_ebook += line + '\n'
                                else:
                                    display_ebook += line + '\n'
                        else:
                            display_ebook += line + '\n'
                        i += 1
                    if not display_ebook:
                        print('File not found')
                    else:
                        print(display_ebook)

                    old_unread_posts = copy.deepcopy(unread_posts)

                    if not pull_thread:
                        pull_thread = RepeatingTimer(int(polling_interval),
                                                     pull_mode)
                        pull_thread.start()
                    else:
                        pull_thread.cancel()
                        pull_thread = RepeatingTimer(int(polling_interval),
                                                     pull_mode)
                        pull_thread.start()
                except socket.error, msg:
                    # Send failed
                    print('Error code: ' + str(msg[0]) +
                          ' , Error message: ' + msg[1])
                    sys.exit()
            elif mode == 'push':
                cur_book, cur_page_number = user_command[1], user_command[2]
                try:
                    client_socket.sendall(
                        'd;' + cur_book + ';' + cur_page_number)

                    ebook = str(client_socket.recv(RECV_BUFFER))

                    i = 1
                    display_ebook = ''
                    for line in ebook.splitlines():
                        if (cur_book + cur_page_number) in unread_posts:
                            for unread_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if int(unread_post[2]) == i:
                                    line = 'n' + line[1:]
                                    display_ebook += line + '\n'
                                    break
                            else:
                                if (cur_book + cur_page_number) in read_posts:
                                    for read_post in read_posts[
                                                cur_book + cur_page_number]:
                                        if int(read_post[2]) == i:
                                            line = 'm' + line[1:]
                                            display_ebook += line + '\n'
                                            break
                                    else:
                                        display_ebook += line + '\n'
                                else:
                                    display_ebook += line + '\n'
                        else:
                            display_ebook += line + '\n'
                        i += 1
                    if not display_ebook:
                        print('File not found')
                    else:
                        print(display_ebook)
                except socket.error, msg:
                    # Send failed
                    print('Error code: ' + str(msg[0]) +
                          ' , Error message: ' + msg[1])
                    sys.exit()
        # Post_to_forum line_number content_of_post
        elif request == 'POST_TO_FORUM':
            content_of_post = ' '.join(user_command[2:])
            line_number = int(user_command[1])
            if cur_book != '' and cur_page_number != '':
                post_to_forum(str(line_number), content_of_post)
            else:
                print('Unable to post, no ebook opened.\n')
        # Read unread post on certain line number
        elif request == 'READ_POST':
            update_post()

            post_to_read = []
            if unread_posts:
                i = 0
                del_index = []
                for unread_post in unread_posts[cur_book + cur_page_number]:
                    if unread_post[2] == str(user_command[1]):
                        post_to_read.append(unread_post)
                        if cur_book + cur_page_number in read_posts:
                            read_posts[
                                cur_book + cur_page_number].append(
                                unread_post)
                        else:
                            read_posts[cur_book + cur_page_number] = [
                                unread_post]
                        del_index.append(i)
                        i -= 1
                    i += 1
                # print(del_index)
                for i in del_index:
                    unread_posts[cur_book + cur_page_number].pop(i)

            old_unread_posts = copy.deepcopy(unread_posts)

            if not post_to_read:
                print('No new post\n')
            else:
                print(post_to_read)
        elif request == 'CHAT_REQUEST':
            client_socket.sendall('chat' + ';' + user_command[1])

            server_response = client_socket.recv(RECV_BUFFER).split(';')
            chat_peer = tuple(server_response)
            print(chat_peer)
            print('Ready to chat')
            start_new_thread(chat_receiver, (chat_port,))

        elif request == 'Y':

            client_socket.sendall(request.lower())

            server_response = client_socket.recv(RECV_BUFFER).split(';')
            chat_peer = tuple(server_response)
            print(chat_peer)
            print('Ready to chat')
            start_new_thread(chat_receiver, (chat_port,))

        elif request == 'N':
            client_socket.sendall(request.lower())

        elif request == "CHAT":
            print(request)
            ch_socket.sendto(' '.join(user_command[2:]),
                             (chat_peer[0], int(chat_peer[1])))
        elif request == 'Q':
            client_socket.sendall('q')
            if pull_thread:
                pull_thread.cancel()
            print('Close client')
            break
        else:
            print("Incorrect command, please try again")

    client_socket.close()
