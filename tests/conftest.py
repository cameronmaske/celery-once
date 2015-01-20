from fakeredis import FakeStrictRedis

import pytest


@pytest.fixture()
def redis(monkeypatch):
    fake_redis = FakeStrictRedis()
    monkeypatch.setattr("celery_once.tasks.QueueOnce.redis", fake_redis)
    return fake_redis
