import socket
import threading
import sys
from enum import Enum

HOST = "127.0.0.1"
PORT = int(sys.argv[1])

TIMEOUT = 1
TIMEOUT_RECHARGING = 5


class Messages(Enum):
    SERVER_MOVE = "102 MOVE\a\b"
    SERVER_TURN_LEFT = "103 TURN LEFT\a\b"
    SERVER_TURN_RIGHT = "104 TURN RIGHT\a\b"
    SERVER_PICK_UP = "105 GET MESSAGE\a\b"
    SERVER_LOGOUT = "106 LOGOUT\a\b"
    SERVER_KEY_REQUEST = "107 KEY REQUEST\a\b"
    SERVER_OK = "200 OK\a\b"
    SERVER_LOGIN_FAILED = "300 LOGIN FAILED\a\b"
    SERVER_SYNTAX_ERROR = "301 SYNTAX ERROR\a\b"
    SERVER_LOGIC_ERROR = "302 LOGIC ERROR\a\b"
    SERVER_KEY_OUT_OF_RANGE_ERROR = "303 KEY OUT OF RANGE\a\b"


def get_data(connection, data):
    while data[0].find("\a\b") == -1:
        data[0] += connection.recv(1024).decode('ascii')
    pos = data[0].find("\a\b")
    message = data[0][0:pos]
    data[0] = data[0][pos + 2:]
    return message


def send_data(connection, data):
    connection.send(bytes(data, 'ascii'))


def auth(connection, data):
    username = get_data(connection, data)  # CLIENT_USERNAME --->
    print(f"USERNAME IS: {username}")
    send_data(connection, Messages.SERVER_KEY_REQUEST.value)  # <--- SERVER_KEY_REQUEST


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
