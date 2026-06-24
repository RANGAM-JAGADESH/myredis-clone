import socket
import threading
from metrics import metrics_manager
from datastore import DataStore
from pubsub import PubSub
import time

HOST = "127.0.0.1"
PORT = 6379

db = DataStore()

store = db

pubsub = PubSub()

class ReplicationManager:

    def __init__(self):

        self.master_status = "online"
        self.replica_status = "online"
        self.lag_ms = 0

replication_manager = ReplicationManager()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.bind((HOST, PORT))
server.listen()

print(f"MyRedis Server running on {HOST}:{PORT}")

# def replicate_to_replica(command):

#     try:
#         replica_socket = socket.socket(
#             socket.AF_INET,
#             socket.SOCK_STREAM
#         )

#         replica_socket.connect(
#             ("127.0.0.1", 6380)
#         )

#         replica_socket.send(
#             command.encode()
#         )

#         replica_socket.close()

#     except Exception as e:
#         print(
#             f"Replication Error: {e}"
#         )

# print(f"MyRedis Server running on {HOST}:{PORT}")
def replicate_to_replica(command):

    try:

        replica_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        replica_socket.connect(
            ("127.0.0.1", 6380)
        )

        replica_socket.send(
            command.encode()
        )

        replica_socket.close()

        replication_manager.replica_status = "online"
        replication_manager.lag_ms = 0

        metrics_manager.update({
            "replica_status": "online",
            "master_status": "online",
            "replication_lag_ms": 0
        })

        metrics_manager.save()

    except Exception as e:

        replication_manager.replica_status = "offline"

        metrics_manager.update({
            "replica_status": "offline"
        })

        metrics_manager.save()

        print(
            f"Replication Error: {e}"
        )

def handle_client(client_socket, address):

    print(f"Connected: {address}")

    while True:

        try:
            data = client_socket.recv(1024)

            if not data:
                break

            command = data.decode().strip()

            print("Received:", command)

            parts = command.split()

            if not parts:
                response = "Empty Command"

            else:

                cmd = parts[0].upper()

                if cmd == "PING":
                    response = db.ping()

                elif cmd == "SET" and len(parts) == 3:

                    response = db.set(
                        parts[1],
                        parts[2]
                    )

                    replicate_to_replica(
                        command
                    )

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

                elif cmd == "SUBSCRIBE" and len(parts) == 2:

                    response = pubsub.subscribe(
                        parts[1],
                        client_socket
                    )

                elif cmd == "PUBLISH" and len(parts) >= 3:

                    channel = parts[1]

                    message = " ".join(parts[2:])

                    count = pubsub.publish(
                        channel,
                        message
                    )

                    response = (
                        f"Message sent to {count} subscribers"
                    )

                else:
                    response = "Invalid Command"

            client_socket.send(
                str(response).encode()
            )

        except Exception as e:

            print(f"Error: {e}")

            break
    db.connected_clients -= 1

    metrics_manager.update({
        "connected_clients":
            db.connected_clients
    })

    metrics_manager.save()
    client_socket.close()

    print(f"Disconnected: {address}")
def metrics_updater():

    while True:

        metrics_manager.save()

        time.sleep(2)

threading.Thread(
    target=metrics_updater,
    daemon=True
).start()

while True:

    client_socket, address = server.accept()

    db.connected_clients += 1

    metrics_manager.update({
        "connected_clients":
            db.connected_clients
    })

    metrics_manager.save()

    print(f"Connected: {address}")

    thread = threading.Thread(
        target=handle_client,
        args=(client_socket, address)
    )

    thread.start()
    
