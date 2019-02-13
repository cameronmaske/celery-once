import os
import time

import pytest

from celery_once.backends.file import FileBackend
from celery_once.tasks import AlreadyQueued


TEST_LOCATION = '/tmp'


@pytest.fixture()
def backend():
    backend = FileBackend({'location': TEST_LOCATION})
    return backend


def test_file_init(backend):
    assert backend.location == TEST_LOCATION


def test_file_create_lock(backend, mocker):
    key = 'test'
    timeout = 3600
    exists_mock = mocker.patch(
        'celery_once.backends.file.os.path.exists',
        return_value=False)
    open_mock = mocker.mock_open()
    mocker.patch('celery_once.backends.file.open', open_mock, create=True)
    utime_mock = mocker.patch('celery_once.backends.file.os.utime')
    expected_lock_path = os.path.join(TEST_LOCATION, key)
    backend.raise_or_lock(key, timeout)

    assert exists_mock.call_args[0] == (expected_lock_path,)
    assert open_mock.call_count == 1
    assert open_mock.call_args[0] == (expected_lock_path, 'a')
    assert utime_mock.call_args[0] == (expected_lock_path, None)
