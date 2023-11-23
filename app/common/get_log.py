import logging


def get_logger(mod_name: str) -> logging.Logger:
    """Return logger object."""
    format = "%(asctime)s: %(name)s: %(levelname)s: %(message)s"
    logger = logging.getLogger(mod_name)
    # Writes to stdout
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(format))
    logger.addHandler(ch)
    return logger
