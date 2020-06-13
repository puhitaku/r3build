import importlib
import os
import subprocess
import sys
from multiprocessing import cpu_count
from typing import Set


class Processor:
    id: str
    mendatory_keys: Set[str] = set()
    optional_keys: Set[str] = set()

    def __init__(self, root_config):
        self.root_config = root_config

    def on_change(self, config, event):
        raise NotImplementedError

    def _helper_run(self, cmd, **kwargs):
        print(f'Running command: {cmd}')
        if self.root_config.log.processor_output:
            print('Command output:')
        else:
            kwargs['stdout'] = subprocess.DEVNULL
            kwargs['stderr'] = subprocess.DEVNULL
        return subprocess.run(cmd, **kwargs)

    @staticmethod
    def _helper_merge_env(config):
        env = os.environ
        env.update(config.get('environment', dict()))
        return env


class MakeProcessor(Processor):
    id = 'make'
    optional_keys = {'target', 'environment', 'jobs'}

    def on_change(self, config, event):
        jobs = config.get('jobs', 'auto')
        if jobs == 'auto':
            jobs = str(cpu_count())
        else:
            jobs = str(jobs)

        target = config.get('target', '')

        directory = config.get('directory', '')
        if directory:
            directory = f'-C {directory}'

        cmd = f'make -j{jobs} {directory} {target}'.strip()
        env = self._helper_merge_env(config)
        return self._helper_run(cmd, shell=True, env=env).returncode == 0


class PytestProcessor(Processor):
    id = 'pytest'
    mendatory_keys = {'target'}

    def on_change(self, config, event):
        import pytest

        pytest_target = config['target']
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
        cmd = config.get('command', None)
        env = self._helper_merge_env(config)
        return self._helper_run(cmd, shell=True, env=env).returncode == 0


class InternaltestProcessor(Processor):
    id = 'internaltest'
    history = None

    def __init__(self, config):
        super().__init__(config)
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
