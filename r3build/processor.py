import os
import re
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache
from typing import Any, Dict, List, Set


class Processor:
    tid: str
    mendatory_keys: Set[str]
    kv: Dict[str, Any]
    verbose: bool

    _name: str

    def __init__(self):
        self.name = 'noname'
        self.mendatory_keys = set()
        self.kv = dict()
        self.verbose = False

    def _is_sufficient(self):
        return self.mendatory_keys.issubset(set(self.kv.keys()))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    def get(self, key, default=None):
        return self.kv.get(key, default)

    def set(self, key, value):
        self.kv[key] = value

    def invoke(self, event):
        for k, v in self.kv.items():
            if k == 'glob' and not self._filter_glob(v, event):
                return
            elif k == 'glob_exclude' and self._filter_glob(v, event):
                return
            elif k == 'regex' and not self._filter_regex(v, event):
                return
            elif k == 'regex_exclude' and self._filter_regex(v, event):
                return
            elif k == 'only' and not self._filter_only(v, event):
                return

        if not self._is_sufficient():
            lack = self.mendatory_keys - set(self.kv.keys())
            lack = ', '.join(lack)
            s = 's' if len(lack) > 1 else ''
            raise RuntimeError(f'Processor {self.tid} lacks mendatory key{s}: {lack}')

        if self.verbose:
            print(
                f'R3build: detected rule <{self.name}> path={event.src_path}, event={event.event_type}'
            )
        self.on_change(event)

    def on_change(self, event):
        raise NotImplementedError

    def _filter_glob(self, pattern, event):
        if isinstance(pattern, list):
            return any(fnmatchcase(event.src_path, p) for p in pattern)
        return fnmatchcase(event.src_path, pattern)

    def _filter_regex(self, pattern, event):
        match = self._re_match(pattern)
        return match(event.src_path) is not None

    def _filter_only(self, only, event):
        if isinstance(only, list):
            return any(o == event.event_type for o in only)
        return only == event.event_type

    @staticmethod
    @lru_cache(typed=True)
    def _re_match(pattern):
        return re.compile(pattern).search


class MakeProcessor(Processor):
    tid = 'make'
    mendatory_keys = {'file_range', 'target'}

    def on_change(self, event):
        print(f'make: I am going to make {self.kv["target"]} !!')  # FIXME


class PytestProcessor(Processor):
    tid = 'pytest'

    def on_change(self, event):
        import pytest

        pytest.main()


class CommandProcessor(Processor):
    tid = 'command'
    mendatory_keys = {'command'}

    def on_change(self, event):
        cmd = self.kv.get('command')
        env = os.environ
        env.update(self.kv.get('environment', dict()))
        subprocess.run(cmd, shell=True, env=env)


class TestableProcessor(Processor):
    tid = '_test'
    mendatory_keys = set()
    history = None

    def __init__(self):
        super().__init__()
        self.history = []

    def clear_history(self):
        self.history = []

    def on_change(self, event):
        self.history.append(event)
        print(f'<{self.name}>  event: {event.event_type}, path: {event.src_path}')


p = [
    MakeProcessor,
    PytestProcessor,
    CommandProcessor,
    TestableProcessor,
]

available_processors = {t.tid: t for t in p}
