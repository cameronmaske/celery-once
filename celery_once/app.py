from celery import Celery
from celery.result import AsyncResult

class CeleryOnce(Celery):
    def __init__(self, *args, **kwargs):
        super(CeleryOnce, self).__init__(*args, **kwargs)
        @self.task(bind=True)
        def requeue_subsequent_tasks(self, task_id):
            result = AsyncResult(task_id)
            if not result.ready():
                self.retry()
            result.maybe_reraise()
            return result.get()
        self.conf.ONCE_REQUEUE_SUBSEQUENT_TASKS = requeue_subsequent_tasks
