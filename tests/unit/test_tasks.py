
from celery import task
from celery_once.tasks import QueueOnce


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
    assert "qo_args_example_a-1_b-2" == args_example.get_key(
        kwargs={'a': 1, 'b': 2})


def test_get_key_args_2():
    assert "qo_args_example_a-1_b-2" == args_example.get_key(args=(1, 2, ))


def test_get_key_select_args_1():
    assert "qo_select_args_example_a-1" == select_args_example.get_key(
        kwargs={'a': 1, 'b': 2})


def test_get_key_bound_task():
    assert "qo_bound_task_a-1_b-2" == bound_task.get_key(
        kwargs={'a': 1, 'b': 2})
