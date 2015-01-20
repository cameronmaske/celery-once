from celery import Celery
from celery_once import QueueOnce

app = Celery()
app.conf.ONCE_REDIS_URL = 'redis://localhost:6379/0'
app.conf.ONCE_DEFAULT_TIMEOUT = 60 * 60
app.conf.CELERY_ALWAYS_EAGER = True


@app.task(name="example", base=QueueOnce, once={'keys': []})
def example(redis):
    return redis.get("qo_example")


def test_delay(redis):
    result = example.delay(redis)
    assert result.get() is not None
    redis.get("qo_example") is None


def test_apply_async(redis):
    result = example.apply_async(args=(redis, ))
    assert result.get() is not None
    redis.get("qo_example") is None
