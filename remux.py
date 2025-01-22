#!/usr/bin/env python

import argparse
import logging
from pathlib import Path

from common import get_logger
from container import Container, StreamData

# This is a shim for remuxing files that have been processed previously without remuxing.

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", type=Path, help="An MKV to process")
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        help="A directory to search for MKVs to process. This is recursive.",
    )
    remux_group = parser.add_mutually_exclusive_group(required=False)
    remux_group.add_argument(
        "--remux-english",
        action="store_true",
        help="Remux videos to include only English audio and subtitles. Subtitles will not be enabled by default.",
    )
    remux_group.add_argument(
        "--remux-japanese",
        action="store_true",
        help="Remux videos to include only Japanese audio and subtitles. Subtitles will not be enabled by default.",
    )
    remux_group.add_argument(
        "--remux-subs",
        action="store_true",
        help="Remux videos to include only English and Japanese audio and subtitles. Japanese audio will be preferred while Enlgish subtitles will be set as default.",
    )
    remux_group.add_argument(
        "--remux-dubs",
        action="store_true",
        help="Remux videos to include only English and Japanese audio and subtitles. English audio will be preferred while subtitles will not be enabled by default.",
    )
    parser.add_argument("--debug", action="store_true", help="Turn on debug messages.")

    logger = get_logger("RIP")
    logger.setLevel(logging.INFO)

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    files = []

    if args.filename:
        if args.filename.is_file():
            files += [args.filename]

    if args.directory:
        for _file in args.directory.rglob("*.mkv", case_sensitive=False):
            if _file.is_file():
                files += [_file]

    for _file in files:
        c = Container(_file)
        if args.remux_english:
            c.remux_by_language(
                audio_languages=[StreamData.LANG_ENG],
                subtitle_languages=[StreamData.LANG_ENG],
            )
            c.clear_default_audio()
            c.set_preferred_audio_by_language(
                StreamData.LANG_ENG, default_required=True
            )
            c.clear_default_subtitles()
        elif args.remux_japanese:
            c.remux_by_language(
                audio_languages=[StreamData.LANG_JPN],
                subtitle_languages=[StreamData.LANG_JPN],
            )
            c.clear_default_audio()
            c.set_preferred_audio_by_language(
                StreamData.LANG_JPN, default_required=True
            )
            c.clear_default_subtitles()
        elif args.remux_dubs:
            c.remux_by_language(
                audio_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                subtitle_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
            )
            c.clear_default_audio()
            c.set_preferred_audio_by_language(
                StreamData.LANG_ENG, default_required=True
            )
            c.clear_default_subtitles()
        elif args.remux_subs:
            c.remux_by_language(
                audio_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                subtitle_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
            )
            c.clear_default_audio()
            c.set_preferred_audio_by_language(
                StreamData.LANG_JPN, default_required=True
            )
            c.clear_default_subtitles()
            c.set_preferred_subtitles_by_language(StreamData.LANG_ENG)
