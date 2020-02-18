import os
import re
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache
from multiprocessing import cpu_count
from typing import Any, Dict, List, Set


class Processor:
    id: str
    mendatory_keys: Set[str] = set()
    optional_keys: Set[str] = set()

    def __init__(self, root_config):
        self.root_config = root_config

    def on_change(self, config, event):
        raise NotImplementedError


class MakeProcessor(Processor):
    id = 'make'
    optional_keys = {'target', 'environment', 'jobs'}

    def on_change(self, config, event):
        jobs = config.get('jobs', 'auto')
        if jobs == 'auto':
            jobs = str(cpu_count())
        else:
            jobs = str(jobs)

        target = config.get('target', '')
        cmd = f'make -j{jobs} {target}'.strip()

        env = os.environ
        env.update(config.get('environment', dict()))

        kwargs = dict()
        if not self.root_config.log.processor_output:
            kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}

        subprocess.run(cmd, shell=True, env=env, **kwargs)


class PytestProcessor(Processor):
    # RECOMMEND: use `CommandProcessor` to run pytest.
    # FIXME: this processor looks like working but it does not
    #        affect the change of code that are being tested.
    #        We have to find how to identify what's being tested in runtime and
    #        its module name to commence re-import and remove side-effect.
    #        This means it's totally unusable in the field that r3build
    #        focuses into -- doing re-builds and re-tests.
    #        We won't deprecate it for now, but it won't be enabled until this issue is solved.
    id = 'pytest'

    def on_change(self, event):
        import pytest

        pytest.main()


class CommandProcessor(Processor):
    id = 'command'
    mendatory_keys = {'command'}
    optional_keys = {'environment'}

    def on_change(self, config, event):
        cmd = config.get('command', None)
        env = os.environ
        env.update(config.get('environment', dict()))

        kwargs = dict()
        if not self.root_config.log.processor_output:
            kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}

        subprocess.run(cmd, shell=True, env=env, **kwargs)


class TestableProcessor(Processor):
    id = '_test'
    history = None

    def __init__(self, config):
        super().__init__(config)
        self.history = []

    def clear_history(self):
        self.history = []

    def on_change(self, config, event):
        self.history.append(event)
        name = config.get('name', 'noname')
        print(f'<{name}>  event: {event.event_type}, path: {event.src_path}')


p = [
    MakeProcessor,
    # PytestProcessor,
    CommandProcessor,
    TestableProcessor,
]

available_processors = {t.id: t for t in p}
