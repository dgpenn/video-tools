#!/usr/bin/env python3

import logging
import shutil
import subprocess
from collections.abc import Generator
from pathlib import Path


class GeneratorExit:
    """Wrapper class to simplify using generator functions with a return code."""

    def __init__(self, generator):
        self.generator = generator

    def __iter__(self):
        self.code: int = yield from self.generator
        return self.code


def get_logger(name: str) -> logging.Logger:
    """This function returns a common console logger using the given name."""

    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)-8s - %(threadName)s - %(message)s",
            datefmt="%x - %X",
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


def check_command(command: str) -> Path:
    """This function returns a Path object for the location of the given command.

    A FileNotFoundError will be raised if the command executable was not found.
    """
    command = shutil.which(command)
    if not command:
        raise FileNotFoundError("The {} command was not found in PATH!".format(command))
    return Path(command)


def run_command(command: list[str]) -> Generator[str, None, int]:
    """Run an arbitrary command and yield output. The process return code is returned."""
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ) as remote:
        for line in iter(remote.stdout.readline, ""):
            yield line
        remote.stdout.close()
        return remote.wait()
