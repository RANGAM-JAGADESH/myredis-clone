from aof import AOF_FILE


def replay_aof(db):

    try:

        with open(AOF_FILE, "r") as file:

            commands = file.readlines()

        for command in commands:

            parts = command.strip().split()

            if not parts:
                continue

            cmd = parts[0].upper()

            if cmd == "SET" and len(parts) == 3:

                db.store[parts[1]] = parts[2]

            elif cmd == "DEL" and len(parts) == 2:

                if parts[1] in db.store:
                    del db.store[parts[1]]

        print("AOF Recovery Complete")

    except FileNotFoundError:

        print("No AOF file found")