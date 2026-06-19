from datastore import DataStore

db = DataStore()

while True:
    command = input("MyRedis > ").strip()

    parts = command.split()

    if not parts:
        continue

    cmd = parts[0].upper()

    if cmd == "SET":
        print(db.set(parts[1], parts[2]))

    elif cmd == "GET":
        print(db.get(parts[1]))

    elif cmd == "DEL":
        print(db.delete(parts[1]))

    elif cmd == "KEYS":
        print(db.keys())

    elif cmd == "EXISTS":
        print(db.exists(parts[1]))

    elif cmd == "EXIT":
        print("Bye!")
        break

    else:
        print("Unknown Command")