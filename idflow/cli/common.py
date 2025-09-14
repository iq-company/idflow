"""Common utilities for CLI modules."""

import click
import typer


def help_callback(ctx: click.Context, param: click.Parameter, value: bool):
    """Standard help callback for -h alias support across all CLI apps."""
    if value:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def add_help_option(help_text: str = "Show this message and exit."):
    """Create a help option with -h alias."""
    return typer.Option(False, "-h", "--help", callback=help_callback, is_eager=True, help=help_text)
