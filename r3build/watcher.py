from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable, Dict

from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

from r3build.config import Config
from r3build.prompter import Prompter


class EventBuffer:
    """Thread-safe event buffer.

    EventBuffer intends to store pairs of FileSystemEvent and its timestamp.
    """

    d: Dict[FileSystemEvent, float]
    mutex: threading.Lock

    def __init__(self, *args, **kwargs):
        self.d = dict(*args, **kwargs)
        self.mutex = threading.Lock()

    def __do(self, fn, *args, **kwargs):
        self.mutex.acquire()
        try:
            return fn(*args, **kwargs)
        finally:
            self.mutex.release()

    def events(self):
        return self.__do(lambda: list(self.d.keys()))

    def items(self):
        return self.__do(lambda: list(self.d.items()))

    def push(self, event):
        self.__do(lambda: self.d.__setitem__(event, datetime.now().timestamp()))

    def pop(self, event):
        self.__do(lambda: self.d.pop(event))


class Watcher(FileSystemEventHandler, threading.Thread):
    """Sophisticated watcher implementation.

    This layer is intended to "cleanse" filesystem events;
    remove duplicates in short term (~10ms) to make it easy
    to handle events in later stage.

    That being said, this does not have to be asynchronous.
    We are looking forward to refactor it.
    """

    config: Config
    prompter: Prompter

    observer: Observer
    has_path: bool
    event_buffer: EventBuffer
    _callback: Callable[[FileSystemEvent], bool]  # returns if the event was launched

    def __init__(self, config, prompter: Prompter):
        FileSystemEventHandler.__init__(self)
        threading.Thread.__init__(self, daemon=True)

        self.config = config
        self.prompter = prompter
        self.observer = Observer()
        self.has_path = False
        self.event_buffer = EventBuffer()
        self._callback = None

    def add_path(self, path):
        self.has_path = True
        self.observer.schedule(self, path, recursive=True)

    @property
    def callback(self):
        raise RuntimeError('Callback is write-only')

    @callback.setter
    def callback(self, fn):
        if not self.has_path:
            raise RuntimeError('Set at least one path before registering a callback')
        self._callback = fn

    def run(self):
        """Watcher's main loop.

        It consumes incoming events in buffer. The events won't be consumed
        if they are too fresh (~10ms).
        """

        if not self._callback:
            raise RuntimeError('Set callback before starting watcher')

        self.observer.start()
        last = datetime.now().timestamp()

        while True:
            for event, timestamp in self.event_buffer.items():
                elapsed = datetime.now().timestamp() - timestamp
                if elapsed <= self.config.event.rate_limit_duration:
                    continue
                elif self.config.event.ignore_events_while_run and timestamp < last:
                    if self.config.log.ignored_events:  # TODO: change to ignored_events
                        self.prompter.ignore("Watcher", "overlapped", event)
                    self.event_buffer.pop(event)
                    continue
                self.event_buffer.pop(event)
                launched = self._callback(event)
                if launched:
                    last = datetime.now().timestamp()
            time.sleep(0.1)

    # -- Impl. of FileSystemEventHandler --

    def on_any_event(self, event):
        """Callback from Observer.

        If there is an identical event in buffer, it's ignored.
        """
        if event in self.event_buffer.events():
            if self.config.log.ignored_events:
                self.prompter.ignore("Watcher", "ratelimit", event)
            return
        if self.config.log.accepted_events:
            self.prompter.accept(event)

        self.event_buffer.push(event)
