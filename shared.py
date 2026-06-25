from datastore import DataStore
from pubsub import PubSub
from transaction import TransactionManager

transaction_manager = TransactionManager()
db = DataStore()
pubsub = PubSub()


class ReplicationManager:

    def __init__(self):

        self.master_status = "online"
        self.replica_status = "online"
        self.lag_ms = 0


replication_manager = ReplicationManager()