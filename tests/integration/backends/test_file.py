import pytest
import time
import os 

from celery import Celery
from celery_once import QueueOnce, AlreadyQueued


app = Celery()
app.conf.ONCE = {
    'backend': "celery_once.backends.File",
    'settings': {
        'location': '/tmp/celery_once',
        'default_timeout': 60 * 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce)
def example(a=1):
    pass 

@pytest.fixture()
def lock_path():
    path = '/tmp/celery_once/qo_example_a-1_b7f89d8561e5788a3e7687c6ede93bcd'
    yield path
    os.remove(path) # Remove file after test function runs.

def test_delay(lock_path):
    example.delay(1)
    assert os.open(lock_path, os.O_CREAT) is not None

def test_delay_already_queued(lock_path):
    os.open(lock_path, os.O_CREAT)
    with pytest.raises(AlreadyQueued):
        example.delay(1)

