import pytest
from pytest import approx
import time
from fakeredis import FakeStrictRedis

from celery_once.backends.redis import parse_url, Redis
from celery_once.tasks import AlreadyQueued
from redis.lock import Lock as RedisLock


def test_parse_redis_details_tcp_default_args():
    details = parse_url('redis://localhost:6379/')
    assert details == {'host': 'localhost', 'port': 6379}


def test_parse_url_tcp_with_db():
    details = parse_url('redis://localhost:6379/3')
    assert details == {'host': 'localhost', 'port': 6379, 'db': 3}


def test_parse_url_tcp_no_port():
    details = parse_url('redis://localhost')
    assert details == {'host': 'localhost'}


def test_parse_url_tcp_with_password():
    details = parse_url('redis://:ohai@localhost:6379')
    assert details == {'host': 'localhost', 'port': 6379, 'password': 'ohai'}


def test_parse_url_unix_sock_no_options():
    details = parse_url('redis+socket:///var/run/redis/redis.sock')
    assert details == {'unix_socket_path': '/var/run/redis/redis.sock'}


def test_parse_url_unix_sock_with_options():
    details = parse_url('redis+socket:///var/run/redis/redis.sock?db=2&socket_timeout=2')
    assert details == {
        'unix_socket_path': '/var/run/redis/redis.sock',
        'db': 2,
        'socket_timeout': 2.0
    }


def test_parse_url_with_ssl():
    details = parse_url('rediss://localhost:6379/3')
    assert details == {'host': 'localhost', 'port': 6379, 'db': 3, 'ssl': True}


def test_parse_unsupported_url():
    with pytest.raises(ValueError):
        parse_url('amqp://guest:guest@localhost:5672/potato')


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


def test_redis_raise_or_lock(redis, backend):
    assert redis.get("test") is None
    backend.raise_or_lock(key="test", timeout=60)
    assert redis.get("test") is not None

def test_redis_raise_or_lock_locked(redis, backend):
    # Set to expire in 30 seconds!
    lock = RedisLock(redis, "test", timeout=30)
    lock.acquire()

    with pytest.raises(AlreadyQueued) as e:
        backend.raise_or_lock(key="test", timeout=60)

    assert e.value.countdown == approx(30.0, rel=0.1)
    assert "Expires in" in e.value.message


def test_redis_raise_or_lock_locked_and_expired(redis, backend):
    lock = RedisLock(redis, "test", timeout=1)
    lock.acquire()
    time.sleep(1)  # wait for lock to expire

    backend.raise_or_lock(key="test", timeout=60)
    assert redis.get("test") is not None


def test_redis_clear_lock(redis, backend):
    redis.set("test", 1326499200 + 30)
    backend.clear_lock("test")
    assert redis.get("test") is None


def test_redis_cached_property(mocker, monkeypatch):
    # Remove any side effect previous tests could have had
    monkeypatch.setattr('celery_once.backends.redis.redis', None)
    mock_parse = mocker.patch('celery_once.backends.redis.parse_url')
    mock_parse.return_value = {
        'host': "localhost"
    }
    # Despite the class being inited twice, should only setup once.
    Redis({
        'url': "redis://localhost:1337"
    })
    Redis({})
    assert mock_parse.call_count == 1
