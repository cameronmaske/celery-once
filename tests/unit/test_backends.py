import pytest

from freezegun import freeze_time

from celery_once.tasks import QueueOnce, AlreadyQueued


@freeze_time("2012-01-14")  # 1326499200
def test_redis_raise_or_lock(redis_backend):
    assert redis_backend.redis.get("test") is None
    QueueOnce().once_backend.raise_or_lock(key="test", expires=60)
    assert redis_backend.redis.get("test") is not None


@freeze_time("2012-01-14")  # 1326499200
def test_redis_raise_or_lock_locked(redis_backend):
    # Set to expire in 30 seconds!
    redis_backend.redis.set("test", 1326499200 + 30)
    with pytest.raises(AlreadyQueued) as e:
        QueueOnce().once_backend.raise_or_lock(key="test", expires=60)
    assert e.value.countdown == 30
    assert e.value.message == "Expires in 30 seconds"


@freeze_time("2012-01-14")  # 1326499200
def test_redis_raise_or_lock_locked_and_expired(redis_backend):
    # Set to have expired 30 ago seconds!
    redis_backend.redis.set("test", 1326499200 - 30)
    QueueOnce().once_backend.raise_or_lock(key="test", expires=60)
    assert redis_backend.redis.get("test") is not None


def test_redis_clear_lock(redis_backend):
    redis_backend.redis.set("test", 1326499200 + 30)
    QueueOnce().once_backend.clear_lock("test")
    assert redis_backend.redis.get("test") is None
