from fastapi import FastAPI
from datastore import DataStore
from metrics import load_metrics
from pydantic import BaseModel
class KeyValue(BaseModel):
    key: str
    value: str


class TTLRequest(BaseModel):
    key: str
    seconds: int
app = FastAPI()

db = DataStore()

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