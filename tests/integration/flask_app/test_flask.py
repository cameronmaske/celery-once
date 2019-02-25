from __future__ import absolute_import
from tests.integration.flask_app.app import sleep_task 
from time import sleep
import pytest
from celery_once import AlreadyQueued
import pytest


@pytest.mark.framework
def test_flask():
    sleep_task.delay(1)
    sleep(0.5)
    with pytest.raises(AlreadyQueued):
        sleep_task.delay(1)
    sleep(2) # Task should of completed by now. 
    sleep_task.delay(1)
