from enum import Enum
import socket

SERVER = '192.168.56.1'
PORT = 12345


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
KEY_PAIRS = [(23019, 32037), (32037, 29295), (18789, 13603), (16443, 29533), (18189, 21952)]


def start_server(server):
    print("[SERVER] Starting server")

    # Checking whether port is free
    try:
        server.bind((SERVER, PORT))
    except ConnectionError as e:
        print(e)

    server.listen()
    print(f"[SERVER] Listening on {SERVER}:{PORT}")

    while True:
        connection, address = server.accept()
        print(f"[SERVER] New active connection {connection} {address}")


def stop_server(server):
    print("[SERVER] Stopping server")
    server.close()


def main():
    server = socket.socket()
    start_server(server)
    stop_server(server)


if __name__ == '__main__':
    main()
