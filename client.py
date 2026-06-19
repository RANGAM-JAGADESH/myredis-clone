import socket

HOST = "127.0.0.1"
PORT = 6379

client = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

client.connect((HOST, PORT))

while True:
    command = input("MyRedis Client > ")

    if command.upper() == "EXIT":
        break

    client.send(command.encode())

    response = client.recv(1024)

    print("Server:", response.decode())

client.close()