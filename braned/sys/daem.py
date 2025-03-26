import datetime
import json
import signal
import sys
import time
from pathlib import Path

import daemon
import daemon.pidfile

from loguru import logger
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEventHandler

from braned import config
from braned.exceptions import InvalidConfigException
from braned.models import ConfigModel
from braned.models import TargetDirectory


class BraneDaemonController:
    def __init__(self):
        self._observer: BaseObserver | None = None

        self.user_config_last_modified: datetime.datetime | None = None
        # self.user_config_path: str = config.DEFAULT_CONFIG_PATH
        self.user_config_path = (
            "/Users/shel/Documents/brane/braned/config.json"
            # TODO config.DEFAULT_CONFIG_PATH
        )
        self.user_config: ConfigModel | None = None

    def run(self):
        # load the config
        self.reload_config()

        # create and launch the observer thread
        self._observer = create_observer(self.user_config)

        try:
            self._observer.start()
            logger.info("Started observer")
        except Exception as e:
            logger.error(f"Error starting observer: {e}")

        # enter the main loop
        try:
            logger.info("Daemon running")
            while True:
                self.survey_config()
                time.sleep(5)
        except Exception as e:
            logger.error(f"Observer stopped: {e}")

        self._observer.join()

    def survey_config(self):
        """Check if the config file has been modified and attempt to reload it if so."""
        # verify config file still exists
        if not Path(self.user_config_path).exists():
            logger.error(f"Config file not found at {self.user_config_path}")
            raise InvalidConfigException(
                f"Config file not found at {self.user_config_path}"
            )

        # check if config file has been modified
        if Path(self.user_config_path).stat().st_mtime > self.user_config_last_modified:
            # config has updated, reload it
            self.reload_config()
            reset_observer_handlers(self._observer, self.user_config.target_directories)

    def reload_config(self):
        """Reload the config model, observer, and update the stored last modified time.

        Raises:
            InvalidConfigException: If the config file is missing or cannot be parsed.
        """
        try:
            with open(self.user_config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise InvalidConfigException(f"Error loading config: {e}") from e

        try:
            new_config_model = ConfigModel(**config_data)
        except Exception as e:
            logger.error(f"Error parsing config: {e}")
            raise InvalidConfigException(f"Error parsing config: {e}") from e

        self.user_config_last_modified = Path(self.user_config_path).stat().st_mtime
        self.user_config = new_config_model

    def _shutdown(self):
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()

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


def create_observer(config_model: ConfigModel) -> BaseObserver:
    try:
        observer = Observer()

    except Exception as e:
        logger.error(f"Error starting observer: {e}")

    reset_observer_handlers(observer, config_model.target_directories)

    return observer


def reset_observer_handlers(
    observer: BaseObserver,
    target_directories: list[TargetDirectory],
) -> list[BraneDaemonLocalSyncHandler]:
    # Remove all existing handlers
    observer.unschedule_all()

    # Create new handlers
    # TODO should there be a loading operation to populate vector_store?
    handlers = [BraneDaemonLocalSyncHandler(d.path) for d in target_directories]

    # Add new handlers to the observer
    try:
        for handler in handlers:
            observer.schedule(
                event_handler=handler,
                path=handler.source_dir,
                recursive=True,
            )

        logger.info(f"Monitoring directories: {[d.path for d in target_directories]}")

    except Exception as e:
        logger.error(f"Error adding handlers to observer: {e}")

    return handlers


def start_brane_daemon():
    braned_controller = BraneDaemonController()

    context = daemon.DaemonContext(
        umask=0o002,
        pidfile=daemon.pidfile.PIDLockFile(config.DEFAULT_PID_FILE),
        stdout=open(config.log_file_path, "w", encoding="utf-8"),
        stderr=open(config.log_file_path, "w", encoding="utf-8"),
        signal_map={
            signal.SIGTERM: braned_controller._shutdown,  # type: ignore
            signal.SIGINT: braned_controller._shutdown,  # type: ignore
        },
    )

    with context:
        braned_controller.run()
