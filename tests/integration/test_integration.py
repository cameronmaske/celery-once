import pytest

from celery import Celery
from freezegun import freeze_time

from celery_once import QueueOnce, AlreadyQueued


app = Celery()
app.conf.ONCE = {
    'backend': 'celery_once.backends.Redis',
    'settings': {
        'url': 'redis://localhost:1337/0',
        'timeout': 30 * 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce, once={'keys': ['a']})
def example(redis_backend, a=1):
    return redis_backend.redis.get("qo_example_a-1")


def test_delay_1(redis_backend):
    result = example.delay(redis_backend)
    assert result.get() is not None
    assert redis_backend.redis.get("qo_example_a-1") is None


def test_delay_2(redis_backend):
    redis_backend.redis.set("qo_example_a-1", 10000000000)
    try:
        example.delay(redis_backend)
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


@freeze_time("2012-01-14")  # 1326499200
def test_delay_3(redis_backend):
    redis_backend.redis.set("qo_example_a-1", 1326499200 - 60 * 60)
    example.delay(redis_backend)


def test_apply_async_1(redis_backend):
    result = example.apply_async(args=(redis_backend, ))
    assert result.get() is not None
    redis_backend.redis.get("qo_example_a-1") is None


def test_apply_async_2(redis_backend):
    redis_backend.redis.set("qo_example_a-1", 10000000000)
    try:
        example.apply_async(args=(redis_backend, ))
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


def test_apply_async_3(redis_backend):
    redis_backend.redis.set("qo_example_a-1", 10000000000)
    result = example.apply_async(args=(redis_backend, ), once={'graceful': True})
    assert result is None


@freeze_time("2012-01-14")  # 1326499200
def test_apply_async_4(redis_backend):
    redis_backend.redis.set("qo_example_a-1", 1326499200 - 60 * 60)
    example.apply_async(args=(redis_backend, ))


def test_redis():
    connection_kwargs = example.once_backend.redis.connection_pool.connection_kwargs
    details = example.once_backend.details
    assert details['host'] == connection_kwargs['host'] == "localhost"
    assert details['port'] == connection_kwargs['port'] == 1337
    assert details['db'] == connection_kwargs['db'] == 0


def test_default_timeout():
    assert example.default_timeout == 30 * 60
