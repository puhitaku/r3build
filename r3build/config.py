from __future__ import annotations

import re
from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from functools import lru_cache
from math import floor
from pathlib import Path
from typing import List

from r3build.config_class import Log, Event, Processor, processors
from r3build.config_validator import AccessValidator
from r3build.processor import Processor as ProcessorParent, available_processors
from r3build.prompter import Prompter


class Job:
    _processor: ProcessorParent
    _root_config: Config
    _job_config: Processor
    _prompter: Prompter

    def __init__(self, root_config: Config, prompter: Prompter, job_config: Processor):
        pid = job_config.type
        p = available_processors.get(pid, None)
        if p is None:
            raise ValueError(f'Unknown processor: "{pid}"')

        self._processor = p(root_config, job_config, prompter)
        self._root_config = root_config
        self._job_config = job_config
        self._prompter = prompter

    """Common job properties"""

    @property
    def name(self):
        return self._job_config.name

    @property
    def processor(self) -> ProcessorParent:
        return self._processor

    @property
    def when(self):
        return self._job_config.when

    @property
    def path(self):
        return self._job_config.path

    def _glob_relative(self, g):
        # If no pattern is specified, return as-is
        if not g:
            return g

        if g.startswith('/') or g.startswith(self.path):
            # If the pattern is absolute or starts with the job path, return as-is
            return g

        # The pattern seems to be relative, add job path, and make it absolute
        path = str((Path(self.path) / g).absolute())
        return path

    @property
    def glob(self):
        g = self._job_config.glob
        if isinstance(g, list):
            return [self._glob_relative(p) for p in g]
        return self._glob_relative(g)

    @property
    def glob_exclude(self):
        g = self._job_config.glob_exclude
        if isinstance(g, list):
            return [self._glob_relative(p) for p in g]
        return self._glob_relative(g)

    @property
    def regex(self):
        return self._job_config.regex

    @property
    def regex_exclude(self):
        return self._job_config.regex_exclude

    def trigger(self, event):
        if self.glob and not self._filter_glob(self.glob, event):
            self._log_ignored_event(event)
            return False
        elif self.glob_exclude and self._filter_glob(self.glob_exclude, event):
            self._log_ignored_event(event)
            return False
        elif self.regex and not self._filter_regex(self.regex, event):
            self._log_ignored_event(event)
            return False
        elif self.regex_exclude and self._filter_regex(self.regex_exclude, event):
            self._log_ignored_event(event)
            return False
        elif self.when and not self._filter_when(self.when, event):
            self._log_ignored_event(event)
            return False

        if self._root_config.log.launched_events:
            self._prompter.trigger(self.name, event)

        start = datetime.now()
        result = self.processor.on_change(event)
        diff = datetime.now() - start

        info = []

        if result.message:
            info.append(result.message)
        else:
            if self._root_config.log.result:
                mes = 'SUCCEEDED' if result.success else 'FAILED'
                info.append(mes)

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
            if result.color:
                color = result.color
            else:
                color = "green" if result.success else "red"
            self._prompter.result(self.name, info, color)

        return True

    """Utilities"""

    def _filter_glob(self, pattern, event):
        if isinstance(pattern, list):
            abspath = str(Path(event.src_path).absolute())
            return any(fnmatchcase(abspath, str(Path(p).absolute())) for p in pattern)
        abspath = str(Path(event.src_path).absolute())
        return fnmatchcase(abspath, str(Path(pattern).absolute()))

    def _filter_regex(self, pattern, event):
        if isinstance(pattern, list):
            match = [self._re_match(p) for p in pattern]
        else:
            match = [self._re_match(pattern)]
        return any(m(event.src_path) is not None for m in match)

    def _filter_when(self, when, event):
        if isinstance(when, list):
            return any(o == event.event_type for o in when)
        return when == event.event_type

    def _log_ignored_event(self, event):
        if self._root_config.log.ignored_events:
            self._prompter.ignore(self.name, "patterns don't match", event)

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
        self.__annotations__.update(
            {
                'log': Log,
                'event': Event,
                'job': List[Job],
            }
        )

        super().__init__('root', dict())
        self.log = Log('log', raw_dict.get('log', dict()))
        if self.log.all:
            self.log.accepted_events = True
            self.log.ignored_events = True
            self.log.launched_events = True

        self.event = Event('event', raw_dict.get('event', dict()))

        rawjobs = raw_dict.get('job', [])
        if not rawjobs:
            raise ValueError("The config has no job definition")

        self.job = []
        for job_def in raw_dict.get('job', []):
            proc = job_def.get('type', None)
            if proc is None:
                raise ValueError(
                    f'The job definition "{job_def.get("name", "(noname)")}" lacks "type" key'
                )
            elif proc not in processors:
                raise ValueError(f'Unknown processor: "{proc}"')

            procins = processors[proc](job_def.get('name', '(noname)'), job_def)
            job = Job(self, Prompter(self), procins)
            self.job.append(job)
