import socket
from sharding import get_shard


def send_to_shard(command, key):

    host, port = get_shard(key)

    shard_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    shard_socket.connect(
        (host, port)
    )

    shard_socket.send(
        command.encode()
    )

    response = shard_socket.recv(
        1024
    ).decode()

    shard_socket.close()

    return response