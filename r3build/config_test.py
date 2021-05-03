import pytest

from r3build.config_class import Processor, MakeProcessorConfig


def test_simple_validation():
    with pytest.raises(ValueError):
        p = Processor('', {})

    p = Processor('', {'type': ''})

    p.type = 'foo'
    assert p.type == 'foo'

    with pytest.raises(TypeError):
        p.type = 1


def test_recursive_validation():
    p = Processor('proc', {'type': ''})

    # Union[List[str], str]
    p.when = ['foo']
    p.when = 'foo'

    with pytest.raises(TypeError):
        p.when = [1]

    with pytest.raises(TypeError):
        p.when = 1

    m = MakeProcessorConfig('make', {'type': 'make'})

    # Dict[str, str]
    m.environment = {'foo': '1'}

    with pytest.raises(TypeError):
        m.environment = {0xF00: '1'}

    with pytest.raises(TypeError):
        m.environment = 'I AM A DICT!!!!!'


def test_access_control():
    p = Processor('', {'type': ''})

    with pytest.raises(AttributeError):
        p.unknown = 3939
