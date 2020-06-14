from typing import Dict, List, Union


class AccessValidator:
    _slots: set
    _required: set

    def __init__(self, sec: str, kv: Dict):
        mro = self.__class__.mro()
        if len(mro) > 3:  # Implies it's a subsection
            new_annot = mro[1].__annotations__.copy()
            new_annot.update(self.__annotations__)
            self.__annotations__ = new_annot

        ks = set(kv.keys())
        if hasattr(self, '_required') and not self._required.issubset(ks):
            lacks = self._required - ks
            raise ValueError(f"Section {sec} lacks required keys: {', '.join(lacks)}", )

        for k, v in kv.items():
            setattr(self, k, v)

    def __setattr__(self, name, value):
        if name in self._slots:
            expect = self.__annotations__[name]
            ok = self._type_check(value, expect)
            if not ok:
                raise TypeError(f'Type mismatch: given={type(value)}, expected={expect}')
        elif not name.startswith('__'):
            raise AttributeError(f'Writing to undefined attributes is prohibited')
        object.__setattr__(self, name, value)

    @staticmethod
    def _is_special(typ):
        return getattr(typ, '_special', False)

    @staticmethod
    def _has_origin(typ):
        return hasattr(typ, '__origin__')

    @staticmethod
    def _is_generic(typ):
        return any(typ is t for t in [Dict, List, Union])

    @classmethod
    def _decompose(cls, typ):
        if cls._has_origin(typ):  # At least it's a generic type
            if cls._is_special(typ):  # It's a primitive Dict or List
                return typ.__origin__, None
            return typ.__origin__, typ.__args__
        return typ, None

    @classmethod
    def _type_check(cls, value, expect_typ):
        value_typ = type(value)
        t_origin, t_args = cls._decompose(expect_typ)

        if t_origin != Union and value_typ != t_origin:
            return False  # Completely different

        if not t_args:
            return True  # Origin type and value type are same, and it does not have any recursive type info

        if t_origin == list:
            return all(cls._type_check(v, t_args[0]) for v in value)
        elif t_origin == dict:
            return all(cls._type_check(k, t_args[0]) and cls._type_check(v, t_args[1]) for k, v in value.items())
        elif t_origin == Union:
            return any(cls._type_check(value, t) for t in t_args)
        else:
            raise TypeError(f'Unexpected type(s) for comparison: value_typ={value_typ}, expect_typ={expect_typ}')
