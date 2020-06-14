import importlib
import os
import subprocess
import sys
from multiprocessing import cpu_count
from typing import Set

from watchdog.events import FileSystemEvent

from r3build.prompter import Prompter


class Processor:
    id: str
    mendatory_keys: Set[str] = set()
    optional_keys: Set[str] = set()

    _prompter: Prompter

    def __init__(self, root_config, prompter: Prompter):
        self.root_config = root_config
        self._prompter = prompter

    def on_change(self, config, event):
        raise NotImplementedError

    def _helper_run(self, cmd, **kwargs):
        if not self.root_config.log.job_output:
            kwargs['stdout'] = subprocess.DEVNULL
            kwargs['stderr'] = subprocess.DEVNULL
        return subprocess.run(cmd, **kwargs)

    @staticmethod
    def _helper_merge_env(config, event: FileSystemEvent):
        env = os.environ
        env.update(config.environment)
        env.update({
            'R3_EVENT': event.event_type,
            'R3_FILENAME': event.src_path,
            'R3_IS_DIRECTORY': '1' if event.is_directory else '0',
        })
        return env


class MakeProcessor(Processor):
    id = 'make'
    optional_keys = {'target', 'environment', 'jobs'}

    def on_change(self, config, event):
        jobs = config.jobs
        if jobs == 0:
            jobs = str(cpu_count())
        else:
            jobs = str(jobs)

        target = config.target

        directory = config.directory
        if directory:
            directory = f'-C {directory}'

        cmd = f'make -j{jobs} {directory} {target}'.strip()
        env = self._helper_merge_env(config, event)
        return self._helper_run(cmd, shell=True, env=env).returncode == 0


class PytestProcessor(Processor):
    id = 'pytest'
    mendatory_keys = {'target'}

    def on_change(self, config, event):
        import pytest

        pytest_target = config.target
        modules = [v for k, v in sys.modules.items() if k.startswith(pytest_target)]
        for m in modules:
            importlib.reload(m)
        exitcode = pytest.main([pytest_target])
        return exitcode == 0


class CommandProcessor(Processor):
    id = 'command'
    mendatory_keys = {'command'}
    optional_keys = {'environment'}

    def on_change(self, config, event):
        cmd = config.command
        env = self._helper_merge_env(config, event)
        return self._helper_run(cmd, shell=True, env=env).returncode == 0


class InternaltestProcessor(Processor):
    id = 'internaltest'
    history = None

    def __init__(self, config, prompter):
        super().__init__(config, prompter)
        self.history = []

    def clear_history(self):
        self.history = []

    def on_change(self, config, event):
        self.history.append(event)
        name = config.name
        print(f'<{name}>  event: {event.event_type}, path: {event.src_path}')
        return True


p = [
    MakeProcessor,
    PytestProcessor,
    CommandProcessor,
    InternaltestProcessor,
]

available_processors = {t.id: t for t in p}
