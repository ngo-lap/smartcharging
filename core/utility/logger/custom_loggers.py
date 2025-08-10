import logging


def setup_logger(name: str) -> logging.Logger:
    """
        Creates a logger with the given name. Quick Results from ChatGPT
        Example usage:
            logger = setup_logger(__name__)

    :param name:
    :return: Logger
    """

    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add handler to the logger
        logger.addHandler(ch)

    return logger
