import click

from loguru import logger

from braned.sys.daem import BraneDaemonController


@click.group()
def cli():
    pass


@cli.command()
def start():
    logger.info("Starting braned")
    BraneDaemonController.start_brane_daemon()


@cli.command()
def stop():
    # handled by systemd
    pass
