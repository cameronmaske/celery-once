"""
Definition of the file locking backend.
"""
import os
import time

from celery_once.tasks import AlreadyQueued


class FileBackend(object):
    """
    File locking backend.
    """
    def __init__(self, settings):
        self.location = settings['location']
        os.makedirs(self.location, exist_ok=True)

    def _get_lock_path(self, key):
        return os.path.join(self.location, key)

    def raise_or_lock(self, key, timeout):
        """
        Check the lock file and create one if it does not exist.
        """
        lock_path = self._get_lock_path(key)
        if os.path.exists(lock_path):
            # Check file modification time
            mtime = os.path.getmtime(lock_path)
            ttl = mtime + timeout - time.time()
            if ttl > 0:
                raise AlreadyQueued(ttl)
        # Create lock file or update it after timeout
        with open(lock_path, 'a'):
            os.utime(lock_path, None)

    def clear_lock(self, key):
        """
        Remove the lock file.
        """
        lock_path = self._get_lock_path(key)
        return os.remove(lock_path)
