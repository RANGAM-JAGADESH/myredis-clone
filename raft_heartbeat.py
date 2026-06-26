import socket
import time

from leader_election import leader_manager

HOST = "127.0.0.1"

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
            f"Heartbeat -> {port}: {response}"
        )

        replica_socket.close()

    except Exception as e:

        print(
            f"Heartbeat failed -> {port}: {e}"
        )


def start_heartbeat(node_port):

    while True:

        if leader_manager.get_leader() == node_port:

            for replica in REPLICAS:

                if replica != node_port:

                    send_heartbeat(replica)

        time.sleep(1)