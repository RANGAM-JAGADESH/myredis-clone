import socket
import threading
import time
import random
from datastore import DataStore
from metrics import metrics_manager
from raft_state import raft_state
from raft_vote import collect_votes
HOST = "127.0.0.1"

PORT = int(
    input("Replica Port: ")
)

last_heartbeat = time.time()

heartbeat_started = False
global ELECTION_TIMEOUT



ELECTION_TIMEOUT = random.randint(
    5,
    10
)

raft_state.set_timeout(
    ELECTION_TIMEOUT
)

print(
    f"Election Timeout = {ELECTION_TIMEOUT}s"
)

db = DataStore()

server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.bind(
    (HOST, PORT)
)

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

        # Leader never starts a new election
        if raft_state.get_role() == "LEADER":

            time.sleep(1)

            continue

        if (
            time.time() - last_heartbeat
            >=
            ELECTION_TIMEOUT
        ):

            print()
            print(
                "Leader timeout detected!"
            )

            raft_state.become_candidate()

            votes = collect_votes(PORT)

            print(
                f"Votes = {votes}"
            )

            from raft_vote import has_majority

            if has_majority(votes):

                raft_state.become_leader()

                last_heartbeat = time.time()

                from leader_election import leader_manager
                from raft_heartbeat import start_heartbeat

                leader_manager.set_leader(PORT)

                print(
                    f"Leader elected on {PORT}"
                )

                global heartbeat_started

                if not heartbeat_started:

                    heartbeat_started = True

                    threading.Thread(
                        target=start_heartbeat,
                        args=(PORT,),
                        daemon=True
                    ).start()

            last_heartbeat = time.time()

        time.sleep(1)


threading.Thread(
    target=monitor_heartbeat,
    daemon=True
).start()


while True:

    client_socket, address = server.accept()

    try:

        while True:

            try:

                data = client_socket.recv(1024)

            except (
                ConnectionResetError,
                ConnectionAbortedError
            ):
                break

            if not data:
                break

            command = data.decode().strip()

            parts = command.split()

            # -------------------------------
            # HEARTBEAT
            # -------------------------------

            if parts[0] == "HEARTBEAT":

                leader_term = int(parts[1])

                if leader_term >= raft_state.get_term():

                    raft_state.set_term(
                        leader_term
                    )

                    if raft_state.get_role() != "FOLLOWER":

                        raft_state.become_follower()

                    last_heartbeat = time.time()

                    print(
                        f"Heartbeat accepted "
                        f"(Term {leader_term})"
                    )

                    client_socket.send(
                        b"ALIVE"
                    )

                else:

                    client_socket.send(
                        b"STALE"
                    )

                continue

            # -------------------------------
            # REQUEST_VOTE
            # -------------------------------

            elif (
                len(parts) == 2
                and
                parts[0] == "REQUEST_VOTE"
            ):

                term = int(parts[1])

                response = raft_state.vote(term)

                client_socket.send(
                    response.encode()
                )

                continue

            # -------------------------------
            # REPLICATION
            # -------------------------------

            elif (
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

    finally:

        client_socket.close()