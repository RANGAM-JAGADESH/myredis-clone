from datastore import DataStore
from pubsub import PubSub
from transaction import TransactionManager
from watch_manager import WatchManager
from leader_election import LeaderElection

leader_manager = LeaderElection()
transaction_manager = TransactionManager()


watch_manager = WatchManager()
db = DataStore()
pubsub = PubSub()


class ReplicationManager:

    def __init__(self):

        self.master_status = "online"
        self.replica_status = "online"
        self.lag_ms = 0


replication_manager = ReplicationManager()