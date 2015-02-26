import pytest

from celery import Celery
from freezegun import freeze_time

from celery_once import QueueOnce, AlreadyQueued


app = Celery()
app.conf.ONCE_BACKEND_URL = 'redis://localhost:1337/0'
app.conf.ONCE_DEFAULT_TIMEOUT = 30 * 60
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce, once={'keys': ['a']})
def example(redis, a=1):
    return redis.get("qo_example_a-1")


def test_delay_1(redis):
    result = example.delay(redis)
    assert result.get() is not None
    redis.get("qo_example_a-1") is None


def test_delay_2(redis):
    redis.set("qo_example_a-1", 10000000000)
    try:
        example.delay(redis)
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


@freeze_time("2012-01-14")  # 1326499200
def test_delay_3(redis):
    redis.set("qo_example_a-1", 1326499200 - 60 * 60)
    example.delay(redis)


def test_apply_async_1(redis):
    result = example.apply_async(args=(redis, ))
    assert result.get() is not None
    redis.get("qo_example_a-1") is None


def test_apply_async_2(redis):
    redis.set("qo_example_a-1", 10000000000)
    try:
        example.apply_async(args=(redis, ))
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass


def test_apply_async_3(redis):
    redis.set("qo_example_a-1", 10000000000)
    result = example.apply_async(args=(redis, ), once={'graceful': True})
    assert result is None


@freeze_time("2012-01-14")  # 1326499200
def test_apply_async_4(redis):
    redis.set("qo_example_a-1", 1326499200 - 60 * 60)
    example.apply_async(args=(redis, ))


def test_redis():
    connection_kwargs = example.once_backend.redis.connection_pool.connection_kwargs
    details = example.once_backend.details
    assert details['host'] == connection_kwargs['host'] == "localhost"
    assert details['port'] == connection_kwargs['port'] == 1337
    assert details['db'] == connection_kwargs['db'] == 0


def test_default_timeout():
    assert example.default_timeout == 30 * 60
