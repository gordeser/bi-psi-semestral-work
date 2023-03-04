import threading
from enum import Enum
import socket
import sys

SERVER = '127.0.0.1'
PORT = int(sys.argv[1])


class Messages(Enum):
    SERVER_MOVE = '102 MOVE\a\b'
    SERVER_TURN_LEFT = '103 TURN LEFT\a\b'
    SERVER_TURN_RIGHT = '104 TURN RIGHT\a\b'
    SERVER_PICK_UP = '105 GET MESSAGE\a\b'
    SERVER_LOGOUT = '106 LOGOUT\a\b'
    SERVER_KEY_REQUEST = '107 KEY REQUEST\a\b'
    SERVER_OK = '200 OK\a\b'
    SERVER_LOGIN_FAILED = '300 LOGIN FAILED\a\b'
    SERVER_SYNTAX_ERROR = '301 SYNTAX ERROR\a\b'
    SERVER_LOGIC_ERROR = '302 LOGIC ERROR\a\b'
    SERVER_KEY_OUT_OF_RANGE_ERROR = '303 KEY OUT OF RANGE\a\b'


# (server_key, client_key)
server_keys = [23019, 32037, 18789, 16443, 18189]
client_keys = [32037, 29295, 13603, 29533, 21952]

data = ''


def check_username(username: str) -> bool:
    if len(username) <= 18:
        return True
    return False


def check_key_id(key_id: int) -> bool:
    if 0 <= key_id <= 4:
        return True
    return False


def count_hash(username: str) -> int:
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * 1000) % 65536
    return _hash


def count_server_confirmation(_hash: int, key_id: int) -> int:
    return (_hash + server_keys[key_id]) % 65536


def count_client_confirmation(_hash: int, key_id: int) -> int:
    return (_hash + client_keys[key_id]) % 65536


def get_data(connection: socket.socket) -> str:
    global data
    while data.find('\a\b') == -1:
        buf = connection.recv(1024)
        data += buf.decode('ascii')
    pos = data.find('\a\b')
    message = data[0:data.find('\a\b')]
    data = data[pos + 2:]
    return message


def send_data(connection: socket.socket, message: str):
    connection.send(bytes(message, 'ascii'))


def auth(connection: socket.socket) -> bool:
    username = get_data(connection)  # CLIENT_USERNAME
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # SERVER_KEY_REQUEST
    key_id = int(get_data(connection))  # CLIENT_KEY_ID
    if not check_key_id(key_id):
        send_data(connection, Messages.SERVER_KEY_OUT_OF_RANGE_ERROR.value)
        return False
    _hash = count_hash(username)
    server_confirmation = count_server_confirmation(_hash, key_id)
    send_data(connection, str(server_confirmation) + '\a\b')  # SERVER_CONFIRMATION
    check_client_confirmation = int(get_data(connection))  # CLIENT_CONFIRMATION
    client_confirmation = count_client_confirmation(_hash, key_id)
    if check_client_confirmation != client_confirmation:
        send_data(connection, Messages.SERVER_LOGIN_FAILED.value)  # SERVER_LOGIN_FAILED
        return False
    send_data(connection, Messages.SERVER_OK.value)  # SERVER_OK
    return True


def get_coords(connection: socket.socket) -> list:
    buf = get_data(connection)
    coords = []
    for coord in buf.split():
        try:
            coords.append(int(coord))
        except ValueError:
            pass
    return coords


def move(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_MOVE.value)
    coords = get_coords(connection)
    return coords


def turn_left(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_TURN_LEFT.value)
    coords = get_coords(connection)
    return coords


def turn_right(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_TURN_RIGHT.value)
    coords = get_coords(connection)
    return coords


def target(connection: socket.socket) -> None:
    try:
        if not auth(connection):
            connection.close()
            return
    except:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()


def main():
    server = socket.socket()
    try:
        server.bind((SERVER, PORT))
    except OSError as e:
        print(e)
        exit()
    server.listen()
    print(f"Start listening on {SERVER}:{PORT}")
    while True:
        connection, address = server.accept()
        thread = threading.Thread(target=target, args=[connection])
        thread.start()


if __name__ == '__main__':
    main()
