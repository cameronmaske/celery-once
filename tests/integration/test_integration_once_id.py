from celery import Celery
from celery.result import AsyncResult
from celery_once import QueueOnce, AlreadyQueued
from celery_once.tasks import QueueOnceId
from freezegun import freeze_time
import pytest


app = Celery()
app.conf.ONCE_REDIS_URL = 'redis://localhost:1337/0'
app.conf.ONCE_DEFAULT_TIMEOUT = 30 * 60
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnceId)
def example(a=1):
    return 'Something'

@app.task(name="example_graceful", base=QueueOnceId, once={'graceful': True})
def example_graceful(a=1):
    return 'Something'

def helper_test_result(result, id='test'):
    assert result is not None
    assert isinstance(result, AsyncResult)
    assert result.id == id

def test_no_id_no_args(redis):
    result = example.apply_async(args=( ))
    helper_test_result(result, id='example_cW9fZXhhbXBsZV9hLTE=')

def test_no_id(redis):
    result = example.apply_async(args=(2, ))
    helper_test_result(result, id='example_cW9fZXhhbXBsZV9hLTI=')

def test_empty_string_id(redis):
    try:
        example.apply_async(args=( ), task_id='')
        pytest.fail("QueueOnceId was started with an empty task_id")
    except ValueError:
        pass

def test_specified_num_id(redis):
    result = example.apply_async(args=( ), task_id=1)
    helper_test_result(result, id=1)

def test_specified_string_id(redis):
    result = example.apply_async(args=( ), task_id='test')
    helper_test_result(result)

def test_specified_id_exists(redis):
    redis.set("qo_example_graceful_test", 10000000000)
    result = example_graceful.apply_async(args=( ), task_id='test')
    helper_test_result(result)

def test_specified_id_exists_not_graceful(redis):
    redis.set("qo_example_test", 10000000000)
    try:
        example.apply_async(args=( ), task_id='test')
        pytest.fail("QueueOnceId should have failed")
    except AlreadyQueued:
        pass

@freeze_time("2012-01-14")  # 1326499200
def test_apply_async_timeout_fail(redis):
    try:
        redis.set("qo_example_test", 1326499200 + 10 * 60)
        example.apply_async(args=( ), task_id='test')
        pytest.fail("QueueOnceId should have failed")
    except AlreadyQueued:
        pass

@freeze_time("2012-01-14")  # 1326499200
def test_apply_async_timeout(redis):
    redis.set("qo_example_test", 1326499200 - 60 * 60)
    result = example.apply_async(args=( ), task_id='test')
    helper_test_result(result)

@freeze_time("2012-01-14")  # 1326499200
def test_apply_async_timeout_result(redis):
    redis.set("qo_example_graceful_test", 1326499200 + 10 * 60)
    result = example_graceful.apply_async(args=( ), task_id='test')
    helper_test_result(result)
