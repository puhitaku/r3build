from __future__ import annotations

import functools
import threading
import time
from datetime import datetime
from typing import Any, Callable, List, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler


class EventBuffer:
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
    observer: Observer
    has_path: bool
    callback: Callable[[FileSystemEvent], None]
    event_buffer: EventBuffer
    verbose: bool

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        self.observer = Observer()
        self.has_path = False
        self.callback = None
        self.event_buffer = EventBuffer()
        self.verbose = False

    @functools.lru_cache(maxsize=None)
    def add_path(self, path):
        self.has_path = True
        self.observer.schedule(self, path, recursive=True)

    def set_callback(self, fn):
        if not self.has_path:
            raise RuntimeError('Set at least one path before registering a callback')
        self.callback = fn

    def run(self):
        self.observer.start()

        while True:
            self._run()
            time.sleep(0.001)

    def _run(self):
        for event, timestamp in self.event_buffer.items():
            elapsed = datetime.now().timestamp() - timestamp
            if elapsed >= 0.01:
                self.event_buffer.pop(event)
                if self.callback:
                    self.callback(event)

    def on_any_event(self, event):
        if event in self.event_buffer.events():
            if self.verbose:
                print(f'Ign event: {event}')
            return
        if self.verbose:
            print(f'Set event: {event}')

        self.event_buffer.push(event)
