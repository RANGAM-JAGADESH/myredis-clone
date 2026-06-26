import socket
import threading
from metrics import metrics_manager
from health_checker import monitor  
import time
# from shared import db, pubsub, replication_manager
from shard_router import send_to_shard
from cluster_health import monitor_cluster
from shared import (
    db,
    pubsub,
    replication_manager,
    transaction_manager,
    watch_manager
)
from raft_heartbeat import start_heartbeat

HOST = "127.0.0.1"
PORT = 6379
replica_status = {
    6380: "unknown",
    6381: "unknown",
    6382: "unknown"
}


store = db



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

    replicas = [
        6380,
        6381,
        6382
    ]

    online_replicas = 0

    for port in replicas:

        try:

            replica_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            replica_socket.connect(
                ("127.0.0.1", port)
            )

            replica_socket.send(
                command.encode()
            )

            replica_socket.close()

            online_replicas += 1
            replica_status[port] = "online"

        except Exception as e:

            replica_status[port] = "offline"

            print(
                f"Replica {port} Error: {e}"
            )

    metrics_manager.update({
        "master_status": "online",
        "replica_status":
            f"{online_replicas}/3 online",
        "replication_lag_ms": 0
    })

    metrics_manager.save()

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

                    response = send_to_shard(
                        command,
                        parts[1]
                    )

                    replicate_to_replica(command)

                    watch_manager.touch(
                        parts[1]
                    )

                elif cmd == "GET" and len(parts) == 2:

                    response = send_to_shard(
                        command,
                        parts[1]
                    )

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
                    
                elif cmd == "BGREWRITEAOF":

                    from aof_rewrite import rewrite_aof

                    rewrite_aof(db)

                    response = "AOF Rewrite Completed"


                elif cmd == "MULTI":

                    response = transaction_manager.begin()


                elif cmd == "QUEUE":

                    queued_command = " ".join(parts[1:])

                    response = transaction_manager.queue(
                        queued_command
                    )


                elif cmd == "EXEC":

                    if not watch_manager.validate():

                        response = (
                            "Transaction Aborted"
                        )

                    else:

                        response = (
                            transaction_manager.execute(
                                db
                            )
                        )

                    watch_manager.clear()


                elif cmd == "DISCARD":

                    response = transaction_manager.discard()
                    
                elif cmd == "WATCH" and len(parts) == 2:

                    response = watch_manager.watch(
                        parts[1]
                    )
                elif cmd == "UNWATCH":

                    watch_manager.clear()

                    response = "OK"

                else:
                    response = "Invalid Command"


            client_socket.send(
                str(response).encode()
            )

        except Exception as e:

            print(f"Error: {e}")

            break
    if db.connected_clients > 0:
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

        metrics_manager.update({

            "connected_clients":
                db.connected_clients,

            "replica_6380":
                replica_status.get(6380),

            "replica_6381":
                replica_status.get(6381),

            "replica_6382":
                replica_status.get(6382)
        })

        metrics_manager.save()

        time.sleep(5)

threading.Thread(
    target=metrics_updater,
    daemon=True
).start()
threading.Thread(
    target=monitor,
    daemon=True
).start()

threading.Thread(
    target=monitor_cluster,
    daemon=True
).start()

threading.Thread(
    target=start_heartbeat,
    args=(6379,),
    daemon=True
).start()

threading.Thread(
    target=start_heartbeat,
    args=(PORT,),
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
    
