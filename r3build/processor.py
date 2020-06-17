from __future__ import annotations

import importlib
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import IntEnum
from multiprocessing import cpu_count
from subprocess import Popen
from typing import Optional, Set

from watchdog.events import FileSystemEvent

from r3build.prompter import Prompter
from r3build.config_class import *


class Processor:
    id: str
    mendatory_keys: Set[str] = set()
    optional_keys: Set[str] = set()

    _prompter: Prompter

    def __init__(self, root_config, job_config, prompter: Prompter):
        self._root_config = root_config
        self._config = job_config
        self._prompter = prompter

    def open(self):
        """close is the start-up function that runs in the beginning of operation. Implementation is optional."""
        pass

    def on_change(self, event: FileSystemEvent) -> ProcessorResult:
        """on_change is the entrypoint for an incoming event. Derived classes must impelemnt it."""
        raise NotImplementedError

    def close(self):
        """close is the clean-up function that runs very before r3build exits. Implementation is optional."""
        pass

    def _helper_run(self, cmd, **kwargs):
        if not self._root_config.log.job_output:
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


@dataclass
class ProcessorResult:
    success: bool
    message: str
    color: str

    def __init__(self, success, message="", color=""):
        self.success, self.message, self.color = success, message, color


class MakeProcessor(Processor):
    id = 'make'
    optional_keys = {'target', 'environment', 'jobs'}

    _config: MakeProcessorConfig

    def on_change(self, event: FileSystemEvent):
        jobs = self._config.jobs
        if jobs == 0:
            jobs = str(cpu_count())
        else:
            jobs = str(jobs)

        target = self._config.target

        directory = self._config.directory
        if directory:
            directory = f'-C {directory}'

        cmd = f'make -j{jobs} {directory} {target}'.strip()
        env = self._helper_merge_env(self._config, event)
        return ProcessorResult(success=self._helper_run(cmd, shell=True, env=env).returncode == 0)


class PytestProcessor(Processor):
    id = 'pytest'
    mendatory_keys = {'target'}

    _config: PytestProcessorConfig

    def on_change(self, event: FileSystemEvent):
        import pytest

        pytest_target = self._config.target
        modules = [v for k, v in sys.modules.items() if k.startswith(pytest_target)]
        for m in modules:
            importlib.reload(m)
        exitcode = pytest.main([pytest_target])
        return ProcessorResult(success=exitcode == 0)


class CommandProcessor(Processor):
    id = 'command'
    mendatory_keys = {'command'}
    optional_keys = {'environment'}

    _config: CommandProcessorConfig

    def on_change(self, event: FileSystemEvent):
        cmd = self._config.command
        env = self._helper_merge_env(self._config, event)
        return ProcessorResult(success=self._helper_run(cmd, shell=True, env=env).returncode == 0)


class DaemonProcessor(Processor):
    id = 'daemon'
    mendatory_keys = {'command'}
    optional_keys = {'signal', 'environment'}

    _config: DaemonProcessorConfig

    _signal: int = None
    _child_process: Optional[Popen] = None

    def __init__(self, root_config, job_config: DaemonProcessorConfig, prompter):
        super().__init__(root_config, job_config, prompter)

        signals_str = {s.name: s for s in signal.valid_signals() if isinstance(s, IntEnum)}
        signals_int = [s for s in signal.valid_signals()]

        if isinstance(job_config.signal, int):
            if job_config.signal not in signals_int:
                raise ValueError(f'Signal {job_config.signal} is not available.')
            self._signal = job_config.signal
        else:
            if job_config.signal not in signals_str:
                raise ValueError(f'Signal {job_config.signal} is not available.')
            self._signal = signals_str[job_config.signal]

    def open(self):
        self._start()
        self._prompter.procsay(self._config.name, f'Started: `{self._config.command}`')

    def on_change(self, event: FileSystemEvent):
        self._prompter.procsay(self._config.name, f'Restarting...')
        self._stop()
        self._start()
        return ProcessorResult(success=True, message="Restarted!")

    def close(self):
        self._stop()
        self._prompter.procsay(self._config.name, f'Stopped!')

    def _start(self):
        stdout = None if self._config.stdout else subprocess.DEVNULL
        stderr = None if self._config.stderr else subprocess.DEVNULL
        # Thanks to: https://stackoverflow.com/a/22582602/2735798
        self._child_process = Popen(
            self._config.command,
            shell=True,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=os.setsid,
        )

    def _stop(self):
        if self._child_process is None:
            return

        for duration in self._backoff(self._config.timeout):
            # Graceful
            os.killpg(os.getpgid(self._child_process.pid), self._signal)
            self._fire_and_forget()
            if self._child_process.poll() is not None:
                break
            time.sleep(duration)
        else:
            # You have been terminated
            self._fire_and_forget(sig=signal.SIGKILL)
        self._child_process = None

    def _fire_and_forget(self, sig=None):
        if sig is None:
            sig = self._signal
        try:
            os.killpg(os.getpgid(self._child_process.pid), sig)
        except Exception:
            pass

    @staticmethod
    def _backoff(timeout):
        class Backoff:
            def __init__(self, d, timeout):
                self.d, self.timeout = d, timeout
                self.acc, self.stop = 0, False

            def __iter__(self):
                return self

            def __next__(self):
                if self.stop:
                    raise StopIteration

                if self.acc + self.d > self.timeout:
                    self.stop = True
                    return self.timeout - self.acc

                ret = self.d
                self.acc += self.d
                self.d *= 2
                return ret
        return Backoff(0.1, timeout)


class InternaltestProcessor(Processor):
    id = 'internaltest'
    history = None

    _config: InternaltestProcessorConfig

    def __init__(self, root_config, job_config, prompter):
        super().__init__(root_config, job_config, prompter)
        self.history = []

    def clear_history(self):
        self.history = []

    def on_change(self, event: FileSystemEvent):
        self.history.append(event)
        name = self._config.name
        print(f'<{name}>  event: {event.event_type}, path: {event.src_path}')
        return ProcessorResult(success=True)


p = [
    MakeProcessor,
    PytestProcessor,
    CommandProcessor,
    DaemonProcessor,
    InternaltestProcessor,
]

available_processors = {t.id: t for t in p}
