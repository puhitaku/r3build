from watchdog.events import FileSystemEvent
from termcolor import cprint


class Prompter:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def ellipsify(text, length=10):
        if len(text) > length:
            return text[:length-3] + "..."
        return text + ' ' * (length - len(text))

    def accept(self, event: FileSystemEvent):
        cprint(f"R3BUILD Watcher    >> Accept: '{event.event_type}' event on {event.src_path}", "cyan")

    def ignore(self, name, reason, event: FileSystemEvent):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> Ignore: ({reason}) '{event.event_type}' event on {event.src_path}", "yellow")

    def trigger(self, name, event: FileSystemEvent):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> Detected '{event.event_type}' event on {event.src_path}", "green")

    def result(self, name, info, color):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> {info}", color)

    def procsay(self, name, mes):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> {mes}", "green")

    def procerr(self, name, mes):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> {mes}", "red")
