from persistence import save_data, load_data
import time
from collections import OrderedDict
class DataStore:
    def __init__(self):
        self.store = OrderedDict(load_data())
        self.expiry = {}
        self.max_keys = 3
        self.command_count = 0
        

        self.start_time = time.time()

        # Dashboard compatibility
        self.data = self.store
        self.ttl_map = self.expiry
        self.capacity = self.max_keys

        # Metrics
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        self.connected_clients = 0
        self.request_count = 0

    def increment_commands(self):
        self.command_count += 1
        self.request_count += 1

    def set(self, key, value):
        self.increment_commands()
        self.store[key] = value

        self.store.move_to_end(key)

        self.enforce_lru()

        save_data(dict(self.store))
        return "OK"
    
    def get(self, key):

        self.increment_commands()

        self.check_expiry(key)

        if key in self.store:

            self.hit_count += 1

            self.store.move_to_end(key)

            return self.store[key]

        self.miss_count += 1

        return None

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

        self.cleanup_expired()

        return {
            "keys": len(self.store),
            "commands_executed": self.command_count,
            "max_keys": self.max_keys,
            "ttl_keys": len(self.expiry),
            "cache_usage": len(self.store)
        }
        
    def expire(self, key, seconds):
        self.increment_commands()

        if key not in self.store:
            return 0

        self.expiry[key] = time.time() + seconds

        return 1
    

    def check_expiry(self, key):

        if key in self.expiry:

            if time.time() > self.expiry[key]:

                if key in self.store:
                    del self.store[key]

                del self.expiry[key]

                save_data(dict(self.store))

                return True

        return False
    def cleanup_expired(self):

        expired = []

        for key in self.expiry:

            if time.time() > self.expiry[key]:

                expired.append(key)

        for key in expired:

            if key in self.store:
                del self.store[key]

            del self.expiry[key]
    
    def ttl(self, key):
        self.increment_commands()

        self.check_expiry(key)

        if key not in self.expiry:
            return -1

        return int(self.expiry[key] - time.time())
    
    
    def enforce_lru(self):

        while len(self.store) > self.max_keys:

            # Dashboard Metric
            self.eviction_count += 1

            oldest_key = next(iter(self.store))

            del self.store[oldest_key]

            if oldest_key in self.expiry:
                del self.expiry[oldest_key]

            save_data(dict(self.store))