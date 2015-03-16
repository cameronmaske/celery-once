import pytest
from freezegun import freeze_time
from fakeredis import FakeStrictRedis

from celery_once.backends.redis import parse_url, Redis
from celery_once.tasks import AlreadyQueued


def test_parse_url_1():
    details = parse_url("redis://localhost:1337")
    assert details['host'] == "localhost"
    assert details['port'] == 1337


def test_parse_url_2():
    details = parse_url("redis://localhost:1337/0")
    assert details['host'] == "localhost"
    assert details['port'] == 1337
    assert details['db'] == 0


@pytest.fixture()
def redis(monkeypatch):
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    monkeypatch.setattr("celery_once.backends.redis.Redis.redis", fake_redis)
    return fake_redis


@pytest.fixture()
def backend():
    backend = Redis({'url': "redis://localhost:1337"})
    return backend


@freeze_time("2012-01-14")  # Time since epoch = 1326499200
def test_redis_raise_or_lock(redis, backend):
    assert redis.get("test") is None
    backend.raise_or_lock(key="test", timeout=60)
    assert redis.get("test") is not None


@freeze_time("2012-01-14")  # Time since epoch = 1326499200
def test_redis_raise_or_lock_locked(redis, backend):
    # Set to expire in 30 seconds!
    redis.set("test", 1326499200 + 30)
    with pytest.raises(AlreadyQueued) as e:
        backend.raise_or_lock(key="test", timeout=60)
    assert e.value.countdown == 30
    assert e.value.message == "Expires in 30 seconds"


@freeze_time("2012-01-14")  # Time since epoch = 1326499200
def test_redis_raise_or_lock_locked_and_expired(redis, backend):
    # Set to have expired 30 ago seconds!
    redis.set("test", 1326499200 - 30)
    backend.raise_or_lock(key="test", timeout=60)
    assert redis.get("test") is not None


def test_redis_clear_lock(redis, backend):
    redis.set("test", 1326499200 + 30)
    backend.clear_lock("test")
    assert redis.get("test") is None
