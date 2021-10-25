import pytest
from fakeredis import FakeStrictRedis

from celery_once.backends.sentinel import Sentinel
from tests.unit.backends.test_redis import TestRedis


class TestSentinel(TestRedis):
    @pytest.fixture()
    def redis(self, monkeypatch):
        fake_redis = FakeStrictRedis()
        fake_redis.flushall()
        for attr in ("master_for", "slave_for"):
            setattr(fake_redis, attr, lambda *_, **__: fake_redis)
        monkeypatch.setattr(
            "celery_once.backends.sentinel.Sentinel.sentinel",
            fake_redis
        )
        return fake_redis

    @pytest.fixture()
    def backend(self):
        backend = Sentinel({
            "instances": ["redis://s1:1337", "redis://s2:1337"],
            "default_timeout": 60 * 60 * 24,
            "master_name": 'my_master',
            "password": 'strong_one'
        })
        return backend
