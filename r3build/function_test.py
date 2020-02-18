import time
from pathlib import Path

import pytest

from r3build.cli import R3build


@pytest.fixture(scope='session')
def tmp(tmpdir_factory):
    p = Path(tmpdir_factory.mktemp('r3'))
    return p


@pytest.fixture(scope='session')
def instance(tmp):
    rules = [
        {
            'name': 'glob1',
            'processor': '_test',
            'path': str(tmp),
            'glob': '*/glob1/*/*.txt',
        },
        {
            'name': 'glob2',
            'processor': '_test',
            'path': str(tmp),
            'glob': '*/glob2/*/*.txt',
            'glob_exclude': '*/glob2/exclude/*.txt',
        },
        {
            'name': 'regex1',
            'processor': '_test',
            'path': str(tmp),
            'regex': '.+/regex1/.+/[^.]+\.txt',
        },
        {
            'name': 'regex2',
            'processor': '_test',
            'path': str(tmp),
            'regex': '.+/regex2/.+/[^.]+\.txt',
            'regex_exclude': '.+/regex2/exclude/[^.]+\.txt',
        },
    ]
    r3 = R3build(config_dict={'rule': rules})
    r3.run()
    return r3


def touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w'):
        pass
    time.sleep(1)


def write(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write('mikumiku')
    time.sleep(1)


def test_glob1(instance, tmp):
    rule = instance.get_rule('glob1')
    rule.processor.clear_history()

    touch(tmp / 'glob1/bar.txt')
    assert len(rule.processor.history) == 0

    touch(tmp / 'glob1/foo/bar.txt')
    assert len(rule.processor.history) == 1
    ev = rule.processor.history[0]
    assert ev.src_path == str(tmp / 'glob1/foo/bar.txt')
    assert ev.event_type == 'created'

    write(tmp / 'glob1/foo/bar.txt')
    assert len(rule.processor.history) == 2
    ev = rule.processor.history[1]
    assert ev.src_path == str(tmp / 'glob1/foo/bar.txt')
    assert ev.event_type == 'modified'


def test_glob2(instance, tmp):
    rule = instance.get_rule('glob2')
    rule.processor.clear_history()

    touch(tmp / 'glob2/foo/bar.txt')
    assert len(rule.processor.history) == 1
    ev = rule.processor.history[0]
    assert ev.src_path == str(tmp / 'glob2/foo/bar.txt')
    assert ev.event_type == 'created'

    touch(tmp / 'glob2/exclude/bar.txt')
    assert len(rule.processor.history) == 1

    write(tmp / 'glob2/foo/bar.txt')
    assert len(rule.processor.history) == 2
    ev = rule.processor.history[1]
    assert ev.src_path == str(tmp / 'glob2/foo/bar.txt')
    assert ev.event_type == 'modified'

    write(tmp / 'glob2/exclude/bar.txt')
    assert len(rule.processor.history) == 2


def test_regex1(instance, tmp):
    rule = instance.get_rule('regex1')
    rule.processor.clear_history()

    touch(tmp / 'regex1/bar.txt')
    assert len(rule.processor.history) == 0

    touch(tmp / 'regex1/foo/bar.txt')
    assert len(rule.processor.history) == 1
    ev = rule.processor.history[0]
    assert ev.src_path == str(tmp / 'regex1/foo/bar.txt')
    assert ev.event_type == 'created'

    write(tmp / 'regex1/foo/bar.txt')
    assert len(rule.processor.history) == 2
    ev = rule.processor.history[1]
    assert ev.src_path == str(tmp / 'regex1/foo/bar.txt')
    assert ev.event_type == 'modified'


def test_regex2(instance, tmp):
    rule = instance.get_rule('regex2')
    rule.processor.clear_history()

    touch(tmp / 'regex2/foo/bar.txt')
    assert len(rule.processor.history) == 1
    ev = rule.processor.history[0]
    assert ev.src_path == str(tmp / 'regex2/foo/bar.txt')
    assert ev.event_type == 'created'

    touch(tmp / 'regex2/exclude/bar.txt')
    assert len(rule.processor.history) == 1

    write(tmp / 'regex2/foo/bar.txt')
    assert len(rule.processor.history) == 2
    ev = rule.processor.history[1]
    assert ev.src_path == str(tmp / 'regex2/foo/bar.txt')
    assert ev.event_type == 'modified'

    write(tmp / 'regex2/exclude/bar.txt')
    assert len(rule.processor.history) == 2
