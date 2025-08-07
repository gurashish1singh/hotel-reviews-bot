from __future__ import annotations

import logging
import logging.config

from yaml import safe_load


def set_logging(config_file: str = "logging.yaml", log_level: int | str = logging.DEBUG) -> None:
    try:
        with open(config_file, "rt") as f:
            config = safe_load(f.read())
            logging.config.dictConfig(config)
    except Exception as err:
        print(f"Error occurred while creating logger from {config_file=}.\nERROR: {err}")
        print("Falling back to basic logging configuration")
        logging.basicConfig(level=log_level)
