from enum import Enum

from typing_extensions import Self

from fds.utils.log import log_and_raise


class EnumFromInput(str, Enum):
    @classmethod
    def from_input(cls, value: str | Self):
        if isinstance(value, cls):
            return value
        elif isinstance(value, str):
            return cls(value)
        else:
            msg = f"Invalid input {value} for {cls.__name__}"
            log_and_raise(ValueError, msg)
