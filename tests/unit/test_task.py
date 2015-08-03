from celery import task
from celery_once.tasks import QueueOnce, AlreadyQueued, ParametersBasedRateLimit
from freezegun import freeze_time
import pytest


@task(name='simple_example', base=QueueOnce)
def simple_example():
    return "simple"


@task(name='bound_task', bind=True, base=QueueOnce)
def bound_task(self, a, b):
    return a + b


@task(name='args_example', base=QueueOnce)
def args_example(a, b):
    return a + b


@task(name='select_args_example', base=QueueOnce, once={'keys': ['a']})
def select_args_example(a, b):
    return a + b


def test_get_key_simple():
    assert "qo_simple_example" == simple_example.get_key()


def test_get_key_args_1():
    assert "qo_args_example_a-1_b-2" == args_example.get_key(kwargs={'a': 1, 'b': 2})


def test_get_key_args_2():
    assert "qo_args_example_a-1_b-2" == args_example.get_key(args=(1, 2, ))


def test_get_key_select_args_1():
    assert "qo_select_args_example_a-1" == select_args_example.get_key(kwargs={'a': 1, 'b': 2})


def test_get_key_bound_task():
    assert "qo_bound_task_a-1_b-2" == bound_task.get_key(kwargs={'a': 1, 'b': 2})


@freeze_time("2012-01-14")  # 1326499200
def test_raise_or_lock(redis):
    assert redis.get("test") is None
    QueueOnce().raise_or_lock(key="test", expires=60)
    assert redis.get("test") is not None
    assert redis.ttl("test") == 60


@freeze_time("2012-01-14")  # 1326499200
def test_raise_or_lock_locked(redis):
    # Set to expire in 30 seconds!
    redis.set("test", 1326499200 + 30)
    with pytest.raises(AlreadyQueued) as e:
        QueueOnce().raise_or_lock(key="test", expires=60)
    assert e.value.countdown == 30
    assert e.value.message == "Expires in 30 seconds"


@freeze_time("2012-01-14")  # 1326499200
def test_raise_or_lock_locked_and_expired(redis):
    # Set to have expired 30 ago seconds!
    redis.set("test", 1326499200 - 30)
    QueueOnce().raise_or_lock(key="test", expires=60)
    assert redis.get("test") is not None
    assert redis.ttl("test") == 60


def test_clear_lock(redis):
    redis.set("test", 1326499200 + 30)
    QueueOnce().clear_lock("test")
    assert redis.get("test") is None


@task(name='rate_simple_example', base=ParametersBasedRateLimit, rate_limit="1/s")
def rate_simple_example():
    return "simple"


@task(name='rate_bound_task', bind=True, base=ParametersBasedRateLimit, rate_limit="1/m")
def rate_bound_task(self, a, b):
    return a + b


@task(name='rate_args_example', base=ParametersBasedRateLimit, rate_limit="1/h")
def rate_args_example(a, b):
    return a + b


@task(name='rate_select_args_example', base=ParametersBasedRateLimit,
      rate_limit_options={'keys': ['a']}, rate_limit="4/s")
def rate_select_args_example(a, b):
    return a + b


def test_rate_get_key_simple():
    assert "qo_rate_simple_example" == rate_simple_example.get_key()


def test_rate_get_key_args_1():
    assert "qo_rate_args_example_a-1_b-2" == rate_args_example.get_key(a=1, b=2)


def test_rate_get_key_args_2():
    assert "qo_rate_args_example_a-1_b-2" == rate_args_example.get_key(1, 2)


def test_rate_get_key_select_args_1():
    assert "qo_rate_select_args_example_a-1" == rate_select_args_example.get_key(a=1, b=2)


def test_rate_get_key_bound_task():
    assert "qo_rate_bound_task_a-1_b-2" == rate_bound_task.get_key(a=1, b=2)


def test_get_rate_limit():
    assert "1/m" == rate_bound_task.get_rate_limit(a=1, b=2)
