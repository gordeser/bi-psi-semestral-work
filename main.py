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
server_keys = [23019, 32037, 18789, 16443, 18189]
client_keys = [32037, 29295, 13603, 29533, 21952]


def count_hash(username):
    username_decimal = [ord(i) for i in list(username)]
    _hash = (sum(username_decimal) * 1000) % 65536
    return _hash


def count_server_confirmation(_hash, key_id):
    return (_hash + server_keys[key_id]) % 65536


def count_client_confirmation(_hash, key_id):
    return (_hash + client_keys[key_id]) % 65536

def start_server(server):
    print("[SERVER] Starting server")

    # Checking whether port is free
    try:
        server.bind((SERVER, PORT))
    except OSError as e:
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
