from termcolor import cprint


class Prompter:
    def __init__(self, config):
        self.config = config

    def accept(self, event):
        cprint(f"R3BUILD Watcher >> Accept: {event}", "green")

    def ignore(self, name, reason, event):
        name = f'{name:7s}'[:7]
        cprint(f"R3BUILD {name} >> Ignore: ({reason}) {event}", "yellow")

    def launch(self, name, event):
        name = f'{name:7s}'[:7]
        cprint(f"R3BUILD {name} >> Launch: {event}", "green")

    def result(self, name, info, color):
        name = f'{name:7s}'[:7]
        cprint(f"R3BUILD {name} >> {info}", color)
