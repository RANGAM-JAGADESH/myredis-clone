import socket

from raft_state import raft_state

HOST = "127.0.0.1"

REPLICAS = [
    6380,
    6381
]


def request_vote(port):

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        s.settimeout(2)

        s.connect(
            (HOST, port)
        )

        command = (
            f"REQUEST_VOTE "
            f"{raft_state.get_term()}"
        )

        s.send(command.encode())

        response = (
            s.recv(1024)
            .decode()
        )

        s.close()

        return response

    except:

        return "NO"


def collect_votes():

    votes = 1

    print(
        "Vote from self"
    )

    for replica in REPLICAS:

        response = request_vote(
            replica
        )

        print(
            f"{replica} -> {response}"
        )

        if response == "YES":

            votes += 1

    return votes