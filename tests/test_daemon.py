import os

import daemon
import daemon.pidfile


def test_start_daemon():
    context = daemon.DaemonContext(
        pidfile=daemon.pidfile.PIDLockFile("/var/run/braned.test.pid")
    )

    with context:
        # assert that the pid file exists
        assert os.path.exists("/var/run/braned.test.pid")

    # assert that the pid file does not exist
    assert not os.path.exists("/var/run/braned.test.pid")
