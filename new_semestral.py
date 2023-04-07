import socket
import threading
import sys
from enum import Enum

HOST = "127.0.0.1"
try:
    PORT = int(sys.argv[1])
except:
    PORT = 1234

TIMEOUT = 1
TIMEOUT_RECHARGING = 5
ENDING = "\a\b"

MULTIPLY = 1000
MODULO = 65536

SERVER_KEYS = [23019, 32037, 18789, 16443, 18189]
CLIENT_KEYS = [32037, 29295, 13603, 29533, 21952]


class Messages(Enum):
    SERVER_MOVE = "102 MOVE"
    SERVER_TURN_LEFT = "103 TURN LEFT"
    SERVER_TURN_RIGHT = "104 TURN RIGHT"
    SERVER_PICK_UP = "105 GET MESSAGE"
    SERVER_LOGOUT = "106 LOGOUT"
    SERVER_KEY_REQUEST = "107 KEY REQUEST"
    SERVER_OK = "200 OK"
    SERVER_LOGIN_FAILED = "300 LOGIN FAILED"
    SERVER_SYNTAX_ERROR = "301 SYNTAX ERROR"
    SERVER_LOGIC_ERROR = "302 LOGIC ERROR"
    SERVER_KEY_OUT_OF_RANGE_ERROR = "303 KEY OUT OF RANGE"


def get_data(connection, data, maxlen=100):
    while data[0].find(ENDING) == -1:
        data[0] += connection.recv(1024).decode('ascii')

        if len(data[0]) >= maxlen and ENDING not in data[0]:
            print(f"[{data[2]}] EXCEEDED MAXLEN: {data[0]}")
            send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
            connection.close()
            return False

    pos = data[0].find(ENDING)
    message = data[0][:pos]
    data[0] = data[0][pos + 2:]
    if message == "RECHARGING":
        print(f"[{data[2]}] RECHARGING...")

        data[1] = True
        connection.settimeout(TIMEOUT_RECHARGING)
        full_power = get_data(connection, data, 12)
        if full_power != "FULL POWER":
            send_data(connection, Messages.SERVER_LOGIC_ERROR.value)
            print(f"[{data[2]}] FAILED RECHARGING")
            connection.close()
            return False
        else:
            print(f"[{data[2]}] DONE RECHARGING")
            data[1] = False
            new_message = get_data(connection, data, maxlen)
            print(f"[{data[2]}] DATA AFTER RECHARGING: {new_message}")
            return new_message

    if len(message) > maxlen - 2:
        print(f"[{data[2]}] EXCEEDED MAXLEN: {data[0]}")
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False

    return message


def send_data(connection, data):
    connection.send(bytes(str(data) + ENDING, 'utf-8'))


def count_hash(username):
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * MULTIPLY) % MODULO
    return _hash


def count_server_confirmation(_hash, key_id):
    return (_hash + SERVER_KEYS[key_id]) % MODULO


def count_client_confirmation(_hash, key_id):
    return (_hash + CLIENT_KEYS[key_id]) % MODULO


def check_key_id(key_id):
    return 0 <= key_id <= 4


def auth(connection, data):
    username = get_data(connection, data, 20)  # CLIENT_USERNAME --->
    print(f"[{data[2]}] USERNAME: {username}")
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # <--- SERVER_KEY_REQUEST
    key_id = get_data(connection, data, 5)
    try:
        key_id = int(key_id)  # CLIENT_KEY_ID --->
    except ValueError:
        print(f"[{data[2]}] WRONG KEY_ID: {key_id}")
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False
    if not check_key_id(key_id):
        send_data(connection, Messages.SERVER_KEY_OUT_OF_RANGE_ERROR.value)
        print(f"[{data[2]}] WRONG KEY_ID: {key_id}")
        connection.close()
        return False
    print(f"[{data[2]}] KEY_ID: {key_id}")
    _hash = count_hash(username)
    print(f"[{data[2]}] COUNTED HASH: {_hash}")
    server_confirmation = count_server_confirmation(_hash, key_id)
    client_confirmation = count_client_confirmation(_hash, key_id)
    print(f"[{data[2]}] CONFIRMS: SERVER {server_confirmation} and CLIENT {client_confirmation}")
    send_data(connection, server_confirmation)  # <--- SERVER_CONFIRMATION
    check_client_confirmation = get_data(connection, data, 7)  # CLIENT_CONFIRMATION --->
    if len(check_client_confirmation) != len(str(int(check_client_confirmation))):
        print(f"[{data[2]}] SPACE AFTER CONFIRMATION: {check_client_confirmation}")
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False
    print(f"[{data[2]}] CONFIRM FROM CLIENT: {check_client_confirmation} and OURS: {client_confirmation}")
    if int(client_confirmation) != int(check_client_confirmation):
        send_data(connection, Messages.SERVER_LOGIN_FAILED.value)  # <--- # SERVER_LOGIN_FAILED
        connection.close()
        return False
    send_data(connection, Messages.SERVER_OK.value)  # <--- SERVER_OK
    return True


# --------------------------------------------------

def get_coords(connection, data):
    buffer = get_data(connection, data, 12)
    if " ".join(buffer.split()) != buffer:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False
    buffer = buffer.split()
    if '.' in buffer[1] or '.' in buffer[2]:
        send_data(connection, Messages.SERVER_SYNTAX_ERROR.value)
        connection.close()
        return False
    coords = []
    for coord in buffer:
        try:
            coords.append(int(coord))
        except ValueError:
            pass
    return coords


def finished(coords):
    return coords[0] == 0 and coords[1] == 0


def move_forward(connection, data):
    send_data(connection, Messages.SERVER_MOVE.value)
    return get_coords(connection, data)


def turn_left(connection, data):
    send_data(connection, Messages.SERVER_TURN_LEFT.value)
    return get_coords(connection, data)


def turn_right(connection, data):
    send_data(connection, Messages.SERVER_TURN_RIGHT.value)
    return get_coords(connection, data)


def turn_around(connection, data):
    turn_left(connection, data)
    turn_left(connection, data)


def rotate(connection, data, direction, need_to):
    if direction == need_to:
        return True

    elif direction == "RIGHT":
        if need_to == "LEFT":
            turn_around(connection, data)
        elif need_to == "UP":
            turn_left(connection, data)
        elif need_to == "DOWN":
            turn_right(connection, data)

    elif direction == "LEFT":
        if need_to == "RIGHT":
            turn_around(connection, data)
        elif need_to == "UP":
            turn_right(connection, data)
        elif need_to == "DOWN":
            turn_left(connection, data)

    elif direction == "UP":
        if need_to == "LEFT":
            turn_left(connection, data)
        elif need_to == "RIGHT":
            turn_right(connection, data)
        elif need_to == "DOWN":
            turn_around(connection, data)

    elif direction == "DOWN":
        if need_to == "LEFT":
            turn_right(connection, data)
        elif need_to == "RIGHT":
            turn_left(connection, data)
        elif need_to == "UP":
            turn_around(connection, data)


def next_move(connection, data, prev_pos, curr_pos):
    x = curr_pos[0] - prev_pos[0]
    y = curr_pos[1] - prev_pos[1]

    direction = ""
    if y == 0 and x > 0:
        direction = "RIGHT"
    if y == 0 and x < 0:
        direction = "LEFT"
    if x == 0 and y > 0:
        direction = "UP"
    if x == 0 and y < 0:
        direction = "DOWN"

    need_to = ""
    if curr_pos[0] > 0:
        need_to = "LEFT"
    elif curr_pos[0] < 0:
        need_to = "RIGHT"
    elif curr_pos[1] > 0:
        need_to = "DOWN"
    elif curr_pos[1] < 0:
        need_to = "UP"

    rotate(connection, data, direction, need_to)
    return move_forward(connection, data)


def get_secret(connection, data):
    send_data(connection, Messages.SERVER_PICK_UP.value)
    return get_data(connection, data)


def logout(connection):
    send_data(connection, Messages.SERVER_LOGOUT.value)
    connection.close()


def solve_obstacle(connection, data):
    turn_right(connection, data)
    coords = move_forward(connection, data)
    if finished(coords):
        get_secret(connection, data)
        logout(connection)

    turn_left(connection, data)
    coords = move_forward(connection, data)
    if finished(coords):
        get_secret(connection, data)
        logout(connection)

    coords = move_forward(connection, data)
    if finished(coords):
        get_secret(connection, data)
        logout(connection)

    turn_left(connection, data)
    coords = move_forward(connection, data)
    if finished(coords):
        get_secret(connection, data)
        logout(connection)

    return turn_right(connection, data)


def robot_part(connection, data):
    coords = move_forward(connection, data)
    print(f"[{data[2]}] POSITION: {coords}")
    if finished(coords):
        secret = get_secret(connection, data)
        print(f"[{data[2]}] SECRET MESSAGE: {secret}")
        logout(connection)

    prev_pos = coords
    curr_pos = move_forward(connection, data)
    print(f"[{data[2]}] POSITION: {curr_pos}")
    while curr_pos != [0, 0]:
        if prev_pos == curr_pos:
            print(f"[{data[2]}] GOT INTO OBSTACLE with {prev_pos} and {curr_pos}")
            tmp = solve_obstacle(connection, data)
            prev_pos = curr_pos
            curr_pos = tmp
        else:
            tmp = next_move(connection, data, prev_pos, curr_pos)

            prev_pos = curr_pos
            curr_pos = tmp
            print(f"[{data[2]}] POSITION: {curr_pos}")

    secret = get_secret(connection, data)
    print(f"[{data[2]}] SECRET MESSAGE: {secret}")
    logout(connection)


def handle_client(connection: socket.socket, count):
    print(f"[{count}] NEW CONNECTION")
    connection.settimeout(TIMEOUT)
    data = ["", False, count]  # make data mutable, format: [text, is_sleeping, num of thread]
    try:
        auth(connection, data)
        robot_part(connection, data)
    except socket.timeout:
        print(f"[{data[2]}] CONNECTION TIMEOUT")
        connection.close()
        print('-----------------------------------')
        return False
    except:
        pass
    print('-----------------------------------')
    return True


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solve "Address already in use"
    try:
        server.bind((HOST, PORT))
    except Exception as e:
        print(str(e))
    server.listen()
    print(f"Start listening on {HOST}:{PORT}")
    count = 0
    while True:
        connection, address = server.accept()
        count += 1
        thread = threading.Thread(target=handle_client, args=[connection, count])
        thread.start()


if __name__ == '__main__':
    main()
