from celery_once.app import CeleryOnce
from celery_once import QueueOnce, AlreadyQueued
import pytest
import mock

app = CeleryOnce()
app.conf.ONCE_REDIS_URL = 'redis://localhost:1337/0'
app.conf.ONCE_DEFAULT_TIMEOUT = 30 * 60
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce, once={'keys': ['a']})
def example(redis, a=1):
    return redis.get("qo_example_a-1")

@app.task(name="example_unlock_before_run", base=QueueOnce, once={'keys': ['a'], 'unlock_before_run': True})
def example_unlock_before_run(redis, a=1):
    return redis.get("qo_example_unlock_before_run_a-1")

@app.task(name="example_unlock_before_run_set_key", base=QueueOnce, once={'keys': ['a'], 'unlock_before_run': True})
def example_unlock_before_run_set_key(redis, a=1):
    result = redis.get("qo_example_unlock_before_run_set_key_a-1")
    redis.set("qo_example_unlock_before_run_set_key_a-1", b"1234")
    return result

@app.task(name="example_chained_task")
def example_chained_task(redis):
    redis.set("called", 1)

@app.task(name="example_retry", base=QueueOnce, once={'keys': []}, bind=True)
def example_retry(self, redis, a=1):
    if a > 0:
        self.request.called_directly = False
        self.retry(redis, a=0)


def test_delay_1(redis):
    result = example.delay(redis)
    assert result.get() is not None
    assert redis.get("qo_example_a-1") is None

def test_delay_2(redis):
    redis.setex("qo_example_a-1", 10000000000, 1)
    try:
        example.delay(redis)
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass

def test_delay_3(redis):
    redis.setex("qo_example_a-1", -60 * 60, 1)
    example.delay(redis)


def test_delay_unlock_before_run_1(redis):
    result = example_unlock_before_run.delay(redis)
    assert result.get() is None
    assert redis.get("qo_example_unlock_before_run_a-1") is None

def test_delay_unlock_before_run_2(redis):
    result = example_unlock_before_run_set_key.delay(redis)
    assert result.get() is None
    assert redis.get("qo_example_unlock_before_run_set_key_a-1") == b"1234"


def test_apply_async_1(redis):
    result = example.apply_async(args=(redis, ))
    assert result.get() is not None
    assert redis.get("qo_example_a-1") is None

def test_apply_async_2(redis):
    redis.setex("qo_example_a-1", 10000000000, 1)
    try:
        example.apply_async(args=(redis, ))
        pytest.fail("Didn't raise AlreadyQueued.")
    except AlreadyQueued:
        pass

def test_apply_async_3(redis):
    redis.set("qo_example_a-1", 10000000000, 1)
    result = example.apply_async(args=(redis, ), once={'graceful': True})
    assert result.result is None


def test_apply_async_unlock_before_run_1(redis):
    result = example_unlock_before_run.apply_async(args=(redis, ))
    assert result.get() is None
    assert redis.get("qo_example_unlock_before_run_a-1") is None

def test_apply_async_unlock_before_run_2(redis):
    result = example_unlock_before_run_set_key.apply_async(args=(redis, ))
    assert result.get() is None
    assert redis.get("qo_example_unlock_before_run_set_key_a-1") == b"1234"


def test_apply_async_4(redis):
    redis.setex("qo_example_a-1", -60 * 60, 1)
    example.apply_async(args=(redis, ))

def test_redis():
    assert example.redis.connection_pool.connection_kwargs['host'] == "localhost"
    assert example.redis.connection_pool.connection_kwargs['port'] == 1337
    assert example.redis.connection_pool.connection_kwargs['db'] == 0

def test_default_timeout():
    assert example.default_timeout == 30 * 60

def test_retry(redis):
    result = example_retry.apply_async(args=(redis, ))
    assert redis.get("qo_example_retry") is None
