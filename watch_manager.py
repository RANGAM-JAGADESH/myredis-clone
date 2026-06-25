class WatchManager:

    def __init__(self):

        self.versions = {}

        self.watched = {}

    def watch(self, key):

        self.watched[key] = self.versions.get(
            key,
            0
        )

        print(
            f"WATCH {key} version={self.watched[key]}"
        )

        return "OK"

    def touch(self, key):

        self.versions[key] = (
            self.versions.get(key, 0) + 1
        )

        print(
            f"TOUCH {key} version={self.versions[key]}"
        )

    def validate(self):

        print(
            "WATCHED:",
            self.watched
        )

        print(
            "VERSIONS:",
            self.versions
        )

        for key, version in self.watched.items():

            if self.versions.get(
                key,
                0
            ) != version:

                return False

        return True

    def clear(self):

        self.watched = {}