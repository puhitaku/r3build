from r3build.cli import R3build


def test_load_targets():
    d = {
        'target': [{'name': 'foo', 'processor': '_test',},],
    }
    r3 = R3build(config_dict=d)
    assert r3.get_target('foo') is not None
    assert r3.get_target('foo').name == 'foo'
    assert r3.get_target('foo').processor.id == '_test'
