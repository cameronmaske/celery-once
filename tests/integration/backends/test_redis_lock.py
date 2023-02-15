import pytest
import time
from fakeredis import FakeStrictRedis

from celery import Celery
from celery_once import QueueOnce, AlreadyQueued
from redis.lock import Lock as RedisLock

EXAMPLE_KEY = "lock:qo_example_b-1"


@pytest.fixture()
def redis(monkeypatch):
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    monkeypatch.setattr("celery_once.backends.redis.Redis.redis", fake_redis)
    return fake_redis


app = Celery()
app.conf.ONCE = {
    'backend': "celery_once.backends.redis_lock.RedisLockBackend",
    'settings': {
        'url': "redis://192.168.241.178:6379/1",
        # 'url': "redis://localhost:1337/0",
        'timeout': 30 * 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce)
def example(a=1):
    assert example.once_backend.redis.get(EXAMPLE_KEY) is not None


def test_init():
    details = example.once_backend._redis.connection_pool.connection_kwargs
    assert details['host'] == "localhost"
    assert details['port'] == 1337
    assert details['db'] == 0


def test_delay(redis):
    example.delay(1)
    assert redis.get(EXAMPLE_KEY) is None

