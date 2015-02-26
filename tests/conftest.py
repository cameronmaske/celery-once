import pytest

from fakeredis import FakeStrictRedis

from celery_once.backends import Redis


@pytest.fixture()
def backend(monkeypatch):
    backend = Redis('redis://localhost:6379/0')
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    backend.redis = fake_redis
    monkeypatch.setattr("celery_once.tasks.QueueOnce.once_backend", backend)
    return backend


@pytest.fixture()
def redis(monkeypatch):
    backend = Redis('redis://localhost:6379/0')
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    backend.redis = fake_redis
    monkeypatch.setattr("celery_once.tasks.QueueOnce.once_backend", backend)
    return backend
