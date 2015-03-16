import pytest
import mock

from celery import Celery
from celery_once import QueueOnce, AlreadyQueued


app = Celery()
app.conf.ONCE = {
    'backend': 'tests.backends.TestBackend',
    'settings': {
        'timeout': 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce)
def example():
    return


def test_config():
    assert example.config == app.conf


def test_once_config():
    assert example.once_config == {
        'backend': 'tests.backends.TestBackend',
        'settings': {
            'timeout': 60
        }
    }


def test_default_timeout():
    assert example.default_timeout == 60


def test_apply_async():
    example.apply_async()
    example.once_backend.raise_or_lock.assert_called_with(
        "qo_example", timeout=60)


def test_apply_async_timeout():
    example.once_backend.raise_or_lock = mock.Mock()
    example.apply_async(once={'timeout': 120})
    example.once_backend.raise_or_lock.assert_called_with(
        "qo_example", timeout=120)


def test_raise_already_queued():
    example.once_backend.raise_or_lock.side_effect = AlreadyQueued(60)
    with pytest.raises(AlreadyQueued):
        example.apply_async()


def test_raise_already_queued_graceful():
    example.once_backend.raise_or_lock.side_effect = AlreadyQueued(60)
    assert example.apply_async(once={'graceful': True}) is None
