from metrics import metrics_manager
class PubSub:

    def __init__(self):

        self.channels = {}

        self.message_count = 0

    def subscribe(self, channel, client_socket):

        if channel not in self.channels:
            self.channels[channel] = []

        self.channels[channel].append(client_socket)

        metrics_manager.update({
            "total_channels": len(self.channels),
            "active_subscribers":
                sum(len(x) for x in self.channels.values())
        })

        metrics_manager.save()

        return f"Subscribed to {channel}"

    def publish(self, channel, message):

        self.message_count += 1

        if channel not in self.channels:

            metrics_manager.update({
                "messages_published": self.message_count,
                "total_channels": len(self.channels),
                "active_subscribers":
                    sum(len(x) for x in self.channels.values())
            })

            metrics_manager.save()

            return 0

        subscribers = self.channels[channel]

        for subscriber in subscribers:

            try:

                subscriber.send(
                    f"\n[{channel}] {message}\n".encode()
                )

            except:
                pass

        metrics_manager.update({
            "messages_published": self.message_count,
            "total_channels": len(self.channels),
            "active_subscribers":
                sum(len(x) for x in self.channels.values())
        })

        metrics_manager.save()

        return len(subscribers)