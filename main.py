import socket

SERVER = '192.168.56.1'
PORT = 12345


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
