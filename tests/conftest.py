import pytest

from fakeredis import FakeStrictRedis

from celery_once.backends import Redis


@pytest.fixture()
def redis_backend(monkeypatch):
    conf = {
        'url': 'redis://localhost:6379/0',
        'timeout': 30 * 60
    }
    backend = Redis(conf)
    fake_redis = FakeStrictRedis()
    fake_redis.flushall()
    backend.redis = fake_redis
    monkeypatch.setattr("celery_once.tasks.QueueOnce.once_backend", backend)
    return backend
