#!/usr/bin/env python3
import os
import click

from ._version import __version__ 
from .simulation import universe
from .visualization import dashboard


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, '-V', '--version')
@click.pass_context
def cli(ctx):
    """
    Population dynamics simulator
    """
    pass 


cli.add_command(universe.run_universe)
cli.add_command(dashboard.dashboard)


if __name__ == '__main__':
    cli()