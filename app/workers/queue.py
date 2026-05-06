from redis import Redis
from rq import Queue


def create_queue(redis_url, queue_name="custom-agents"):
    connection = Redis.from_url(redis_url)
    return Queue(name=queue_name, connection=connection)
