import click
import os
from .game import ChessGame

# Change environment variables for Click commands to work
# os.environ['LC_ALL'] = 'en_US.utf-8'
# os.environ['LANG'] = 'en_US.utf-8'


@click.command()
def cli():
    """Play a game of chess against the engine."""
    try:
        ChessGame()
    except Exception as error:
        click.echo(error)


if __name__ == "__main__":
    cli()
    # Revert environment variables back
    # os.unsetenv('LC_ALL')
    # os.unsetenv('LANG')
