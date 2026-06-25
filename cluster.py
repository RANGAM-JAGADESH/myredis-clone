from sharding import SHARDS

def cluster_info():

    return {
        "cluster_state": "ok",
        "total_shards": len(SHARDS),
        "shards": SHARDS
    }