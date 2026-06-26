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

            return json.load(f)["leader"]

    def elect(self, port):

        with open(FILE, "w") as f:

            json.dump(
                {
                    "leader": port
                },
                f
            )