from typing import List

import toml
from watchdog.observers import Observer

from r3build import watcher
from r3build.config import Config
from r3build.processor import Processor, available_processors


class R3build:
    """The core implementation of r3build.

    It parepares a watcher, targets and processors as described in the config
    from a TOML or a dict.

    Preparation is finished in the __init__ and user has to call run() to
    get it working. R3build class handles filesystem events asynchronously;
    they are reported via a callback.

    Reported events are "cleansed" in the outer watcher.
    For the implementation of it, please refer to r3build.watcher.Watcher.
    """

    watcher: watcher.Watcher
    config: Config

    def __init__(self, config_fn=None, config_dict=None, verbose=False):
        # Load the config from toml
        if config_fn:
            with open(config_fn) as raw:
                self.config = Config(toml.load(raw))
        # Or from prepared dict
        elif config_dict:
            self.config = Config(config_dict)
        else:
            raise RuntimeError('Specify config file or config dict')

        self.config.log.all |= verbose
        self.watcher = watcher.Watcher(self.config)

    def run(self):
        # Register paths to watch
        paths = {target.path for target in self.config.target}
        for path in paths:
            self.watcher.add_path(path)

        # Callback for filesystem events
        def _invoke(event):
            for target in self.config.target:
                target.dispatch(event)

        # Register callback and start asynchronous watcher
        self.watcher.callback = _invoke
        self.watcher.start()

    def get_target(self, name):
        for target in self.config.target:
            if target.name == name:
                return target
        return None
