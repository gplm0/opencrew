import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.group()
def cli():
    """🤖 Jarvis AI Assistant - CLI Interface"""
    pass


if __name__ == "__main__":
    cli()
