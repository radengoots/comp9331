import copy
import pickle
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
chat_peer = dict()


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
    """
    Check new post for cur_book and cur_page_number
    :return:
    """
    update_post()

    if (cur_book + cur_page_number) in old_unread_posts:
        if not cmp(old_unread_posts[cur_book + cur_page_number],
                   unread_posts[cur_book + cur_page_number]):
            # print('No new post')
            pass
        else:
            print('There are new posts.')
    elif (cur_book + cur_page_number) in unread_posts:
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
                    for r_post in read_posts[
                                cur_book + cur_page_number]:
                        if r_post[0] == post_id:
                            # Check next post_id
                            break
                    else:
                        # Request post detail for unread post id
                        client_socket.sendall(
                            'g;' + cur_book + ';' + cur_page_number + ';' + post_id)

                        post = client_socket.recv(RECV_BUFFER)
                        post = str(post).split(';')

                        if (cur_book + cur_page_number) in unread_posts:
                            for u_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if u_post[0] == post_id:
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
                        for u_post in unread_posts[
                                    cur_book + cur_page_number]:
                            if u_post[0] == post_id:
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

        book_name, page_number, post_id, username, l_number, post_content = str(
            push_update).split(';')

        if (book_name + page_number) in unread_posts:
            unread_posts[
                book_name + page_number].append(
                [post_id, user_name, l_number, post_content])
        else:
            unread_posts[
                book_name + page_number] = [[post_id, user_name, l_number,
                                             post_content]]

        if cur_book and cur_page_number:
            if cur_book == book_name and cur_page_number == page_number:
                print('There are new posts.')

        conn.close()

    push_socket.close()


def chat_request_listener(port_number):
    # TODO: Multiple chat peers
    """
    Listen to the chat request from server
    :param port_number:
    :return:
    """
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
    """
    Receive message sent by chatting peers
    :param port_number:
    :return:
    """
    chat_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    chat_socket.bind(('', port_number))
    while 1:
        message, sender_address = chat_socket.recvfrom(RECV_BUFFER)
        print(message)


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

    client_port = get_available_port()

    chat_listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the client to available port
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.bind(('', client_port))
    except socket.error, msg:
        print('Error code: ' + str(msg[0]) +
              ' , Error message: ' + msg[1])
        sys.exit()

    # Try to resolve server ip_address
    try:
        server_ip_address = socket.gethostbyname(server_name)
    except socket.gaierror:
        # could not resolve
        print('Hostname could not be resolved. Exiting')
        sys.exit()

    client_socket.connect((server_ip_address, server_port_number))

    print('Socket connected to ' + server_name + ' @' + server_ip_address)

    # Setup chat request listener thread
    chat_port = get_available_port()
    start_new_thread(chat_request_listener, (chat_port,))

    # Register client
    client_socket.sendall(
        's;' + user_name + ';' + mode + ';' + polling_interval + ';' + str(
            chat_port))
    server_response = client_socket.recv(RECV_BUFFER)

    if server_response != 'ok':
        sys.exit()
    else:
        print('Login as ' + user_name + '\n')

    # Push mode setup
    if mode == 'push':
        notification_port = get_available_port()
        client_socket.sendall(str(notification_port))

        unread_posts_string = client_socket.recv(RECV_BUFFER)

        try:
            unread_posts = pickle.loads(unread_posts_string)
        except:
            print('Error parsing data')
        else:
            client_socket.sendall('ok')
            start_new_thread(push_listener, (notification_port,))

    while 1:
        user_command = str(raw_input(''))
        user_command = user_command.split(' ')

        request = user_command[0].upper()

        # display book_name page_number
        if request == 'DISPLAY':
            if mode == 'pull':
                cur_book, cur_page_number = user_command[1], user_command[2]
                try:
                    client_socket.sendall(
                        'd;' + cur_book + ';' + cur_page_number)

                    ebook = str(client_socket.recv(RECV_BUFFER))

                    update_post()

                    cur_line_number = 1
                    displayed_ebook = ''
                    for cur_line in ebook.splitlines():
                        if (cur_book + cur_page_number) in unread_posts:
                            for unread_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if int(unread_post[2]) == cur_line_number:
                                    cur_line = 'n' + cur_line[1:]
                                    displayed_ebook += cur_line + '\n'
                                    break
                            else:
                                if (cur_book + cur_page_number) in read_posts:
                                    for read_post in read_posts[
                                                cur_book + cur_page_number]:
                                        if int(read_post[2]) == cur_line_number:
                                            cur_line = 'm' + cur_line[1:]
                                            displayed_ebook += cur_line + '\n'
                                            break
                                    else:
                                        displayed_ebook += cur_line + '\n'
                                else:
                                    displayed_ebook += cur_line + '\n'
                        else:
                            displayed_ebook += cur_line + '\n'
                        cur_line_number += 1
                    if not displayed_ebook:
                        print('File not found')
                    else:
                        print(displayed_ebook)

                    old_unread_posts = copy.deepcopy(unread_posts)

                    # Pull update
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
                    displayed_ebook = ''
                    for cur_line in ebook.splitlines():
                        if (cur_book + cur_page_number) in unread_posts:
                            for unread_post in unread_posts[
                                        cur_book + cur_page_number]:
                                if int(unread_post[2]) == i:
                                    cur_line = 'n' + cur_line[1:]
                                    displayed_ebook += cur_line + '\n'
                                    break
                            else:
                                if (cur_book + cur_page_number) in read_posts:
                                    for read_post in read_posts[
                                                cur_book + cur_page_number]:
                                        if int(read_post[2]) == i:
                                            cur_line = 'm' + cur_line[1:]
                                            displayed_ebook += cur_line + '\n'
                                            break
                                    else:
                                        displayed_ebook += cur_line + '\n'
                                else:
                                    displayed_ebook += cur_line + '\n'
                        else:
                            displayed_ebook += cur_line + '\n'
                        i += 1
                    if not displayed_ebook:
                        print('File not found')
                    else:
                        print(displayed_ebook)
                except socket.error, msg:
                    # Send failed
                    print('Error code: ' + str(msg[0]) +
                          ' , Error message: ' + msg[1])
                    sys.exit()
        # post_to_forum line_number content
        elif request == 'POST_TO_FORUM':
            content = ' '.join(user_command[2:])
            line_number = user_command[1]
            if cur_book != '' and cur_page_number != '':
                post_to_forum(line_number, content)
            else:
                print('Unable to post, no ebook opened.\n')
        # read_post line_number
        elif request == 'READ_POST':
            line_number = str(user_command[1])
            update_post()

            posts_to_read = []
            if unread_posts:
                i = 0
                del_index = []
                for unread_post in unread_posts[cur_book + cur_page_number]:
                    if unread_post[2] == line_number:
                        posts_to_read.append(unread_post)
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

            if not posts_to_read:
                print('No unread posts.\n')
            else:
                print('Book by ' + cur_book + ', Page ' + cur_page_number +
                      ', Line number ' + line_number + ':')
                for post in posts_to_read:
                    print(post[0] + ' ' + post[1] + ': ' + post[3])
        # chat_request username
        elif request == 'CHAT_REQUEST':
            client_socket.sendall('chat' + ';' + user_command[1])
            server_response = client_socket.recv(RECV_BUFFER).split(';')

            if server_response == ['0']:
                print('User not found or refused.')
            else:
                chat_peer[user_command[1]] = server_response

                print(user_command[1] + ' accept the request')
                print('Ready to chat')

                start_new_thread(chat_receiver, (chat_port,))
        # Target accept for chat request
        elif request == 'Y':
            client_socket.sendall(request.lower())
            server_response = client_socket.recv(RECV_BUFFER).split(';')

            chat_peer[server_response[2]] = server_response[:2]

            print('Ready to chat')

            start_new_thread(chat_receiver, (chat_port,))
        # Target refuse for chat request
        elif request == 'N':
            client_socket.sendall(request.lower())
        elif request == "CHAT":
            target = user_command[1]
            if target in chat_peer:
                chat_listener_socket.sendto(
                    user_name + ': ' + ' '.join(user_command[2:]),
                    (chat_peer[target][0], int(chat_peer[target][1])))
            else:
                print("You're not connected with " + target)
        elif request == 'Q':
            client_socket.sendall('q')
            if pull_thread:
                pull_thread.cancel()
            print('Close client')
            break
        else:
            print("Incorrect command, please try again")

    client_socket.close()
