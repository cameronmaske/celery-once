import pytest
import time
from fakeredis import FakeStrictRedis

from celery import Celery
from celery_once import QueueOnce, AlreadyQueued
from redis.lock import Lock as RedisLock


@pytest.fixture()
def redis(monkeypatch):
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    monkeypatch.setattr("celery_once.backends.redis.Redis.redis", fake_redis)
    return fake_redis


app = Celery()
app.conf.ONCE = {
    'backend': "celery_once.backends.redis.Redis",
    'settings': {
        'url': "redis://localhost:1337/0",
        'timeout': 30 * 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce)
def example(a=1):
    assert example.once_backend.redis.get("qo_example_a-1") is not None


def test_init():
    details = example.once_backend.redis.connection_pool.connection_kwargs
    assert details['host'] == "localhost"
    assert details['port'] == 1337
    assert details['db'] == 0


def test_delay(redis):
    example.delay(1)
    assert redis.get("qo_example_a-1") is None


def test_delay_already_queued(redis):
    redis.set("qo_example_a-1", 10000000000)
    try:
        example.delay(1)
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


def test_delay_expired(redis):
    lock = RedisLock(redis, "qo_example_a-1", timeout=1)
    lock.acquire()

    assert redis.get("qo_example_a-1") is not None

    time.sleep(1)
    example.delay(1)

    assert redis.get("qo_example_a-1") is None


def test_apply_async(redis):
    example.apply_async(args=(1, ))
    assert redis.get("qo_example_a-1") is None


def test_apply_async_queued(redis):
    redis.set("qo_example_a-1", 10000000000)
    try:
        example.apply_async(args=(1, ))
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


def test_already_queued_graceful(redis):
    redis.set("qo_example_a-1", 10000000000)
    result = example.apply_async(args=(1, ), once={'graceful': True})
    assert result.result is None


def test_apply_async_expired(redis):
    lock = RedisLock(redis, "qo_example_a-1", timeout=1)
    lock.acquire()

    assert redis.get("qo_example_a-1") is not None

    time.sleep(1)
    example.apply_async(args=(1, ))

    assert redis.get("qo_example_a-1") is None
