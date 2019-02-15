from flask import Flask, has_app_context
from celery import Celery
from time import sleep 
from celery_once import QueueOnce
import os 

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    class ContextQueueOnce(QueueOnce):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super(ContextQueueOnce, self).__call__(*args, **kwargs)

    celery.Task = ContextTask
    celery.QueueOnce = ContextQueueOnce
    return celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='{}/1'.format(REDIS_URL),
    CELERY_RESULT_BACKEND='{}/2'.format(REDIS_URL),
)
celery = make_celery(flask_app)
celery.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': '{}/3'.format(REDIS_URL),
    'default_timeout': 60 * 60
  }
}

# Setting the `name` allow us to reach this task in the test folder. 
@celery.task(name="tests.integration.flask_app.app.sleep_task", base=celery.QueueOnce)
def sleep_task(value):
    assert has_app_context() is True
    return sleep(value)