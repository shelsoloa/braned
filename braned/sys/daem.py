import signal
import sys
import time
from pathlib import Path

import daemon
import daemon.pidfile

from loguru import logger
from watchdog.observers import Observer
from watchdog.observers import ObserverType
from watchdog.events import FileSystemEventHandler

from braned import config


class BraneDaemonController:
    def __init__(self):
        self.observer = None

    @classmethod
    def start_brane_daemon(cls):
        brane_controller = cls()

        context = daemon.DaemonContext(
            umask=0o002,
            pidfile=daemon.pidfile.PIDLockFile(config.DEFAULT_PID_FILE),
            stdout=open(config.DEFAULT_LOG_FILE, "w", encoding="utf-8"),
            stderr=open(config.DEFAULT_LOG_FILE, "w", encoding="utf-8"),
            signal_map={
                signal.SIGTERM: brane_controller._shutdown,
                signal.SIGINT: brane_controller._shutdown,
            },
        )

        with context:
            brane_controller.run()

    def run(self):
        # create and launch the observer thread
        self.observer = _create_observer()

        try:
            self.observer.start()
            logger.info("Started observer")
        except Exception as e:
            logger.error(f"Error starting observer: {e}")

        # enter the main loop
        try:
            while True:
                logger.info("Daemon running")
                time.sleep(1)
        except Exception as e:
            logger.error(f"Observer stopped: {e}")

        self.observer.join()

    def _shutdown(self):
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()

        logger.info("Daemon stopping...")
        sys.exit(0)


class BraneDaemonLocalSyncHandler(FileSystemEventHandler):
    def __init__(self, source_dir: str):
        self.source_dir = source_dir

    def on_created(self, event):
        if not event.is_directory:
            self.on_modified(event)

    def on_modified(self, event):
        if not event.is_directory:
            try:
                file_path = Path(event.src_path)
                relative_path = file_path.relative_to(self.source_dir)
                logger.info(f"Detected change in file: {relative_path}")

                # TODO perform the sync

            except Exception as e:
                logger.error(f"Error syncing file {file_path}: {str(e)}")


def _create_observer() -> ObserverType:
    # TODO load from config
    target_folders = [
        "/Users/shel/Documents/brane/braned/data",
    ]
    handlers = [BraneDaemonLocalSyncHandler(folder) for folder in target_folders]

    try:
        observer = Observer()
        for handler in handlers:
            observer.schedule(
                event_handler=handler,
                path=handler.source_dir,
                recursive=True,
            )

        logger.info(f"Started monitoring target folders: {target_folders}")

    except Exception as e:
        logger.error(f"Error starting observer: {e}")

    return observer
