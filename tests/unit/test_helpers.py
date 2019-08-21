# -*- coding: utf-8 -*-
from celery_once.helpers import (
    queue_once_key, kwargs_to_list, force_string, import_backend)

import pytest
import six


def test_force_string_1():
    assert force_string('a') == 'a'


def test_force_string_2():
    assert force_string(u'a') == 'a'


def test_force_string_3():
    assert force_string('é') == 'é'


def test_force_string_4():
    assert force_string(u'é') == 'é'


def test_kwargs_to_list_empty():
    keys = kwargs_to_list({})
    assert keys == []


def test_kwargs_to_list_1():
    keys = kwargs_to_list({'int': 1})
    assert keys == ["int-1"]


def test_kwargs_to_list_2():
    keys = kwargs_to_list({'int': 1, 'boolean': True})
    assert keys == ["boolean-True", "int-1"]


def test_kwargs_to_list_3():
    keys = kwargs_to_list({'int': 1, 'boolean': True, 'str': "abc"})
    assert keys == ["boolean-True", "int-1", "str-abc"]


def test_kwargs_to_list_4():
    keys = kwargs_to_list(
        {'int': 1, 'boolean': True, 'str': 'abc', 'list': [1, '2']})
    assert keys == ["boolean-True", "int-1", "list-[1, '2']", "str-abc"]


@pytest.mark.skipif(six.PY3, reason='requires python 2')
def test_kwargs_to_list_5():
    keys = kwargs_to_list(
        {'a': {u'é': 'c'}, 'b': [u'a', 'é'], u'c': 1, 'd': 'é', 'e': u'é'})
    assert keys == [
        "a-{'\\xc3\\xa9': 'c'}",
        "b-['a', '\\xc3\\xa9']",
        "c-1",
        "d-\xc3\xa9",
        "e-\xc3\xa9",
    ]


@pytest.mark.skipif(six.PY2, reason='requires python 3')
def test_kwargs_to_list_6():
    keys = kwargs_to_list(
        {'a': {u'é': 'c'}, 'b': [u'a', 'é'], u'c': 1, 'd': 'é', 'e': u'é'})
    assert keys == ["a-{'é': 'c'}", "b-['a', 'é']", "c-1", "d-é", 'e-é']


def test_kwargs_to_list_nested_dict_is_sorted_1():
    keys = kwargs_to_list({'nested': {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}})
    assert keys == ["nested-{'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}"]


def test_kwargs_to_list_nested_dict_is_sorted_2():
    keys = kwargs_to_list({'nested': {'a': {'a': 1, 'b': 2}, 'c': 2, 'b': 3, 'd': 4, 'e': 5}})
    assert keys == ["nested-{'a': \"{'a': 1, 'b': 2}\", 'b': 3, 'c': 2, 'd': 4, 'e': 5}"]


def test_queue_once_key():
    key = queue_once_key("example", {})
    assert key == "qo_example"


def test_queue_once_key_kwargs():
    key = queue_once_key("example", {'pk': 10})
    assert key == "qo_example_pk-10"


def test_queue_once_key_kwargs_restrict_keys():
    key = queue_once_key("example", {'pk': 10, 'id': 10}, restrict_to=['pk'])
    assert key == "qo_example_pk-10"


@pytest.mark.skipif(six.PY3, reason='requires python 2')
def test_queue_once_key_unicode_py2():
    key = queue_once_key(u"éxample", {'a': u'é', u'b': 'é'})
    assert key == "qo_\xc3\xa9xample_a-\xc3\xa9_b-\xc3\xa9"


@pytest.mark.skipif(six.PY2, reason='requires python 3')
def test_queue_once_key_unicode_py3():
    key = queue_once_key(u"éxample", {'a': u'é', u'b': 'é'})
    assert key == "qo_éxample_a-é_b-é"


class TestBackend(object):
    def __init__(self, settings):
        self.settings = settings


def test_import_backend():
    config = {
        'backend': "tests.backends.TestBackend",
        'settings': 1
    }
    backend = import_backend(config)
    assert backend.settings == 1

