from r3build import cli

def test_load_rules():
    r1 = {
        'name': 'foo',
        'processor': '_test',
        'key': 'value',
    }
    parsed = cli.load_rules([r1], False)
    assert parsed[0].get('name') == 'foo'
    assert parsed[0].tid == '_test'
    assert parsed[0].get('key') == 'value'

