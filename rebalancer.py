from sharding import SHARDS, get_shard

def rebalance(data):

    movement = []

    for key in data.keys():

        target = get_shard(key)

        movement.append({
            "key": key,
            "target": target
        })

    return movement