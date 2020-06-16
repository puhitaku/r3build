import time
from pathlib import Path
from random import randint
from textwrap import dedent

import pytest

from r3build.cli import R3build


@pytest.fixture(scope='session')
def tmp(tmpdir_factory):
    p = Path(tmpdir_factory.mktemp('r3'))
    return p


@pytest.fixture(scope='session')
def instance(tmp):
    jobs = [
        {
            'name': 'glob1',
            'type': 'internaltest',
            'path': str(tmp),
            'glob': 'glob1/*/*.txt',
            'when': ['created', 'modified'],
        },
        {
            'name': 'glob2',
            'type': 'internaltest',
            'path': str(tmp),
            'glob': ['glob2/*/*.txt'],
            'glob_exclude': ['glob2/exclude/*.txt'],
            'when': ['created', 'modified'],
        },
        {
            'name': 'regex1',
            'type': 'internaltest',
            'path': str(tmp),
            'regex': r'.+/regex1/.+/[^.]+\.txt',
            'when': ['created', 'modified'],
        },
        {
            'name': 'regex2',
            'type': 'internaltest',
            'path': str(tmp),
            'regex': [r'.+/regex2/.+/[^.]+\.txt'],
            'regex_exclude': ['.+/regex2/exclude/[^.]+\.txt'],
            'when': ['created', 'modified'],
        },
        {
            'name': 'daemon',
            'type': 'daemon',
            'path': str(tmp),
            'glob': 'app.py',
            'when': 'modified',
            'command': f'python3 {tmp / "app.py"}',
            'stdout': False,
            'stderr': False,
        }
    ]
    log = {
        'all': True,
    }
    event = {
        'ignore_events_while_run': False,
    }
    gen_daemon(tmp)
    r3 = R3build(config_dict={'job': jobs, 'log': log, 'event': event})
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


def gen_daemon(path):
    with open(path / 'app.py', 'w') as f:
        f.write(dedent(f"""
            import time
            print('Daemon has started! nonce={randint(0, 10000)}')
            for i in range(100):
                time.sleep(1)
        """))


def test_config():
    with pytest.raises(ValueError):  # no config
        R3build()

    with pytest.raises(ValueError):  # no job
        R3build(config_dict={'log': {}})

    with pytest.raises(ValueError):  # lack processor
        R3build(config_dict={
            'job': [
                {}
            ]
        })

    with pytest.raises(ValueError):  # unknown processor
        R3build(config_dict={
            'job': [
                {'type': 'sugoiprocessor'}
            ]
        })


def test_glob1(instance, tmp):
    job = instance.get_job('glob1')
    job.processor.clear_history()

    touch(tmp / 'glob1/bar.txt')
    assert len(job.processor.history) == 0

    touch(tmp / 'glob1/foo/bar.txt')
    assert len(job.processor.history) == 1
    ev = job.processor.history[0]
    assert ev.src_path == str(tmp / 'glob1/foo/bar.txt')
    assert ev.event_type == 'created'

    write(tmp / 'glob1/foo/bar.txt')
    assert len(job.processor.history) == 2
    ev = job.processor.history[1]
    assert ev.src_path == str(tmp / 'glob1/foo/bar.txt')
    assert ev.event_type == 'modified'


def test_glob2(instance, tmp):
    job = instance.get_job('glob2')
    job.processor.clear_history()

    touch(tmp / 'glob2/foo/bar.txt')
    assert len(job.processor.history) == 1
    ev = job.processor.history[0]
    assert ev.src_path == str(tmp / 'glob2/foo/bar.txt')
    assert ev.event_type == 'created'

    touch(tmp / 'glob2/exclude/bar.txt')
    assert len(job.processor.history) == 1

    write(tmp / 'glob2/foo/bar.txt')
    assert len(job.processor.history) == 2
    ev = job.processor.history[1]
    assert ev.src_path == str(tmp / 'glob2/foo/bar.txt')
    assert ev.event_type == 'modified'

    write(tmp / 'glob2/exclude/bar.txt')
    assert len(job.processor.history) == 2


def test_regex1(instance, tmp):
    job = instance.get_job('regex1')
    job.processor.clear_history()

    touch(tmp / 'regex1/bar.txt')
    assert len(job.processor.history) == 0

    touch(tmp / 'regex1/foo/bar.txt')
    assert len(job.processor.history) == 1
    ev = job.processor.history[0]
    assert ev.src_path == str(tmp / 'regex1/foo/bar.txt')
    assert ev.event_type == 'created'

    write(tmp / 'regex1/foo/bar.txt')
    assert len(job.processor.history) == 2
    ev = job.processor.history[1]
    assert ev.src_path == str(tmp / 'regex1/foo/bar.txt')
    assert ev.event_type == 'modified'


def test_regex2(instance, tmp):
    job = instance.get_job('regex2')
    job.processor.clear_history()

    touch(tmp / 'regex2/foo/bar.txt')
    assert len(job.processor.history) == 1
    ev = job.processor.history[0]
    assert ev.src_path == str(tmp / 'regex2/foo/bar.txt')
    assert ev.event_type == 'created'

    touch(tmp / 'regex2/exclude/bar.txt')
    assert len(job.processor.history) == 1

    write(tmp / 'regex2/foo/bar.txt')
    assert len(job.processor.history) == 2
    ev = job.processor.history[1]
    assert ev.src_path == str(tmp / 'regex2/foo/bar.txt')
    assert ev.event_type == 'modified'

    write(tmp / 'regex2/exclude/bar.txt')
    assert len(job.processor.history) == 2


def test_daemon_processor(instance, tmp):
    job = instance.get_job('daemon')
    assert job.processor._child_process.poll() is None
    pid = job.processor._child_process.pid

    # Reload 1
    gen_daemon(tmp)

    for _ in range(50):
        if job.processor._child_process.pid != pid:
            break
        time.sleep(0.1)
    else:
        raise TimeoutError

    pid = job.processor._child_process.pid

    # Reload 2
    gen_daemon(tmp)
    time.sleep(0.1)

    for _ in range(50):
        if job.processor._child_process.pid != pid:
            break
        time.sleep(0.1)
    else:
        raise TimeoutError
