from celery import task
from celery_once.tasks import QueueOnce, AlreadyQueued, QueueOnceId
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
    assert "qo_args_example_a-1_b-2" == args_example.get_key(kwargs={'a':1, 'b': 2})


def test_get_key_args_2():
    assert "qo_args_example_a-1_b-2" == args_example.get_key(args=(1, 2, ))


def test_get_key_select_args_1():
    assert "qo_select_args_example_a-1" == select_args_example.get_key(kwargs={'a':1, 'b': 2})


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


# QueueOnceId
@task(name='task_id_example', base=QueueOnceId, once={'keys': ['a']})
def task_id_example(a, b):
    return a + b

def test_task_id_key():
    assert "qo_task_id_example_a_key" == task_id_example.get_key_from_id(task_id='a_key')

def test_task_id_key_num():
    assert "qo_task_id_example_10" == task_id_example.get_key_from_id(task_id=10)