import socket
import threading
import sys
from enum import Enum

HOST = "127.0.0.1"
PORT = int(sys.argv[1])

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


def get_data(connection, data):
    while data[0].find(ENDING) == -1:
        data[0] += connection.recv(1024).decode('ascii')

    pos = data[0].find(ENDING)
    message = data[0][:pos]
    data[0] = data[0][pos + 2:]
    return message


def send_data(connection, data):
    connection.send(bytes(str(data)+ENDING, 'utf-8'))


def count_hash(username):
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * MULTIPLY) % MODULO
    return _hash


def count_server_confirmation(_hash, key_id):
    return (_hash + SERVER_KEYS[key_id]) % MODULO


def count_client_confirmation(_hash, key_id):
    return (_hash + CLIENT_KEYS[key_id]) % MODULO


def auth(connection, data):
    username = get_data(connection, data)  # CLIENT_USERNAME --->
    print(f"USERNAME: {username}")
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # <--- SERVER_KEY_REQUEST
    key_id = int(get_data(connection, data))  # CLIENT_KEY_ID --->
    print(f"KEY_ID: {key_id}")
    _hash = count_hash(username)
    print(f"COUNTED HASH: {_hash}")
    server_confirmation = count_server_confirmation(_hash, key_id)
    client_confirmation = count_client_confirmation(_hash, key_id)
    print(f"CONFIRMS: SERVER {server_confirmation} and CLIENT {client_confirmation}")
    send_data(connection, server_confirmation)  # <--- SERVER_CONFIRMATION
    check_client_confirmation = get_data(connection, data)  # CLIENT_CONFIRMATION --->
    print(f"CONFIRM FROM CLIENT: {check_client_confirmation} and OURS: {client_confirmation}")
    if client_confirmation != client_confirmation:
        send_data(connection, Messages.SERVER_LOGIN_FAILED.value)  # <--- # SERVER_LOGIN_FAILED
        return False
    send_data(connection, Messages.SERVER_OK.value)  # <--- SERVER_OK
    return True


def handle_client(connection: socket.socket):
    connection.settimeout(TIMEOUT)
    data = [""]  # make data mutable

    auth(connection, data)
    # robot part
    return True


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # # solve "Address already in use"
    try:
        server.bind((HOST, PORT))
    except Exception as e:
        print(str(e))
    server.listen()
    print(f"Start listening on {HOST}:{PORT}")
    while True:
        print('-----------------------------------')
        connection, address = server.accept()
        thread = threading.Thread(target=handle_client, args=[connection])
        thread.start()


if __name__ == '__main__':
    main()
