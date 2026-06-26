import socket
import time
import threading
from datastore import DataStore
from metrics import metrics_manager
from raft_state import raft_state
HOST = "127.0.0.1"

PORT = int(
    input("Replica Port: ")
)
ELECTION_TIMEOUT = 5

last_heartbeat = time.time()

db = DataStore()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.bind((HOST, PORT))
server.listen()

print(
    f"Replica running on port {PORT}"
)

metrics_manager.update({
    "replica_status": "online",
    "master_status": "online",
    "replication_lag_ms": 0
})

metrics_manager.save()
def monitor_heartbeat():

    global last_heartbeat

    while True:

        if (
            time.time() - last_heartbeat
            >
            ELECTION_TIMEOUT
        ):

            print()

            print(
                "Leader timeout detected!"
            )

            raft_state.become_candidate()

            last_heartbeat = time.time()

        time.sleep(1)
        
threading.Thread(
    target=monitor_heartbeat,
    daemon=True
).start()
while True:

    client_socket, address = server.accept()

    while True:

        data = client_socket.recv(1024)

        if not data:
            break

        command = data.decode().strip()

        if command == "HEARTBEAT":

            last_heartbeat = time.time()

            print(
                f"Heartbeat received on {PORT}"
            )

            client_socket.send(
                b"ALIVE"
            )

            continue

        parts = command.split()

        if (
            len(parts) == 3
            and
            parts[0].upper() == "SET"
        ):

            db.set(
                parts[1],
                parts[2]
            )

            metrics_manager.update({
                "replica_status": "online",
                "replication_lag_ms": 0
            })

            metrics_manager.save()

            print(
                f"Replicated: {parts[1]}={parts[2]}"
            )

            client_socket.send(
                b"OK"
            )

        else:

            client_socket.send(
                b"INVALID"
            )

    client_socket.close()
    


