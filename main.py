import threading
from enum import Enum
import socket
import sys

SERVER = '127.0.0.1'
PORT = int(sys.argv[1])
ENDING = '\a\b'


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
    while data.find(ENDING) == -1:
        data += connection.recv(1024).decode('ascii')
    pos = data.find(ENDING)
    message = data[0:pos]
    data = data[pos + 2:]
    return message


def send_data(connection: socket.socket, message: str):
    connection.send(bytes(message, 'ascii'))


def auth(connection: socket.socket) -> bool:
    username = get_data(connection)  # CLIENT_USERNAME
    if not check_username(username):
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        return False
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # SERVER_KEY_REQUEST
    key_id = int(get_data(connection))  # CLIENT_KEY_ID
    if not check_key_id(key_id):
        send_data(connection, Messages.SERVER_KEY_OUT_OF_RANGE_ERROR.value)
        return False
    _hash = count_hash(username)
    server_confirmation = count_server_confirmation(_hash, key_id)
    send_data(connection, str(server_confirmation) + ENDING)  # SERVER_CONFIRMATION
    check_client_confirmation = get_data(connection)  # CLIENT_CONFIRMATION
    if len(check_client_confirmation) != len(str(int(check_client_confirmation))):
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        return False
    if len(str(check_client_confirmation)) > 5:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        return False
    check_client_confirmation = int(check_client_confirmation)
    client_confirmation = count_client_confirmation(_hash, key_id)
    if check_client_confirmation != client_confirmation:
        send_data(connection, Messages.SERVER_LOGIN_FAILED.value)  # SERVER_LOGIN_FAILED
        return False
    send_data(connection, Messages.SERVER_OK.value)  # SERVER_OK
    return True


def get_coords(connection: socket.socket):
    buffer = get_data(connection)
    if '.' in buffer:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False
    if buffer.count(' ') > 2:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False

    coords = []
    for coord in buffer.split():
        try:
            coords.append(int(coord))
        except ValueError:
            pass
    return coords


def make_move(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_MOVE.value)
    return get_coords(connection)


def turn_left(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_TURN_LEFT.value)
    return get_coords(connection)


def turn_right(connection: socket.socket) -> list:
    send_data(connection, Messages.SERVER_TURN_RIGHT.value)
    return get_coords(connection)


def get_direction_and_coords(connection: socket.socket) -> list:
    first_coords = make_move(connection)
    second_coords = make_move(connection)
    x = first_coords[0] - second_coords[0]
    y = first_coords[1] - second_coords[1]
    direction = ""
    if x == 0 and y == -1:
        direction = "UP"
    if x == 0 and y == 1:
        direction = "DOWN"
    if x == -1 and y == 0:
        direction = "RIGHT"
    if x == 1 and y == 0:
        direction = "LEFT"
    if x == 0 and y == 0:
        # todo: handle obstacle
        pass
    return [second_coords, direction]


def turn_around(connection: socket.socket) -> None:
    turn_left(connection)
    turn_left(connection)


def make_left(connection: socket.socket, direction: str) -> str:
    if direction == "UP":
        turn_left(connection)
    elif direction == "RIGHT":
        turn_around(connection)
    elif direction == "DOWN":
        turn_right(connection)
    return "LEFT"


def make_right(connection: socket.socket, direction: str) -> str:
    if direction == "UP":
        turn_right(connection)
    elif direction == "LEFT":
        turn_around(connection)
    elif direction == "DOWN":
        turn_left(connection)
    return "RIGHT"


def make_up(connection: socket.socket, direction: str) -> str:
    if direction == "LEFT":
        turn_right(connection)
    elif direction == "RIGHT":
        turn_left(connection)
    elif direction == "DOWN":
        turn_around(connection)
    return "UP"


def make_down(connection: socket.socket, direction: str) -> str:
    if direction == "UP":
        turn_around(connection)
    elif direction == "RIGHT":
        turn_right(connection)
    elif direction == "LEFT":
        turn_left(connection)
    return "DOWN"


def make_zero_x(connection: socket.socket, current_position: list, direction: str) -> list:
    cur_pos = current_position
    if cur_pos[0] > 0:
        direction = make_left(connection, direction)
    elif cur_pos[0] < 0:
        direction = make_right(connection, direction)
    while cur_pos[0] != 0:
        last_pos = cur_pos
        cur_pos = make_move(connection)
        if last_pos == cur_pos:
            print("[X] THERE IS SOMETHING IN FRONT OF ME", direction)
    return [cur_pos, direction]


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
