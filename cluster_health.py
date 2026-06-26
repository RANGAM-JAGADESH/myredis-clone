import socket
import time

from nodes import NODES
from shared import leader_manager


def is_alive(port):

    try:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.settimeout(1)

        sock.connect(
            ("127.0.0.1", port)
        )

        sock.close()

        return True

    except:

        return False


def monitor_cluster():

    while True:

        current_leader = (
            leader_manager.get_leader()
        )

        if not is_alive(
            current_leader
        ):

            print(
                f"Leader {current_leader} failed"
            )

            new_leader = None

            for node in NODES:

                if (
                    node != current_leader
                    and is_alive(node)
                ):

                    new_leader = node

                    break

            if new_leader:

                leader_manager.elect(
                    new_leader
                )

                print(
                    f"New Leader Elected: {new_leader}"
                )

            else:

                print(
                    "No available nodes found"
                )

        time.sleep(5)


if __name__ == "__main__":

    print("Cluster Health Monitor Started")

    monitor_cluster()