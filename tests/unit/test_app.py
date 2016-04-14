import pytest, mock
from celery_once.app import CeleryOnce
from celery.exceptions import Retry

def raise_intentional_exception():
    raise Exception()

def test_retry_when_not_ready(redis):
    with mock.patch('celery_once.app.AsyncResult', new=mock.Mock(return_value=mock.Mock(**{'ready.return_value': False}))):
        with pytest.raises(Retry):
            CeleryOnce().conf.ONCE_REQUEUE_SUBSEQUENT_TASKS(1)

def test_reraise_exception(redis):
    with mock.patch('celery_once.app.AsyncResult', new=mock.Mock(return_value=mock.Mock(maybe_reraise=raise_intentional_exception))):
        with pytest.raises(Exception):
            CeleryOnce().conf.ONCE_REQUEUE_SUBSEQUENT_TASKS(1)

def test_result_returned(redis):
    with mock.patch('celery_once.app.AsyncResult', new=mock.Mock(return_value=mock.Mock(**{'get.return_value': 5}))):
        assert CeleryOnce().conf.ONCE_REQUEUE_SUBSEQUENT_TASKS(1) == 5
