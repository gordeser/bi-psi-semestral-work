import os
import threading
from enum import Enum
import socket
import sys

ENDING = '\a\b'
data = ""


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


def check_username(connection: socket.socket, username):
    if len(username) > 18:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()


def check_key_id(connection: socket.socket, key_id):
    if not (0 <= key_id <= 4):
        send_data(connection, Messages.SERVER_KEY_OUT_OF_RANGE_ERROR.value)
        connection.close()


def count_hash(username: str) -> int:
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * 1000) % 65536
    return _hash


def count_server_confirmation(_hash: int, key_id: int) -> int:
    return (_hash + server_keys[key_id]) % 65536


def count_client_confirmation(_hash: int, key_id: int) -> int:
    return (_hash + client_keys[key_id]) % 65536


def get_data(connection: socket.socket):
    global data
    connection.settimeout(1)
    try:
        while data.find(ENDING) == -1:
            data += connection.recv(1024).decode('ascii')
        pos = data.find(ENDING)
        message = data[0:pos]
        data = data[pos + 2:]
    except socket.timeout as e:
        print(e)
        connection.close()
        return False
    return message


def send_data(connection: socket.socket, message: str):
    connection.send(bytes(message, 'ascii'))


def auth(connection: socket.socket):
    username = get_data(connection)  # CLIENT_USERNAME
    check_username(connection, username)
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # SERVER_KEY_REQUEST
    key_id = int(get_data(connection))  # CLIENT_KEY_ID
    check_key_id(connection, key_id)
    _hash = count_hash(username)
    server_confirmation = count_server_confirmation(_hash, key_id)
    send_data(connection, str(server_confirmation) + ENDING)  # SERVER_CONFIRMATION
    check_client_confirmation = get_data(connection)  # CLIENT_CONFIRMATION
    if len(check_client_confirmation) != len(str(int(check_client_confirmation))):
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
    if len(str(check_client_confirmation)) > 5:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
    check_client_confirmation = int(check_client_confirmation)
    client_confirmation = count_client_confirmation(_hash, key_id)
    if check_client_confirmation != client_confirmation:
        send_data(connection, Messages.SERVER_LOGIN_FAILED.value)  # SERVER_LOGIN_FAILED
        connection.close()
    send_data(connection, Messages.SERVER_OK.value)  # SERVER_OK


def get_coords(connection: socket.socket):
    buffer = get_data(connection)
    if '.' in buffer:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()

    if buffer.count(' ') > 2:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()

    coords = []
    for coord in buffer.split():
        try:
            coords.append(int(coord))
        except ValueError:
            pass
    return coords


def move_forward(connection: socket.socket):
    send_data(connection, Messages.SERVER_MOVE.value)
    return get_coords(connection)


def turn_left(connection: socket.socket):
    send_data(connection, Messages.SERVER_TURN_LEFT.value)
    return get_coords(connection)


def turn_right(connection: socket.socket):
    send_data(connection, Messages.SERVER_TURN_RIGHT.value)
    return get_coords(connection)


def turn_around(connection: socket.socket):
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


def get_the_fuck_out_of_obstacle(connection: socket.socket):
    turn_right(connection)
    move_forward(connection)
    turn_left(connection)
    move_forward(connection)
    move_forward(connection)
    turn_left(connection)
    move_forward(connection)
    turn_right(connection)


def find_direction(previous_position, current_position):
    x = current_position[0] - previous_position[0]
    y = current_position[1] - current_position[1]
    direction = ""
    if (x > 0) and (y == 0):
        direction = "RIGHT"
    if (x < 0) and (y == 0):
        direction = "LEFT"
    if (x == 0) and (y > 0):
        direction = "UP"
    if (x == 0) and (y < 0):
        direction = "DOWN"
    # there is no case x == 0 and y == 0 (obstacle)
    return direction


def find_side(connection: socket.socket, previous_position, current_position):
    # todo: implementation
    pass


def handle_robot(connection: socket.socket):
    previous_position: str
    current_position = get_coords(connection)
    while current_position != [0, 0]:
        previous_position, current_position = current_position, move_forward(connection)
        if previous_position == current_position:
            get_the_fuck_out_of_obstacle(connection)
        else:
            find_side(connection, previous_position, current_position)
    send_data(connection, Messages.SERVER_PICK_UP.value)
    get_data(connection)
    send_data(connection, Messages.SERVER_LOGOUT.value)
    connection.close()


def target(connection: socket.socket):
    # try:
    auth(connection)
    handle_robot(connection)
    # except Exception as e:
    #     print(e)
    #     send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
    connection.close()


def main():
    HOST = '127.0.0.1'
    PORT = int(sys.argv[1])
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solve "Address already in use"
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Start listening on {HOST}:{PORT}")
    while True:
        print('----------------------------')
        connection, address = server.accept()
        thread = threading.Thread(target=target, args=[connection])
        thread.start()


if __name__ == '__main__':
    main()
