import socket
import time

REPLICAS = [6380, 6381, 6382]

replica_status = {}


def check_replica(port):

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        s.settimeout(1)

        s.connect(
            ("127.0.0.1", port)
        )

        s.close()

        return "online"

    except:
        return "offline"


def monitor():

    global replica_status

    while True:

        for port in REPLICAS:

            replica_status[port] = (
                check_replica(port)
            )

        time.sleep(5)