#!/usr/bin/env python3
import time
import click
from r3build.cli import R3build


class ConfigOption(click.types.StringParamType):
    name = 'config'


@click.command()
@click.option(
    '-c',
    '--config',
    default='r3build.toml',
    help='Configuration file. (default = r3build.toml)',
    type=ConfigOption(),
)
@click.option('-v', '--verbose', is_flag=True)
def main(config, verbose):
    r3 = R3build(config_fn=config, verbose=verbose)
    r3.run()

    try:
        time.sleep(999999)
    except KeyboardInterrupt:
        return


main()
