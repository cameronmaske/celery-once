from flask import Flask
from celery import Celery
from time import sleep 
from celery_once import QueueOnce


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

    celery.Task = ContextTask
    return celery

flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://redis:6379/1',
    CELERY_RESULT_BACKEND='redis://redis:6379/2',
)
celery = make_celery(flask_app)
celery.conf.ONCE = {
  'backend': 'celery_once.backends.Redis',
  'settings': {
    'url': 'redis://redis:6379/3',
    'default_timeout': 60 * 60
  }
}

# Setting the `name` allow us to reach this task in the test folder. 
@celery.task(name="tests.integration.flask.app.sleep_task", base=QueueOnce)
def sleep_task(value):
    print(flask_app.config) # See if we can access app.
    return sleep(value)