import sqlite3
import sqlite_vec
from loguru import logger


def initialize_local_sqlite_vec_db(path: str = "local.db"):
    db = sqlite3.connect(path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    (vec_version,) = db.execute("SELECT vec_version()").fetchone()

    logger.debug(f"sqlite-vec version: {vec_version}")
