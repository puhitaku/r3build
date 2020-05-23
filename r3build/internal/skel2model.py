import re
import sys
from pprint import pprint, saferepr
from typing import Dict, List, Union

import toml


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


def main():
    if len(sys.argv) < 2:
        print('Usage: skel2model <skeleton>')
        sys.exit(-1)

    with open(sys.argv[-1]) as f:
        raw = toml.load(f)

    tree = dig(raw, '')
    # pprint(tree)
    print(saferepr(tree))


def inspect_type(obj) -> type:
    if not isinstance(obj, type):
        obj = type(obj)

    mro = obj.mro()
    if dict in mro:
        return Literalify(dict)
    else:
        return Literalify(obj)


def dig(obj, ancestor_key):
    if isinstance(obj, dict):
        kt = Union[tuple(inspect_type(v) for v in obj.keys()) or tuple([str])]
        vt = Union[tuple(inspect_type(v) for v in obj.values()) or tuple([str])]
        kt, vt = Literalify(kt), Literalify(vt)

        d = dict()
        if ancestor_key == 'target':
            if 'processor' not in obj:
                raise ValueError("Target definition must have processor key")
            d = {'__processor__': obj['processor']}

        d.update(
            {
                '__type__': Literalify(Dict[kt, vt]),
                '__value__': {k: dig(v, k) for k, v in obj.items() if k != 'processor'},
            }
        )
        return d
    elif isinstance(obj, list):
        t = Union[tuple(inspect_type(v) for v in obj)]
        t = Literalify(t)
        return {
            '__type__': Literalify(List[t]),
            '__value__': [dig(v, ancestor_key) for v in obj],
        }
    else:
        return {
            '__type__': inspect_type(obj),
            '__value__': obj,
        }


if __name__ == '__main__':
    main()
