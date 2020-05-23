from dataclasses import asdict, dataclass
from pprint import saferepr
from typing import Any, Dict, List, Union  # necessary for eval
from textwrap import indent

import black
import click
import tomlkit as tk
import tomlkit.items
from black import FileMode, TargetVersion


class Literalify:
    """Wrapper to replace repr and str.

    Before:
        >>> repr(int)
        <class 'int'>
        >>> repr(Union[int])
        <class 'int'>
        >>> repr(Union[int, str])
        typing.Union[int, str]

    After:
        >>> repr(Literalify(int))
        int
        >>> repr(Literalify(Union[int]))
        int
        >>> repr(Literalify(Union[int, str]))
        Union[int, str]
    """

    typ: type

    def __init__(self, typ):
        self.typ = typ
        self.__qualname__ = self.__repr__()
        self.__module__ = self.typ.__module__

    def __call__(self, *args, **kwargs):
        # dummy to spoof typing.py
        pass

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.__module__ + self.__qualname__)

    def __repr__(self):
        if self.typ.__module__ == 'builtins':
            return self.typ.__qualname__
        elif self.typ.__module__ == 'typing':
            return self.typ.__repr__().replace('typing.', '')
        else:
            return self.typ.__repr__()

    def __str__(self):
        return self.__repr__()


@dataclass
class Item:
    required: bool
    type: type
    default: Any
    description: str

    def __repr__(self):
        return str(asdict(self))


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('f', metavar='TOML', type=click.File('r'))
def skel(f):
    def2skel(tk.loads(f.read()))


@cmd.command()
@click.argument('f', metavar='TOML', type=click.File('r'))
def model(f):
    def2model(tk.loads(f.read()))


def def2skel(de):
    sections = {section: parse_section(de[section]) for section in ['log', 'event']}
    processors = {name: parse_section(processor) for name, processor in de['target'].items()}

    def add_mlc(s, blank=True):
        for c in s.strip().split('\n'):
            doc.add(tk.comment(c))
        if blank:
            doc.add(br)

    br, br2 = tk.ws('\n'), tk.ws('\n\n')

    doc = tk.document()
    doc.add(tk.comment('This file shows the skeleton of r3build.toml.'))
    doc.add(tk.comment('It is structured with a bunch of sections that contain multiple keys and values.'))
    doc.add(br)
    doc.add(tk.comment('Values in this file are the default value of corresponding keys.'))
    doc.add(br)


    for name, props in sections.items():
        exs = []

        for key, value in [(t[0], t[1]) for t in props.items() if not t[0].startswith('__')]:
            vex = f'{key} ({repr(value.type)}) {" *REQUIRED " if value.required else ""}\n'
            vex += f'{indent(value.description, "#  - ")}\n#'
            exs.append(vex)
        exs[-1] = exs[-1][:-2] + '\n'

        comment = '\n# ' + props["__description__"].replace('\n', '\n# ') + '\n\n# ' + '\n# '.join(exs)
        trivia = tk.items.Trivia(comment_ws=" ", comment=comment)

        if name == 'target':
            section = tk.api.AoT([])
            table = tk.api.Table(tk.api.Container(), trivia, False)
            for key, value in [(t[0], t[1]) for t in props.items() if not t[0].startswith('__')]:
                table.add(key, value.default)
            section.append(table)
        else:
            section = tk.api.Table(tk.api.Container(), trivia, False)
            for key, value in [(t[0], t[1]) for t in props.items() if not t[0].startswith('__')]:
                section.add(key, value.default)


        doc.add(name, section)
        doc.add(br)

    for name, props in processors.items():
        exs = []
        for key, value in [(t[0], t[1]) for t in props.items() if not t[0].startswith('__')]:
            vex = f'{key} ({repr(value.type)}) {" *REQUIRED* " if value.required else ""}\n'
            vex += f'{indent(value.description, "#  - ")}\n#'
            exs.append(vex)
        exs[-1] = exs[-1][:-2] + '\n'

        if name == 'common':
            comment = '\n# ' + props["__description__"].replace('\n', '\n# ') + '\n\n# ' + '\n# '.join(exs)
        else:
            comment = f' # Properties specific to `{name}` processor\n'
            comment += '# ' + props["__description__"].replace('\n', '\n# ') + '\n\n# ' + '\n# '.join(exs)

        trivia = tk.items.Trivia(comment_ws=" ", comment=comment, indent='\n\n')
        table = tk.api.Table(tk.api.Container(), trivia, False)

        for key, value in [(t[0], t[1]) for t in props.items() if not t[0].startswith('__')]:
            table.add(key, value.default)

        section = tk.api.AoT([])
        section.append(table)

        doc.add('target', section)

    print(tk.dumps(doc).strip())


def2model_template = '''
from typing import Dict, List, Union


sections = {sections}


processors = {processors}
'''


def def2model(de):
    sections = {section: parse_section(de[section]) for section in ['log', 'event']}
    processors = {name: parse_section(processor) for name, processor in de['target'].items()}

    mode = FileMode(
        target_versions={TargetVersion.PY36},
        string_normalization=False,
    )

    sections_f = black.format_str(saferepr(sections), mode=mode)
    processors_f = black.format_str(saferepr(processors), mode=mode)

    print(def2model_template.format(sections=sections_f, processors=processors_f))


def parse_section(section: dict):
    # Workaround not to use pop()
    section_typ = Literalify(eval(section['type']))
    del section['type']
    section_description = section['description'].strip()
    del section['description']

    out = {
        '__type__': section_typ,
        '__description__': section_description,
    }

    for key, spec in section.items():
        out[key] = Item(
            required=spec.get('required', False),
            type=Literalify(eval(spec['type'])),
            default=spec['default'],
            description=spec['description'].strip(),
        )

    return out


if __name__ == '__main__':
    cmd()
