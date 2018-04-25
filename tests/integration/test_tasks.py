import pytest

from celery import Celery
from celery_once import QueueOnce, AlreadyQueued


app = Celery()
app.conf.ONCE = {
    'backend': 'tests.backends.TestBackend',
    'settings': {
        'default_timeout': 60
    }
}
app.conf.CELERY_ALWAYS_EAGER = True


@pytest.fixture(autouse=True)
def mock_backend(mocker):
    mocker.patch('tests.backends.TestBackend.raise_or_lock')
    mocker.patch('tests.backends.TestBackend.clear_lock')


@app.task(name="example", base=QueueOnce)
def example():
    return


@app.task(name="example_unlock_before_run", base=QueueOnce, once={'unlock_before_run': True})
def example_unlock_before_run():
    return


@app.task(name="example_retry", base=QueueOnce, once={'keys': []}, bind=True)
def example_retry(self, a=0):
    if a != 1:
        self.request.called_directly = False
        self.retry(kwargs={'a': 1})


def test_config():
    assert example.config == app.conf


def test_once_config():
    assert example.once_config == {
        'backend': 'tests.backends.TestBackend',
        'settings': {
            'default_timeout': 60
        }
    }


def test_default_timeout():
    assert example.default_timeout == 60


def test_apply_async():
    example.apply_async()
    example.once_backend.raise_or_lock.assert_called_with(
        "qo_example", timeout=60)


def test_apply_async_timeout(mocker):
    example.once_backend.raise_or_lock = mocker.Mock()
    example.apply_async(once={'timeout': 120})
    example.once_backend.raise_or_lock.assert_called_with(
        "qo_example", timeout=120)


def test_raise_already_queued():
    example.once_backend.raise_or_lock.side_effect = AlreadyQueued(60)
    with pytest.raises(AlreadyQueued):
        example.apply_async()


def test_raise_already_queued_graceful():
    example.once_backend.raise_or_lock.side_effect = AlreadyQueued(60)
    result = example.apply_async(once={'graceful': True})
    assert result.result is None


def test_retry():
    example_retry.apply_async()
    example.once_backend.raise_or_lock.assert_called_with(
        "qo_example_retry", timeout=60)
    example.once_backend.clear_lock.assert_called_with("qo_example_retry")


def test_delay_unlock_before_run(mocker):
    mock_parent = mocker.Mock()
    clear_lock_mock = mocker.Mock()
    after_return_mock = mocker.Mock()
    mock_parent.attach_mock(clear_lock_mock, 'clear_lock')
    mock_parent.attach_mock(after_return_mock, 'after_return')
    example_unlock_before_run.once_backend.clear_lock.side_effect = clear_lock_mock
    example_unlock_before_run.after_return = after_return_mock
    example_unlock_before_run.apply_async()
    assert len(mock_parent.mock_calls) == 2
    assert mock_parent.mock_calls[0] == mocker.call.clear_lock('qo_example_unlock_before_run')
