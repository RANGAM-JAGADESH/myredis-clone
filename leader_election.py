import json
import os

FILE = "leader_state.json"


class LeaderElection:

    def __init__(self):

        if not os.path.exists(FILE):

            with open(FILE, "w") as f:

                json.dump(
                    {
                        "leader": 6379
                    },
                    f
                )

    def get_leader(self):

        with open(FILE, "r") as f:

            data = json.load(f)

        return data["leader"]

    def set_leader(self, port):

        with open(FILE, "w") as f:

            json.dump(
                {
                    "leader": port
                },
                f
            )

        print()

        print("=" * 35)

        print(
            f"New Leader -> {port}"
        )

        print("=" * 35)

    # Backward compatibility
    # Existing code using elect(port) will still work.
    def elect(self, port):

        self.set_leader(port)


leader_manager = LeaderElection()