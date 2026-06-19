from persistence import save_data, load_data
class DataStore:
    def __init__(self):
        self.store = load_data()
        self.command_count = 0

    def increment_commands(self):
        self.command_count += 1

    def set(self, key, value):
        self.increment_commands()
        self.store[key] = value
        save_data(self.store)
        return "OK"

    def get(self, key):
        self.increment_commands()
        return self.store.get(key, "(nil)")

    def delete(self, key):
        self.increment_commands()

        if key in self.store:
            del self.store[key]
            save_data(self.store)
            return 1
        return 0

    def keys(self):
        self.increment_commands()
        return list(self.store.keys())

    def exists(self, key):
        self.increment_commands()
        return 1 if key in self.store else 0

    def ping(self):
        self.increment_commands()
        return "PONG"

    def info(self):
        self.increment_commands()

        return {
            "keys": len(self.store),
            "commands_executed": self.command_count
        }