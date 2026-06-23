import socket
from datastore import DataStore

HOST = "127.0.0.1"
PORT = 6380

db = DataStore()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.bind((HOST, PORT))
server.listen()

print("Replica running on port 6380")

while True:

    client_socket, address = server.accept()

    while True:

        data = client_socket.recv(1024)

        if not data:
            break

        command = data.decode().strip()

        parts = command.split()

        if len(parts) == 3 and parts[0] == "SET":

            db.set(parts[1], parts[2])

            print(
                f"Replicated: {parts[1]}={parts[2]}"
            )

    client_socket.close()