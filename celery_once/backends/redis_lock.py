from celery_once import AlreadyQueued

try:
    from redis_lock import Lock
except ImportError:
    raise ImportError("You need to install the python-redis-lock library in order to use RedisLock"
                      " backend (pip install redis_lock)")

try:
    import redis
except ImportError:
    raise ImportError("You need to install the redis library in order to use Redis"
                      " backend (pip install redis)")


class RedisLockBackend(object):
    """
        RedisLock backend based on python-redis-lock library
        https://pypi.org/project/python-redis-lock/
    """

    def __init__(self, settings):
        self._redis = redis.Redis.from_url(settings["url"])
        self.blocking_timeout = settings.get("blocking_timeout", 1)
        self.blocking = settings.get("blocking", False)

    def raise_or_lock(self, key, timeout):
        lock = Lock(self._redis, key, expire=timeout)
        if not lock.acquire(blocking=self.blocking, timeout=self.blocking_timeout):
            raise AlreadyQueued(self._redis.ttl("lock:" + key))

    def clear_lock(self, key):
        Lock(self._redis, key).reset()
