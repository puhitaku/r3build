from r3build.processor import available_processors

class Config:
    kv: dict

    def __init__(self, config):
        self.kv = config

        log = self.get('log', dict())
        enable_all = log.get('all', False)

        class Log:
            all = enable_all
            accepted_events = log.get('accepted_events', True) or enable_all
            ignored_events = log.get('ignored_events', False) or enable_all
            rate_limited_events = log.get('rate_limited_events', False) or enable_all
            processor_output = log.get('processor_output', True) or enable_all
            time = log.get('time', False) or enable_all

        self.log = Log()

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
                self.processor = p()
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
        return self.kv.get(key, default)

