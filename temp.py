import socket
from enum import Enum


class Messages(Enum):
    SERVER_MOVE = b'102 MOVE\a\b'
    SERVER_TURN_LEFT = b'103 TURN LEFT\a\b'
    SERVER_TURN_RIGHT = b'104 TURN RIGHT\a\b'
    SERVER_PICK_UP = b'105 GET MESSAGE\a\b'
    SERVER_LOGOUT = b'106 LOGOUT\a\b'
    SERVER_KEY_REQUEST = b'107 KEY REQUEST\a\b'
    SERVER_OK = b'200 OK\a\b'
    SERVER_LOGIN_FAILED = b'300 LOGIN FAILED\a\b'
    SERVER_SYNTAX_ERROR = b'301 SYNTAX ERROR\a\b'
    SERVER_LOGIC_ERROR = b'302 LOGIC ERROR\a\b'
    SERVER_KEY_OUT_OF_RANGE_ERROR = b'303 KEY OUT OF RANGE\a\b'


server_keys = [23019, 32037, 18789, 16443, 18189]
client_keys = [32037, 29295, 13603, 29533, 21952]


def count_keys(username, key_id):
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * 1000) % 65536
    server_hash = (_hash + server_keys[key_id]) % 65536
    client_hash = (_hash + client_keys[key_id]) % 65536

    return server_hash, client_hash


def get_username(connection):
    buf = b''
    while list(buf[-2:]) != [7, 8]:
        buf += connection.recv(1)
    data = list(buf)
    username = []
    flag = 0
    for i in data:
        if i == 7 and flag == 0:
            flag = 1
        elif i == 8 and flag == 1:
            flag = 2
        else:
            username.append(i)
    if flag == 2:
        username = [chr(i) for i in username]
    return "".join(username)


def get_id(connection):
    buf = b''
    while list(buf[-2:]) != [7, 8]:
        buf += connection.recv(1)
    print(buf)
    data = list(buf)
    client_id = []
    flag = 0
    for i in data:
        if i == 7 and flag == 0:
            flag = 1
        elif i == 8 and flag == 1:
            flag = 2
        else:
            client_id.append(i)
    if flag == 2:
        client_id = "".join([chr(i) for i in client_id])

    return int(client_id)


def get_client_key(connection):
    buf = b''
    while list(buf[-2:]) != [7, 8]:
        buf += connection.recv(1)
    data = list(buf)
    client_key = []
    flag = 0
    for i in data:
        if i == 7 and flag == 0:
            flag = 1
        elif i == 8 and flag == 1:
            flag = 2
        else:
            client_key.append(i)
    if flag == 2:
        client_key = "".join([chr(i) for i in client_key])
    return int(client_key)


def main():
    global keys
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('192.168.56.1', 12346))
        sock.listen(5)
        print("server has started")
    except Exception as e:
        print(e)
        exit(-1)

    while True:
        connection, address = sock.accept()
        # Authenticate
        # todo: get username function
        # todo: send SERVER_KEY_REQUEST
        # todo: get id that must be in range(0, 5)
        # todo: send SERVER_CONFIRMATION (server id) or SERVER_KEY_OUT_OF_RANGE_ERROR (if it is not in range 0-4) or SERVER_SYNTAX_ERROR (if client_id is not a number)
        # todo: get client key and check if it is right
        # todo: send SERVER_OK or SERVER_LOGIN_FAILED (if client key is wrong) or SERVER_SYNTAX_ERROR (if client key is not a number)
        username = get_username(connection)
        connection.sendall(Messages.SERVER_KEY_REQUEST.value)

        client_id = get_id(connection)
        if 0 <= client_id <= 4:
            keys = count_keys(username, client_id)
            connection.sendall(bytes(str(keys[0]), 'utf-8') + b'\a\b')
            print('sent')
        else:
            print(client_id)
            connection.sendall(Messages.SERVER_KEY_OUT_OF_RANGE_ERROR.value)
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            continue

        client_key = get_client_key(connection)
        if client_key == keys[1]:
            connection.send(Messages.SERVER_OK.value)
        else:
            connection.send(Messages.SERVER_LOGIN_FAILED.value)
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()
            continue

        # auth has completed

        connection.send(Messages.SERVER_MOVE.value)
        connection.close()


if __name__ == '__main__':
    main()
