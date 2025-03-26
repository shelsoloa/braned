import click

from loguru import logger

from braned.sys.daem import start_brane_daemon


@click.group()
def cli():
    pass


@cli.command()
def start():
    logger.info("Starting braned")
    start_brane_daemon()


@cli.command()
def stop():
    # handled by systemd
    pass
