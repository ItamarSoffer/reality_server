import logging
import os
from datetime import datetime


def create_log(log_dir_path=None, logging_level=logging.INFO):
    """
    General logger
    Prints to console and file.
    :param log_dir_path:
    :param logging_level:
    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(logging_level)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %I:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # UNCOMMENT THE FOLLOWING LINES TO ADD A FILE LOGGER. ADD log_dir_path AS

    if log_dir_path is not None:
        create_dir(log_dir_path)
        file_handler = logging.FileHandler(
            os.path.join(log_dir_path, datetime.today().strftime("%y%m%d") + ".log")
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
