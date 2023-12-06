import click


@click.command(name="gif")
@click.option('-o', '--output', 
              help='Output filename')
def make_gif(output):
    pass