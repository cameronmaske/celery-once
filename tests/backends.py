import mock


class TestBackend(object):
    def __init__(self, settings):
        self.settings = settings

    raise_or_lock = mock.Mock()
    clear_lock = mock.Mock()
