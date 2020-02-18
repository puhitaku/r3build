from r3build.cli import R3build


def test_load_rules():
    d = {
        'rule': [{'name': 'foo', 'processor': '_test',},],
    }
    r3 = R3build(config_dict=d)
    assert r3.get_rule('foo') is not None
    assert r3.get_rule('foo').name == 'foo'
    assert r3.get_rule('foo').processor.id == '_test'
