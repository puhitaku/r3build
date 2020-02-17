from __future__ import annotations

import functools
import threading
import time
from datetime import datetime
from typing import Any, Callable, List, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler


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

    observer: Observer
    has_path: bool
    event_buffer: EventBuffer
    verbose: bool
    _callback: Callable[[FileSystemEvent], None]

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.observer = Observer()
        self.has_path = False
        self.event_buffer = EventBuffer()
        self.verbose = False
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

        while True:
            for event, timestamp in self.event_buffer.items():
                elapsed = datetime.now().timestamp() - timestamp
                if elapsed <= 0.01:
                    continue
                self.event_buffer.pop(event)
                self._callback(event)
            time.sleep(0.001)

    # -- Impl. of FileSystemEventHandler --

    def on_any_event(self, event):
        """Callback from Observer.

        If there is an identical event in buffer, it's ignored.
        """
        if event in self.event_buffer.events():
            if self.verbose:
                print(f'Ign event: {event}')
            return
        if self.verbose:
            print(f'Set event: {event}')

        self.event_buffer.push(event)
