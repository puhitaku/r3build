import re
from datetime import datetime, timedelta
from fnmatch import fnmatchcase
from functools import lru_cache
from math import floor

from r3build.processor import available_processors


class Target:
    def __init__(self, root_config, target_config):
        pid = target_config.get('processor', None)
        if pid is None:
            raise RuntimeError('Specify a processor in the target')

        p = available_processors.get(pid, None)
        if p is None:
            raise ValueError(f'Unknown processor: "{pid}"')

        self._processor = p(root_config)
        self._root_config = root_config
        self._target_config = target_config

    """Common target properties"""

    @property
    def name(self):
        return self._target_config.get('name', 'noname')

    @property
    def processor(self):
        return self._processor

    @property
    def when(self):
        return self._target_config.get('when', "")

    @property
    def path(self):
        return self._target_config.get('path', '.')

    @property
    def glob(self):
        return self._target_config.get('glob', "")

    @property
    def glob_exclude(self):
        return self._target_config.get('glob_exclude', "")

    @property
    def regex(self):
        return self._target_config.get('regex', "")

    @property
    def regex_exclude(self):
        return self._target_config.get('regex_exclude', "")

    """Event dispatch function called from main loop"""

    def dispatch(self, event):
        for k, v in self._target_config.items():
            if k == 'glob' and not self._filter_glob(v, event):
                self._log_filtered_event(event)
                return False
            elif k == 'glob_exclude' and self._filter_glob(v, event):
                self._log_filtered_event(event)
                return False
            elif k == 'regex' and not self._filter_regex(v, event):
                self._log_filtered_event(event)
                return False
            elif k == 'regex_exclude' and self._filter_regex(v, event):
                self._log_filtered_event(event)
                return False
            elif k == 'when' and not self._filter_when(v, event):
                self._log_filtered_event(event)
                return False

        if self._root_config.log.dispatched_events:
            print(f'\n >> R3BUILD >> detected a change for target "{self.name}" >>\n')

        lacks = self.processor.mendatory_keys - set(self._target_config.keys())
        if len(lacks) >= 1:
            human = ', '.join(sorted(list(lacks)))
            raise RuntimeError(f'Target <{self.name}> lacks mendatory keys: {human}')

        start = datetime.now()
        result = self.processor.on_change(self._target_config, event)
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
            print(f'\n >> R3BUILD >> target "{self.name}" {info} >>\n')

        return True

    """Utilities"""

    def _filter_glob(self, pattern, event):
        if isinstance(pattern, list):
            return any(fnmatchcase(event.src_path, p) for p in pattern)
        return fnmatchcase(event.src_path, pattern)

    def _filter_regex(self, pattern, event):
        match = self._re_match(pattern)
        return match(event.src_path) is not None

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


class Config:
    log: object
    event: object
    target: list

    _raw_dict: dict

    def __init__(self, raw_dict):
        self._raw_dict = raw_dict

        # Load Config.log
        log = raw_dict.get('log', dict())
        enable_all = log.get('all', False)

        class Log:
            all = enable_all
            accepted_events = log.get('accepted_events', False) or enable_all
            rate_limited_events = log.get('rate_limited_events', False) or enable_all
            filtered_events = log.get('filtered_events', False) or enable_all
            dispatched_events = log.get('dispatched_events', True) or enable_all
            processor_output = log.get('processor_output', True) or enable_all
            result = log.get('result', True) or enable_all
            time = log.get('time', False) or enable_all

        self.log = Log()

        # Load Config.event
        event = raw_dict.get('event', dict())

        class Event:
            rate_limit_duration = event.get('rate_limit_duration', 0.01)
            ignore_events_while_run = event.get('ignore_events_while_run', True)

        self.event = Event()

        # Load Config.target
        target = raw_dict.get('target', [])
        self.target = [Target(self, r) for r in target]
