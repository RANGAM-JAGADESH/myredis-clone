import hashlib

SHARDS = [
    ("127.0.0.1", 6379),
    ("127.0.0.1", 6385),
    ("127.0.0.1", 6386)
]

def get_shard(key):

    hash_value = int(
        hashlib.md5(
            key.encode()
        ).hexdigest(),
        16
    )

    return SHARDS[
        hash_value % len(SHARDS)
    ]