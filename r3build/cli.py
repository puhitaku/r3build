from typing import List

import toml
from watchdog.observers import Observer

from r3build import watcher
from r3build.processor import Processor, available_processors


def load_rules(rules, verbose):
    l = []
    for rule in rules:
        name = rule.get('name', 'noname')
        tid = rule.get('processor', None)
        if tid is None:
            raise ValueError(f'Specify "processor" for the rule "{name}".')

        processor = available_processors.get(tid, None)
        if processor is None:
            raise ValueError(f'Unknown processor: "{tid}"')

        processor = processor()
        processor.name = name
        processor.verbose = verbose
        for k, v in rule.items():
            if k in {'processor'}:
                continue
            processor.set(k, v)

        l.append(processor)
    return l


class R3build:
    watcher: watcher.Watcher
    rules: List[Processor]

    def __init__(self, config_fn=None, config_dict=None, verbose=False):
        if config_fn:
            with open(config_fn) as raw:
                self.config = toml.load(raw)
        elif config_dict:
            self.config = config_dict
        else:
            raise RuntimeError('Specify config file or config dict')

        self.watcher = watcher.Watcher()
        self.rules = load_rules(self.config.get('rule', []), verbose)

    def run(self):
        for rule in self.rules:
            self.watcher.add_path(rule.get('path', '.'))

        def _invoke(event):
            for rule in self.rules:
                rule.dispatch(event)

        self.watcher.set_callback(_invoke)
        self.watcher.start()

    def get_rule(self, name):
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None
