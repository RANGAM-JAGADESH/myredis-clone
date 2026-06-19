import socket
from datastore import DataStore

HOST = "127.0.0.1"
PORT = 6379

db = DataStore()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen()

print(f"MyRedis Server running on {HOST}:{PORT}")

while True:
    client_socket, address = server.accept()

    print(f"Connected: {address}")

    while True:
        data = client_socket.recv(1024)

        if not data:
            break

        command = data.decode().strip()

        parts = command.split()

        if not parts:
            response = "Empty Command"

        else:
            cmd = parts[0].upper()

            if cmd == "PING":
                response = db.ping()

            elif cmd == "SET" and len(parts) == 3:
                response = db.set(parts[1], parts[2])

            elif cmd == "GET" and len(parts) == 2:
                response = db.get(parts[1])

            elif cmd == "DEL" and len(parts) == 2:
                response = str(db.delete(parts[1]))

            elif cmd == "KEYS":
                response = str(db.keys())

            elif cmd == "EXISTS" and len(parts) == 2:
                response = str(db.exists(parts[1]))

            elif cmd == "INFO":
                response = str(db.info())
                
            elif cmd == "EXPIRE" and len(parts) == 3:
                response = str(
                    db.expire(
                        parts[1],
                        int(parts[2])
                    )
                )
                
            elif cmd == "TTL" and len(parts) == 2:
                response = str(
                    db.ttl(parts[1])
                )

            else:
                response = "Invalid Command"

        client_socket.send(response.encode())

    client_socket.close()