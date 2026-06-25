AOF_FILE = "appendonly.aof"


def append_command(command):

    with open(AOF_FILE, "a") as f:

        f.write(command + "\n")