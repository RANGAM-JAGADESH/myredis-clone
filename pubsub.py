class PubSub:

    def __init__(self):

        self.channels = {}

        self.message_count = 0

    def subscribe(self, channel, client_socket):

        if channel not in self.channels:
            self.channels[channel] = []

        self.channels[channel].append(client_socket)

        return f"Subscribed to {channel}"

    def publish(self, channel, message):
        self.message_count += 1

        if channel not in self.channels:
            return 0

        subscribers = self.channels[channel]

        for subscriber in subscribers:

            try:

                subscriber.send(
                    f"\n[{channel}] {message}\n".encode()
                )

            except:
                pass

        return len(subscribers)