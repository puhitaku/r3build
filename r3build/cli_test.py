from r3build.cli import R3build


def test_load_jobs():
    d = {
        'job': [{'name': 'foo', 'type': 'internaltest',},],
    }
    r3 = R3build(config_dict=d)
    assert r3.get_job('foo') is not None
    assert r3.get_job('foo').name == 'foo'
    assert r3.get_job('foo').processor.id == 'internaltest'
