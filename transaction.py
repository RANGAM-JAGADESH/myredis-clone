class TransactionManager:

    def __init__(self):

        self.in_transaction = False

        self.commands = []

    def begin(self):

        self.in_transaction = True

        self.commands = []

        return "OK"

    def queue(self, command):

        if not self.in_transaction:

            return "ERR MULTI not started"

        self.commands.append(command)

        return "QUEUED"

    def execute(self, db):

        if not self.in_transaction:

            return "ERR MULTI not started"

        results = []

        for command in self.commands:

            parts = command.split()

            if len(parts) == 3 and parts[0].upper() == "SET":

                results.append(
                    db.set(
                        parts[1],
                        parts[2]
                    )
                )

            elif len(parts) == 2 and parts[0].upper() == "DEL":

                results.append(
                    db.delete(
                        parts[1]
                    )
                )

        self.commands = []

        self.in_transaction = False

        return results

    def discard(self):

        self.commands = []

        self.in_transaction = False

        return "OK"