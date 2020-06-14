import toml

from r3build import watcher
from r3build.config import Config
from r3build.prompter import Prompter


class R3build:
    """The core implementation of r3build.

    It parepares a watcher, jobs and processors as described in the config
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
                self.config = Config(toml.load(raw), p)
        # Or from prepared dict
        elif config_dict:
            self.config = Config(config_dict)
        else:
            raise RuntimeError('Specify config file or config dict')

        self.config.log.all |= verbose
        self.watcher = watcher.Watcher(self.config, Prompter(self.config))

    def run(self):
        # Register paths to watch
        paths = {job.path for job in self.config.job}
        for path in paths:
            self.watcher.add_path(path)

        # Callback for filesystem events
        def _invoke(event):
            accepted = False
            for job in self.config.job:
                accepted |= job.dispatch(event)
            return accepted

        # Register callback and start asynchronous watcher
        self.watcher.callback = _invoke
        self.watcher.start()

    def get_job(self, name):
        for job in self.config.job:
            if job.name == name:
                return job
        return None
