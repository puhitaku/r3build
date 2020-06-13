import pytest

from r3build.config_class import Processor, ProcMake


def test_simple_validation():
    with pytest.raises(ValueError):
        p = Processor('', {})

    p = Processor('', {'processor': ''})

    p.processor = 'foo'
    assert p.processor == 'foo'

    with pytest.raises(TypeError):
        p.processor = 1


def test_recursive_validation():
    p = Processor('proc', {'processor': ''})

    # Union[List[str], str]
    p.when = ['foo']
    p.when = 'foo'

    with pytest.raises(TypeError):
        p.when = [1]

    with pytest.raises(TypeError):
        p.when = 1

    m = ProcMake('make', {'processor': 'make'})

    # Dict[str, str]
    m.environment = {'foo': '1'}

    with pytest.raises(TypeError):
        m.environment = {0xf00: '1'}

    with pytest.raises(TypeError):
        m.environment = 'I AM A DICT!!!!!'


def test_access_control():
    p = Processor('', {'processor': ''})

    with pytest.raises(AttributeError):
        p.unknown = 3939
