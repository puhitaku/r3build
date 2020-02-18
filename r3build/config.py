import re
from fnmatch import fnmatchcase
from functools import lru_cache

from r3build.processor import Processor, available_processors


class Rule:
    def __init__(self, root_config, rule_config):
        pid = rule_config.get('processor', None)
        if pid is None:
            raise RuntimeError('Specify a processor in the rule')

        p = available_processors.get(pid, None)
        if p is None:
            raise ValueError(f'Unknown processor: "{pid}"')

        self._processor = p(root_config)
        self._root_config = root_config
        self._rule_config = rule_config

    """Common rule properties"""

    @property
    def name(self):
        return self._rule_config.get('name', 'noname')

    @property
    def processor(self):
        return self._processor

    @property
    def only(self):
        return self._rule_config.get('only', "")

    @property
    def path(self):
        return self._rule_config.get('path', '.')

    @property
    def glob(self):
        return self._rule_config.get('glob', "")

    @property
    def glob_exclude(self):
        return self._rule_config.get('glob_exclude', "")

    @property
    def regex(self):
        return self._rule_config.get('regex', "")

    @property
    def regex_exclude(self):
        return self._rule_config.get('regex_exclude', "")

    """Event dispatch function called from main loop"""

    def dispatch(self, event):
        for k, v in self._rule_config.items():
            if k == 'glob' and not self._filter_glob(v, event):
                self._log_filtered_event(event)
                return
            elif k == 'glob_exclude' and self._filter_glob(v, event):
                self._log_filtered_event(event)
                return
            elif k == 'regex' and not self._filter_regex(v, event):
                self._log_filtered_event(event)
                return
            elif k == 'regex_exclude' and self._filter_regex(v, event):
                self._log_filtered_event(event)
                return
            elif k == 'only' and not self._filter_only(v, event):
                self._log_filtered_event(event)
                return

        if self._root_config.log.dispatched_events:
            print(
                f'R3build: detected rule <{self.name}> path={event.src_path}, event={event.event_type}'
            )

        lacks = self.processor.mendatory_keys - set(self._rule_config.keys())
        if len(lacks) >= 1:
            human = ', '.join(sorted(list(lacks)))
            raise RuntimeError(f'Rule <{self.name}> lacks mendatory keys: {human}')
        self.processor.on_change(self._rule_config, event)

    """Utilities"""

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
    rule: list

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
            dispatched_events = log.get('dispatched_events', False) or enable_all
            processor_output = log.get('processor_output', True) or enable_all
            time = log.get('time', False) or enable_all
        self.log = Log()

        # Load Config.event
        event = raw_dict.get('event', dict())
        class Event:
            rate_limit_duration = event.get('rate_limit_duration', 0.01)
        self.event = Event()

        # Load Config.rule
        rule = raw_dict.get('rule', [])
        self.rule = [Rule(self, r) for r in rule]
