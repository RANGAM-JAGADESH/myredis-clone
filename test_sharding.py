from sharding import get_shard

print("user   ->", get_shard("user"))
print("city   ->", get_shard("city"))
print("course ->", get_shard("course"))
print("age    ->", get_shard("age"))