import errno
import os
import tempfile
import time

import pytest

from celery_once.backends.file import File
from celery_once.tasks import AlreadyQueued


def test_file_init(mocker):
    makedirs_mock = mocker.patch('celery_once.backends.file.os.makedirs')
    location = '/home/test'
    backend = File({'location': location})

    assert backend.location == location
    assert makedirs_mock.called is True
    assert makedirs_mock.call_args[0] == (location,)


def test_file_init_default(mocker):
    makedirs_mock = mocker.patch('celery_once.backends.file.os.makedirs')
    backend = File({})

    assert backend.location == os.path.join(tempfile.gettempdir(),
                                            'celery_once')
    assert makedirs_mock.called is True


def test_file_init_location_exists(mocker):
    makedirs_mock = mocker.patch('celery_once.backends.file.os.makedirs',
                                 side_effect=OSError(errno.EEXIST, 'error'))
    location = '/home/test'
    backend = File({'location': location})

    assert backend.location == location
    assert makedirs_mock.called is True


TEST_LOCATION = '/tmp/celery'


@pytest.fixture()
def backend(mocker):
    mocker.patch('celery_once.backends.file.os.makedirs')
    backend = File({'location': TEST_LOCATION})
    return backend


def test_file_create_lock(backend, mocker):
    key = 'test.task.key'
    timeout = 3600
    open_mock = mocker.patch('celery_once.backends.file.os.open')
    mtime_mock = mocker.patch('celery_once.backends.file.os.path.getmtime')
    utime_mock = mocker.patch('celery_once.backends.file.os.utime')
    close_mock = mocker.patch('celery_once.backends.file.os.close')
    expected_lock_path = os.path.join(TEST_LOCATION, key)
    ret = backend.raise_or_lock(key, timeout)

    assert open_mock.call_count == 1
    assert open_mock.call_args[0] == (
        expected_lock_path,
        os.O_CREAT | os.O_EXCL,
    )
    assert utime_mock.called is False
    assert close_mock.called is True
    assert ret is None

def test_file_lock_exists(backend, mocker):
    key = 'test.task.key'
    timeout = 3600
    open_mock = mocker.patch(
        'celery_once.backends.file.os.open',
        side_effect=OSError(errno.EEXIST, 'error'))
    mtime_mock = mocker.patch(
        'celery_once.backends.file.os.path.getmtime',
        return_value=1550155000.0)
    time_mock = mocker.patch(
        'celery_once.backends.file.time.time',
        return_value=1550156000.0)
    utime_mock = mocker.patch('celery_once.backends.file.os.utime')
    close_mock = mocker.patch('celery_once.backends.file.os.close')
    with pytest.raises(AlreadyQueued) as exc_info:
        backend.raise_or_lock(key, timeout)

    assert open_mock.call_count == 1
    assert utime_mock.called is False
    assert close_mock.called is False
    assert exc_info.value.countdown == timeout - 1000

def test_file_lock_timeout(backend, mocker):
    key = 'test.task.key'
    timeout = 3600
    open_mock = mocker.patch(
        'celery_once.backends.file.os.open',
        side_effect=OSError(errno.EEXIST, 'error'))
    mtime_mock = mocker.patch(
        'celery_once.backends.file.os.path.getmtime',
        return_value=1550150000.0)
    time_mock = mocker.patch(
        'celery_once.backends.file.time.time',
        return_value=1550156000.0)
    utime_mock = mocker.patch('celery_once.backends.file.os.utime')
    close_mock = mocker.patch('celery_once.backends.file.os.close')
    expected_lock_path = os.path.join(TEST_LOCATION, key)
    ret = backend.raise_or_lock(key, timeout)

    assert open_mock.call_count == 1
    assert utime_mock.call_count == 1
    assert utime_mock.call_args[0] == (expected_lock_path, None)
    assert close_mock.called is False
    assert ret is None

def test_file_clear_lock(backend, mocker):
    key = 'test.task.key'
    remove_mock = mocker.patch('celery_once.backends.file.os.remove')
    expected_lock_path = os.path.join(TEST_LOCATION, key)
    ret = backend.clear_lock(key)

    assert remove_mock.call_count == 1
    assert remove_mock.call_args[0] == (expected_lock_path,)
    assert ret is None
