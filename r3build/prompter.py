from termcolor import cprint


class Prompter:
    def __init__(self, config):
        self.config = config

    @staticmethod
    def ellipsify(text, length=10):
        if len(text) > length:
            return text[:length-3] + "..."
        return text + ' ' * (length - len(text))

    def accept(self, event):
        cprint(f"R3BUILD Watcher    >> Accept: {event}", "cyan")

    def ignore(self, name, reason, event):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> Ignore: ({reason}) {event}", "yellow")

    def launch(self, name, event):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> Launch: {event}", "green")

    def result(self, name, info, color):
        name = self.ellipsify(name)
        cprint(f"R3BUILD {name} >> {info}", color)
