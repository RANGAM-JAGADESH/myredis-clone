import socket
import threading
from datastore import DataStore

HOST = "127.0.0.1"

PORT = int(input("Shard Port: "))

db = DataStore()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.bind((HOST, PORT))
server.listen()

print(f"Shard running on {PORT}")


def handle_client(client_socket):

    while True:

        try:

            data = client_socket.recv(1024)

            if not data:
                break

            command = data.decode().strip()
            print(
    f"[{PORT}] Received:",
    command
)

            parts = command.split()

            if len(parts) == 3 and parts[0].upper() == "SET":

                response = db.set(
                    parts[1],
                    parts[2]
                )

            elif len(parts) == 2 and parts[0].upper() == "GET":

                response = db.get(
                    parts[1]
                )

            else:

                response = "INVALID"

            client_socket.send(
                str(response).encode()
            )

        except:
            break

    client_socket.close()


while True:

    client_socket, _ = server.accept()

    threading.Thread(
        target=handle_client,
        args=(client_socket,)
    ).start()