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


class Job:
    def __init__(self, root_config: Config, job_config: Processor):
        pid = job_config.type
        p = available_processors.get(pid, None)
        if p is None:
            raise ValueError(f'Unknown processor: "{pid}"')

        self._processor = p(root_config)
        self._root_config = root_config
        self._job_config = job_config

    """Common job properties"""

    @property
    def name(self):
        return self._job_config.name

    @property
    def processor(self):
        return self._processor

    @property
    def when(self):
        return self._job_config.when

    @property
    def path(self):
        return self._job_config.path

    @property
    def glob(self):
        return self._job_config.glob

    @property
    def glob_exclude(self):
        return self._job_config.glob_exclude

    @property
    def regex(self):
        return self._job_config.regex

    @property
    def regex_exclude(self):
        return self._job_config.regex_exclude

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

        if self._root_config.log.dispatched_events:
            print(f'\n >> R3BUILD >> detected a change for job "{self.name}" >>\n')

        start = datetime.now()
        result = self.processor.on_change(self._job_config, event)
        diff = datetime.now() - start

        info = []

        if self._root_config.log.result:
            mes = 'SUCCEEDED' if result else 'FAILED'
            info.append(f'has {mes}')

        if self._root_config.log.time:
            h = floor(diff / timedelta(hours=1))
            m = floor(diff / timedelta(minutes=1)) % 60
            s = floor(diff / timedelta(seconds=1)) % 60
            h = f'{h:02d}h' if h > 0 else ''
            m = f'{m:02d}m' if m > 0 else ''
            s = f'{s:02d}s'
            info.append(f'took {h}{m}{s}')

        if info:
            info = ', '.join(info)
            print(f'\n >> R3BUILD >> job "{self.name}" {info} >>\n')

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
        if self._root_config.log.filtered_events:
            print(f'Filtered event: {event}')

    @staticmethod
    @lru_cache(typed=True)
    def _re_match(pattern):
        return re.compile(pattern).search


class Config(AccessValidator):
    _slots = ['log', 'event', 'job']

    log: Log = None
    event: Event = None
    job: List[Job] = None

    def __init__(self, raw_dict):
        # SUPER dirty hack ...
        self.__annotations__['Log'] = Log
        self.__annotations__.update({
            'log': Log,
            'event': Event,
            'job': List[Job],
        })

        super().__init__('root', dict())
        self.log = Log('log', raw_dict.get('log', dict()))
        if self.log.all:
            self.log.accepted_events = True
            self.log.rate_limited_events = True
            self.log.filtered_events = True
            self.log.dispatched_events = True

        self.event = Event('event', raw_dict.get('event', dict()))

        self.job = []
        for job_def in raw_dict.get('job', []):
            proc = job_def.get('type', None)
            if proc is None:
                raise ValueError(f'The job definition "{job_def.get("name", "(noname)")}" lacks "type" key')
            elif proc not in processors:
                raise ValueError(f'Unknown processor: "{proc}"')

            procins = processors[proc](job_def.get('name', '(noname)'), job_def)
            job = Job(self, procins)
            self.job.append(job)
