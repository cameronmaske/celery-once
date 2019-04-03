"""
Definition of the file locking backend.
"""
import errno
import os
import tempfile
import time

from celery_once.tasks import AlreadyQueued


class File(object):
    """
    File locking backend.
    """
    def __init__(self, settings):
        self.location = settings.get('location')
        if self.location is None:
            self.location = os.path.join(tempfile.gettempdir(),
                                         'celery_once')
        try:
            os.makedirs(self.location)
        except OSError as error:
            # Directory exists?
            if error.errno != errno.EEXIST:
                # Re-raise unexpected OSError
                raise

    def _get_lock_path(self, key):
        return os.path.join(self.location, key)

    def raise_or_lock(self, key, timeout):
        """
        Check the lock file and create one if it does not exist.
        """
        lock_path = self._get_lock_path(key)
        try:
            # Create lock file, raise exception if it exists
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL)
        except OSError as error:
            if error.errno == errno.EEXIST:
                # File already exists, check its modification time
                mtime = os.path.getmtime(lock_path)
                ttl = mtime + timeout - time.time()
                if ttl > 0:
                    raise AlreadyQueued(ttl)
                else:
                    # Update modification time if timeout happens
                    os.utime(lock_path, None)
                    return
            else:
                # Re-raise unexpected OSError
                raise
        else:
            os.close(fd)

    def clear_lock(self, key):
        """
        Remove the lock file.
        """
        lock_path = self._get_lock_path(key)
        os.remove(lock_path)
