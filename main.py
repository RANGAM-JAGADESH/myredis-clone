from datastore import DataStore

db = DataStore()

while True:
    command = input("MyRedis > ").strip()

    if not command:
        continue

    parts = command.split()
    cmd = parts[0].upper()

    try:
        if cmd == "SET":
            if len(parts) != 3:
                print("Usage: SET key value")
                continue

            print(db.set(parts[1], parts[2]))

        elif cmd == "GET":
            if len(parts) != 2:
                print("Usage: GET key")
                continue

            print(db.get(parts[1]))

        elif cmd == "DEL":
            if len(parts) != 2:
                print("Usage: DEL key")
                continue

            print(db.delete(parts[1]))

        elif cmd == "KEYS":
            print(db.keys())

        elif cmd == "EXISTS":
            if len(parts) != 2:
                print("Usage: EXISTS key")
                continue

            print(db.exists(parts[1]))

        elif cmd == "PING":
            print(db.ping())

        elif cmd == "INFO":
            print(db.info())

        elif cmd == "EXIT":
            print("Bye!")
            break

        else:
            print("Unknown Command")

    except Exception as e:
        print(f"Error: {e}")