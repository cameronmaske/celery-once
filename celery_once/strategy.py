# -*- coding: utf8 -*-

from __future__ import absolute_import

import logging

from kombu.async.timer import to_timestamp
from kombu.utils.encoding import safe_repr
from kombu.utils.limits import TokenBucket

from celery.utils.log import get_logger
from celery.utils.timeutils import timezone, rate
from celery.worker.job import Request
from celery.worker.state import task_reserved

logger = get_logger(__name__)


def rate_limit_strategy(task, app, consumer,
             info=logger.info, error=logger.error, task_reserved=task_reserved,
             to_system_tz=timezone.to_system):
    """
    This function is mainly a copy/paste of `celery.worker.strategy:default`.
    The modifications lie in the the inner `task_message_handler` function
    and were made to support a parameter based rate limiting.
    """
    hostname = consumer.hostname
    eventer = consumer.event_dispatcher
    Req = Request
    connection_errors = consumer.connection_errors
    _does_info = logger.isEnabledFor(logging.INFO)
    events = eventer and eventer.enabled
    send_event = eventer.send
    call_at = consumer.timer.call_at
    apply_eta_task = consumer.apply_eta_task
    rate_limits_enabled = not consumer.disable_rate_limits
    get_bucket = consumer.task_buckets.__getitem__
    handle = consumer.on_task_request
    limit_task = consumer._limit_task

    def task_message_handler(message, body, ack, reject, callbacks,
                             to_timestamp=to_timestamp):
        req = Req(body, on_ack=ack, on_reject=reject,
                  app=app, hostname=hostname,
                  eventer=eventer, task=task,
                  connection_errors=connection_errors,
                  message=message)
        if req.revoked():
            return

        if _does_info:
            info('Received task: %s', req)

        if events:
            send_event(
                'task-received',
                uuid=req.id, name=req.name,
                args=safe_repr(req.args), kwargs=safe_repr(req.kwargs),
                retries=req.request_dict.get('retries', 0),
                eta=req.eta and req.eta.isoformat(),
                expires=req.expires and req.expires.isoformat(),
            )

        if req.eta:
            try:
                if req.utc:
                    eta = to_timestamp(to_system_tz(req.eta))
                else:
                    eta = to_timestamp(req.eta, timezone.local)
            except OverflowError as exc:
                error("Couldn't convert eta %s to timestamp: %r. Task: %r",
                      req.eta, exc, req.info(safe=True), exc_info=True)
                req.acknowledge()
            else:
                consumer.qos.increment_eventually()
                call_at(eta, apply_eta_task, (req, ), priority=6)
        else:
            if rate_limits_enabled:
                # We get the key from our ParametersBasedRateLimit class
                bucket_key = task.get_key(*body["args"], **body["kwargs"])
                # Then we try to retrieve the bucket (this is the logic behind
                # the rate limiting in celery)
                bucket = get_bucket(bucket_key)
                if not bucket:
                    # No bucket was found so we create a new one
                    limit = rate(task.get_rate_limit(*body["args"],
                                                     **body["kwargs"]))
                    consumer.task_buckets[bucket_key] = \
                        TokenBucket(limit, capacity=1) if limit else None
                    bucket = get_bucket(bucket_key)
                if bucket:
                    # limit_task will ask the bucket it it can launch the task
                    # under the rate limit restriction
                    return limit_task(req, bucket, 1)

            task_reserved(req)
            if callbacks:
                [callback() for callback in callbacks]
            handle(req)

    return task_message_handler
