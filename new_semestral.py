import socket
import threading
import sys
from enum import Enum

HOST = "127.0.0.1"
PORT = int(sys.argv[1])


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


def handle_client(connection):
    pass


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
