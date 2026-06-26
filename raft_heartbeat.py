import socket
import time
from shared import leader_manager
# from leader_election import get_leader

HOST = "127.0.0.1"

LEADER_PORT = 6379

REPLICAS = [
    6380,
    6381
]


def send_heartbeat(port):

    try:

        replica_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        replica_socket.settimeout(2)

        replica_socket.connect(
            (HOST, port)
        )

        replica_socket.send(
            b"HEARTBEAT"
        )

        response = replica_socket.recv(
            1024
        ).decode()

        print(
            f"Heartbeat -> {port} : {response}"
        )

        replica_socket.close()

    except Exception as e:

        print(
            f"Heartbeat failed -> {port}: {e}"
        )


def start_heartbeat():

    while True:

        if leader_manager.get_leader() == LEADER_PORT:

            for replica in REPLICAS:

                send_heartbeat(replica)

        time.sleep(1)