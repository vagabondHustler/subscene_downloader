import dataclasses
import logging
import threading
from pathlib import Path
from typing import Optional, Type

from subsearch.data import app_paths
from subsearch.utils import io_json


def thread_safe_log(func):
    lock = threading.Lock()

    def wrapper_log(cls, *args, **kwargs):
        with lock:
            return func(cls, *args, **kwargs)

    return wrapper_log


class Logger:
    """
    Singleton logging class
    """
    _instance: Optional["Logger"] = None

    def __init__(self) -> None:
        if hasattr(self, "initialized"):
            return

        self.initialized = True
        debug_log_file = app_paths.appdata_local / "debug.log"
        self.debug_logger = self.create_logger(debug_log_file, "debug")

    def __new__(cls, *args, **kwargs) -> "Logger":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_logger(self, log_file: Path, level: str) -> logging.Logger:
        logger = logging.getLogger(level)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    @classmethod
    @thread_safe_log
    def log(cls, message: str, level: str, print_allowed: bool = True) -> None:
        log_methods = {
            "debug": cls._instance.debug_logger.debug,
            "info": cls._instance.debug_logger.info,
            "warning": cls._instance.debug_logger.warning,
            "error": cls._instance.debug_logger.error,
            "critical": cls._instance.debug_logger.critical,
        }

        log_methods[level](message)
        if print_allowed:
            print(message)


def stdout(message: str, level: str = "debug", **kwargs) -> None:
    print_allowed = kwargs.get("print_allowed", True)
    end_new_line = kwargs.get("new_line", False)
    Logger.log(message, level, print_allowed)
    if end_new_line:
        Logger.log("", level, print_allowed)


def stdout_in_brackets(message: str, **kwargs) -> None:
    stdout(f"--- [{message}] ---", **kwargs)


def stdout_match(provider: str, subtitle_name: str, result: int, threshold: int) -> None:
    if result >= threshold:
        stdout(f"> {provider:<14}{result:>3}% {subtitle_name}")
    else:
        stdout(f"  {provider:<14}{result:>3}% {subtitle_name}")


def stdout_path_action(action_type: str, src: Path, dst: Optional[Path] = None) -> None:
    """
    Logs a message indicating the removal, renaming, moving, or extraction of a file or directory.

    Args:
        action_type (str): A string representing the type of action being performed (e.g. "remove", "rename", "move", "extract").
        src (Path): A Path object representing the file or directory being acted upon.
        dst (Path, optional): An optional Path object representing the new location or name of the file or directory (used for renaming, moving and extracting actions). Defaults to None.

    Returns:
        None
    """
    if src.is_file():
        type_ = "file"
    elif src.is_dir():
        type_ = "directory"
    else:
        return None

    __src = src.relative_to(src.parent.parent) if src else None
    __dst = dst.relative_to(dst.parent.parent) if dst else None

    action_messages = {
        "remove": rf"Removing {type_}: ...\{__src}",
        "rename": rf"Renaming {type_}: ...\{__src} -> ...\{__dst}",
        "move": rf"Moving {type_}: ...\{__src} -> ...\{__dst}",
        "extract": rf"Extracting archive: ...\{__src} -> ...\{__dst}",
    }

    message = action_messages.get(action_type)

    if not message:
        raise ValueError("Invalid action type")

    stdout(message)


def stdout_dataclass(instance: Type[dataclasses.dataclass], **kwargs) -> None:
    if not dataclasses.is_dataclass(instance):
        raise ValueError("Input is not a dataclass instance.")
    stdout_in_brackets(instance.__class__.__name__, **kwargs)
    for field in dataclasses.fields(instance):
        key = field.name
        value = getattr(instance, key)
        padding = " " * (30 - len(key))
        stdout(f"{key}:{padding}{value}", **kwargs)


_logger = Logger()
