#!/usr/bin/env python

import argparse
import logging
from pathlib import Path

from common import get_logger
from container import Container

# This is a shim for splitting files on chapter indices.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--filename", type=Path, help="An MKV to process", required=True
    )
    parser.add_argument(
        "indices", type=int, nargs="+", help="The chapter indices to process"
    )
    parser.add_argument("--debug", action="store_true", help="Turn on debug messages.")

    logger = get_logger("RIP")
    logger.setLevel(logging.INFO)

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if not args.filename:
        raise FileNotFoundError("The given file was not found!")

    c = Container(args.filename)
    c.split(chapter_indices=args.indices)
