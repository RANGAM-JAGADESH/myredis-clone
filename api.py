from fastapi import FastAPI
from shared import db, pubsub
from metrics import load_metrics
from pydantic import BaseModel
from shared import db, pubsub, replication_manager

import shutil
class KeyValue(BaseModel):
    key: str
    value: str


class TTLRequest(BaseModel):
    key: str
    seconds: int
app = FastAPI()



@app.get("/")
def root():

    return {
        "status": "healthy",
        "service": "MyRedis"
    }
    
@app.get("/metrics")
def metrics():

    return load_metrics()



@app.get("/keys")
def keys():

    return {
        "keys": db.keys()
    }

@app.get("/info")
def info():

    return db.info()

@app.post("/set")
def set_key(data: KeyValue):

    result = db.set(
        data.key,
        data.value
    )

    return {
        "status": result,
        "key": data.key,
        "value": data.value
    }
    
@app.get("/get/{key}")
def get_key(key: str):

    value = db.get(key)

    return {
        "key": key,
        "value": value
    }
    
    
@app.delete("/delete/{key}")
def delete_key(key: str):

    deleted = db.delete(key)

    return {
        "deleted": deleted
    }
    
    
@app.post("/expire")
def expire_key(data: TTLRequest):

    result = db.expire(
        data.key,
        data.seconds
    )

    return {
        "success": result
    }
    
class PublishRequest(BaseModel):
    channel: str
    message: str


class SubscribeRequest(BaseModel):
    channel: str
    
    
@app.get("/ttl/{key}")
def ttl(key: str):

    return {
        "ttl": db.ttl(key)
    }
    
    
@app.get("/exists/{key}")
def exists(key: str):

    return {
        "exists": db.exists(key)
    }
    
@app.get("/api/metrics")
def api_metrics():
    return load_metrics()


@app.post("/publish")
def publish(data: PublishRequest):

    count = pubsub.publish(
        data.channel,
        data.message
    )

    return {
        "channel": data.channel,
        "subscribers": count,
        "message": data.message
    }
    
    
@app.get("/channels")
def channels():

    return {
        "channels": list(
            pubsub.channels.keys()
        )
    }
    
@app.get("/subscribers")
def subscribers():

    total = sum(
        len(x)
        for x in pubsub.channels.values()
    )

    return {
        "subscribers": total
    }
    
    
@app.get("/pubsub/stats")
def pubsub_stats():

    return {
        "channels":
            len(pubsub.channels),

        "subscribers":
            sum(
                len(x)
                for x in pubsub.channels.values()
            ),

        "messages_published":
            pubsub.message_count
    }
    
    
@app.get("/health")
def health():

    return {
        "status": "healthy",
        "server": "running",
        "replica": "online"
    }


@app.get("/status")
def status():

    return {
        "keys": len(db.store),
        "connected_clients": db.connected_clients,
        "commands": db.command_count,
        "pubsub_channels": len(pubsub.channels)
    }
    
    
@app.get("/replication/status")
def replication_status():

    return {
        "master_status":
            replication_manager.master_status,

        "replica_status":
            replication_manager.replica_status,

        "lag_ms":
            replication_manager.lag_ms
    }
    
@app.get("/server/stats")
def server_stats():

    return {
        "keys": len(db.store),
        "commands": db.command_count,
        "hits": db.hit_count,
        "misses": db.miss_count,
        "evictions": db.eviction_count,
        "clients": db.connected_clients
    }
    


@app.get("/backup")
def backup():

    shutil.copy(
        "dump.json",
        "backup_dump.json"
    )

    return {
        "status": "backup_created"
    }
    
    
@app.get("/restore")
def restore():

    shutil.copy(
        "backup_dump.json",
        "dump.json"
    )

    return {
        "status": "restored"
    }