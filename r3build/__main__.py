#!/usr/bin/env python3
import time
import click
from r3build.cli import R3build
from r3build.processor import available_processors


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
@click.option('--processors', is_flag=True)
def main(config, verbose, processors):
    if processors:
        print('Available Processor ID (a.k.a. job type):')
        print(''.join(f'* {i}\n' for i in available_processors.keys() if i != 'internaltest'))
        return

    r3 = R3build(config_fn=config, verbose=verbose)
    r3.run()

    try:
        time.sleep(999999)
    except KeyboardInterrupt:
        return


main()
