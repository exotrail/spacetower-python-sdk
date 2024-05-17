from typing import NoReturn, Type

from loguru import logger


def log_and_raise(exception_type: Type[BaseException], message: str = "") -> NoReturn:
    """
    Raise an exception with a message and log it.

    Args:
        exception_type (Exception): The exception to be raised.
        message (str): The message to be logged and raised. Defaults to "".

    Raises:
        exception_type: The exception to be raised.
    """
    logger.error(message)
    raise exception_type(message)
