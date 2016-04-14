from celery import task
from celery_once.tasks import QueueOnce, AlreadyQueued
import pytest
import mock


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


def test_raise_or_lock(redis):
    assert redis.get("test") is None
    QueueOnce().raise_or_lock(key="test", expires=60, options={'task_id': 1})
    assert redis.get("test") == b'1'
    assert redis.ttl("test") == 60


def test_raise_or_lock_locked(redis):
    # Set to expire in 30 seconds!
    redis.setex("test", 30, 1)
    with pytest.raises(AlreadyQueued) as e:
        QueueOnce().raise_or_lock(key="test", expires=60, options={'task_id': 2})
    assert e.value.countdown == 30
    assert e.value.message == "Expires in {} seconds".format(e.value.countdown)
    assert e.value.result.id == b'1'

def test_raise_or_lock_locked_and_expired(redis):
    # Set to have expired 30 ago seconds!
    redis.setex("test", -30, 1)
    QueueOnce().raise_or_lock(key="test", expires=60, options={'task_id': 2})
    assert redis.get("test") == b'2'
    assert redis.ttl("test") == 60

def test_raise_or_lock_with_link(redis):
    redis.setex("test", 30, 1)
    task = QueueOnce()
    f = task.app.conf.ONCE_REQUEUE_SUBSEQUENT_TASKS = mock.Mock()
    with pytest.raises(AlreadyQueued):
        task.raise_or_lock(key="test", expires=60, options={'link': 'foo'})
    f.apply_async.assert_called_with(args=(b'1',), link='foo')

def test_clear_lock(redis):
    redis.set("test", 1326499200 + 30)
    QueueOnce().clear_lock("test")
    assert redis.get("test") is None
