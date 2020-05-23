import sys
from dataclasses import asdict, dataclass
from pprint import saferepr
from typing import Any, Dict, List, Union
from textwrap import indent, dedent

import black
import tomlkit
from black import format_str, FileMode, TargetVersion


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


template = '''
from typing import Dict, List, Union


sections = {sections}


processors = {processors}
'''


def main():
    if not sys.argv[-1].endswith('.toml'):
        print('Usage: defconv <def_toml>')
        sys.exit(1)

    with open(sys.argv[-1]) as f:
        de = tomlkit.loads(f.read())

    sections = {section: parse_section(de[section]) for section in ['log', 'event', 'target']}
    processors = {name: parse_section(processor) for name, processor in de['processor'].items()}

    mode = FileMode(
        target_versions={TargetVersion.PY36},
        string_normalization=False,
    )

    sections_f = black.format_str(saferepr(sections), mode=mode)
    processors_f = black.format_str(saferepr(processors), mode=mode)

    print(template.format(sections=sections_f, processors=processors_f))


def parse_section(section: dict):
    # Workaround not to use pop()
    section_typ = Literalify(eval(section['type']))
    del section['type']
    section_description = section['description']
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
    main()
