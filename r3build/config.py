from r3build.processor import available_processors

class Config:
    log: object
    event: object
    rule: list

    _kv: dict

    def __init__(self, kv):
        self._kv = kv
        config = self

        log = self.get('log', dict())
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

        event = self.get('event', dict())

        class Event:
            rate_limit_duration = event.get('rate_limit_duration', 0.01)

        self.event = Event()

        class Rule:
            def __init__(self, kv):
                self.name = kv.get('name', 'noname')
                self.processor_id = kv.get('processor', None)
                self.only = kv.get('only', None)
                self.path = kv.get('path', '.')
                self.glob = kv.get('glob', None)
                self.glob_exclude = kv.get('glob_exclude', None)
                self.regex = kv.get('regex', None)
                self.regex_exclude = kv.get('regex_exclude', None)

                if self.processor_id is None:
                    raise RuntimeError('Specify a processor in the rule')
                p = available_processors.get(self.processor_id, None)
                if p is None:
                    raise ValueError(f'Unknown processor: "{self.processor_id}"')
                self.processor = p(config)
                self.processor.kv = kv
                self._additional_keys = self.processor.additional_keys
                self._kv = kv

            def __getattr__(self, key):
                if key in self._additional_keys:
                    return self._kv.get(key, None)
                else:
                    raise AttributeError(f"'{self.name}' rule has no attribute '{key}'")

        rule = self.get('rule', [])
        self.rule = [Rule(r) for r in rule]

    def get(self, key, default=None):
        return self._kv.get(key, default)

