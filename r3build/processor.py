import os
import re
import subprocess
from dataclasses import dataclass
from fnmatch import fnmatchcase
from functools import lru_cache
from multiprocessing import cpu_count
from typing import Any, Dict, List, Set


class Processor:
    tid: str
    mendatory_keys: Set[str]
    kv: Dict[str, Any]
    verbose: bool

    name: str

    def __init__(self):
        self.name = 'noname'
        self.mendatory_keys = set()
        self.kv = dict()
        self.verbose = False

    def get(self, key, default=None):
        return self.kv.get(key, default)

    def set(self, key, value):
        self.kv[key] = value

    def dispatch(self, event):
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

    def _is_sufficient(self):
        return self.mendatory_keys.issubset(set(self.kv.keys()))

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

    def on_change(self, event):
        jobs = self.get('jobs', 'auto')
        if jobs == 'auto':
            jobs = str(cpu_count())
        else:
            jobs = str(jobs)

        target = self.get('target', '')
        cmd = f'make -j{jobs} {target}'.strip()

        env = os.environ
        env.update(self.get('environment', dict()))

        subprocess.run(cmd, shell=True, env=env)


class PytestProcessor(Processor):
    # RECOMMEND: use `CommandProcessor` to run pytest.
    # FIXME: this processor looks like working but it does not
    #        affect the change of code that are being tested.
    #        We have to find how to identify what's being tested in runtime and
    #        its module name to commence re-import and remove side-effect.
    #        This means it's totally unusable in the field that r3build
    #        focuses into -- doing re-builds and re-tests.
    #        We won't deprecate it for now, but it won't be enabled until this issue is solved.
    tid = 'pytest'

    def on_change(self, event):
        import pytest

        pytest.main()


class CommandProcessor(Processor):
    tid = 'command'
    mendatory_keys = {'command'}

    def on_change(self, event):
        cmd = self.get('command')
        env = os.environ
        env.update(self.get('environment', dict()))
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
    # PytestProcessor,
    CommandProcessor,
    TestableProcessor,
]

available_processors = {t.tid: t for t in p}
