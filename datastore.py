class DataStore:
    def __init__(self):
        self.store = {}

    def set(self, key, value):
        self.store[key] = value
        return "OK"

    def get(self, key):
        return self.store.get(key, "(nil)")

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return 1
        return 0

    def keys(self):
        return list(self.store.keys())

    def exists(self, key):
        return 1 if key in self.store else 0