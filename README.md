# Celery Once

![](https://travis-ci.org/trackmaven/celery-once.png?branch=master)

# Getting Started

```
pip install -U celery_once
```

```python
from celery import Celery
from celery_once import QueueOnceTask
from time import sleep

celery = Celery('tasks', broker='amqp://guest@localhost//')
celery.conf.ONCE_REDIS_URL = 'redis://localhost:6379/0'
celery.conf.ONCE_DEFAULT_TIMEOUT = 60 * 60

@celery.task(base=QueueOnceTask)
def example_tasks(sleep_time=30):
    sleep(30)
    return "Done!"
```

Queue once overrides `apply_async`, `apply` and `delay`.
It does not effect calling the tasks directly.

```python
example.delay(10)
example.delay(10)
Traceback (most recent call last):
    ..
AlreadyQueued()
```

```python
result = example.apply_async(args=(10), once={'expires': 60, 'graceful': True})
print result
result = example.apply_async(args=(10), once={'expires': 60, 'graceful': True})
print result
```

```python
result = example.apply(args=(10))
```

# Todo before release!

- [ ] Documentation
- [ ] A better integration tests!


