from __future__ import annotations

import re
from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from functools import lru_cache
from math import floor
from typing import List

from r3build.processor import available_processors
from r3build.config_class import Log, Event, Processor, processors
from r3build.config_validator import AccessValidator


class Target:
    def __init__(self, root_config: Config, target_config: Processor):
        pid = target_config.processor
        p = available_processors.get(pid, None)
        if p is None:
            raise ValueError(f'Unknown processor: "{pid}"')

        self._processor = p(root_config)
        self._root_config = root_config
        self._target_config = target_config

    """Common target properties"""

    @property
    def name(self):
        return self._target_config.name

    @property
    def processor(self):
        return self._processor

    @property
    def when(self):
        return self._target_config.when

    @property
    def path(self):
        return self._target_config.path

    @property
    def glob(self):
        return self._target_config.glob

    @property
    def glob_exclude(self):
        return self._target_config.glob_exclude

    @property
    def regex(self):
        return self._target_config.regex

    @property
    def regex_exclude(self):
        return self._target_config.regex_exclude

    """Event dispatch function called from main loop"""

    def dispatch(self, event):
        if self.glob and not self._filter_glob(self.glob, event):
            self._log_filtered_event(event)
            return False
        elif self.glob_exclude and self._filter_glob(self.glob_exclude, event):
            self._log_filtered_event(event)
            return False
        elif self.regex and not self._filter_regex(self.regex, event):
            self._log_filtered_event(event)
            return False
        elif self.regex_exclude and self._filter_regex(self.regex_exclude, event):
            self._log_filtered_event(event)
            return False
        elif self.when and not self._filter_when(self.when, event):
            self._log_filtered_event(event)
            return False

        if self._root_config.log.all or self._root_config.log.dispatched_events:
            print(f'\n >> R3BUILD >> detected a change for target "{self.name}" >>\n')

        start = datetime.now()
        result = self.processor.on_change(self._target_config, event)
        diff = datetime.now() - start

        info = []

        if self._root_config.log.all or self._root_config.log.result:
            mes = 'SUCCEEDED' if result else 'FAILED'
            info.append(f'has {mes}')

        if self._root_config.log.all or self._root_config.log.time:
            h = floor(diff / timedelta(hours=1))
            m = floor(diff / timedelta(minutes=1)) % 60
            s = floor(diff / timedelta(seconds=1)) % 60
            h = f'{h:02d}h' if h > 0 else ''
            m = f'{m:02d}m' if m > 0 else ''
            s = f'{s:02d}s'
            info.append(f'took {h}{m}{s}')

        if info:
            info = ', '.join(info)
            print(f'\n >> R3BUILD >> target "{self.name}" {info} >>\n')

        return True

    """Utilities"""

    def _filter_glob(self, pattern, event):
        if isinstance(pattern, list):
            return any(fnmatchcase(event.src_path, p) for p in pattern)
        return fnmatchcase(event.src_path, pattern)

    def _filter_regex(self, pattern, event):
        if isinstance(pattern, str):
            match = [self._re_match(pattern)]
        elif isinstance(pattern, list):
            match = [self._re_match(p) for p in pattern]
        else:
            # TODO: ensure type in parsing stage
            raise TypeError(f"unsupported type for regex rules: {type(pattern)}")
        return any(m(event.src_path) is not None for m in match)

    def _filter_when(self, when, event):
        if isinstance(when, list):
            return any(o == event.event_type for o in when)
        return when == event.event_type

    def _log_filtered_event(self, event):
        if self._root_config.log.all or self._root_config.log.filtered_events:
            print(f'Filtered event: {event}')

    @staticmethod
    @lru_cache(typed=True)
    def _re_match(pattern):
        return re.compile(pattern).search


class Config(AccessValidator):
    _slots = ['log', 'event', 'target']

    log: Log = None
    event: Event = None
    target: List[Target] = None

    def __init__(self, raw_dict):
        # SUPER dirty hack ...
        self.__annotations__['Log'] = Log
        self.__annotations__.update({
            'log': Log,
            'event': Event,
            'target': List[Target],
        })

        super().__init__('root', dict())
        self.log = Log('log', raw_dict.get('log', dict()))
        self.event = Event('event', raw_dict.get('event', dict()))

        self.target = []
        for proc_def in raw_dict.get('target', []):
            proc = proc_def.get('processor', None)
            if proc is None:
                raise ValueError(f'The target definition "{proc_def.get("name", "(noname)")}" lacks "processor" key')
            elif proc not in processors:
                raise ValueError(f'Unknown processor: "{proc}"')

            procins = processors[proc](proc_def.get('name', '(noname)'), proc_def)
            target = Target(self, procins)
            self.target.append(target)
