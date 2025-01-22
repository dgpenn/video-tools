#!/usr/bin/env python3

import argparse
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import ClassVar

from common import GeneratorExit, check_command, get_logger, run_command
from container import Container, StreamData
from disc import Disc
from makemkv import MakeMKVMessage, MakeMKVParser


class Ripper:
    """This class acts as a frontend to other commands for media extraction and basic post-processing."""

    VIDEO_GENERIC: ClassVar[str] = "VIDEO"
    VIDEO_MOVIE: ClassVar[str] = "MOVIE"
    VIDEO_SHOW: ClassVar[str] = "SHOW"

    REMUX_NONE: ClassVar[str] = "REMUX_NONE"
    REMUX_ENGLISH_ONLY: ClassVar[str] = "REMUX_ENGLISH_ONLY"
    REMUX_JAPANESE_ONLY: ClassVar[str] = "REMUX_JAPANESE_ONLY"
    REMUX_ANIME_SUBS: ClassVar[str] = "REMUX_ANIME_SUBS"
    REMUX_ANIME_DUBS: ClassVar[str] = "REMUX_ANIME_DUBS"

    ID: ClassVar[int] = 0

    def __init__(
        self,
        filename: Path,
        root_directory: Path,
        minimum_duration: int = 0,
        maximum_duration: int = 999999,
        media_type: str = VIDEO_GENERIC,
        title: str = "",
        season: int | None = None,
        year: int | None = None,
        eject: bool = True,
        remux_profile: str = REMUX_NONE,
    ):
        Ripper.ID += 1
        self.id = Ripper.ID

        if not title:
            raise ValueError("The media title has not been set!")

        if not root_directory.exists():
            raise FileNotFoundError("The root directory was not found!")

        if type(season) is int:
            if season < 0:
                raise ValueError("The season is less than zero!")

        if media_type not in [
            Ripper.VIDEO_GENERIC,
            Ripper.VIDEO_MOVIE,
            Ripper.VIDEO_SHOW,
        ]:
            raise ValueError("The media type was not recognized!")

        if minimum_duration >= maximum_duration:
            raise ValueError("Maximum duration must be greater than minimum!")

        self.logger: logging.Logger = get_logger("RIP")
        self.raw_filename: Path = filename.absolute()
        self.disc: Disc = Disc(self.raw_filename)

        # This is the Show or Movie Name
        self.title = title.strip()

        # This is the number of titles that should actually be extracted and processed during rip
        # I.e. The duration limits and any other logic have been processed before this is set.
        self.title_count: int = -1

        # The literal season number. 0 means "specials".
        self.season: int = season

        # This is the air year
        self.year: int = year

        # This is the literal root directory where other directories are placed.
        # This is expected to be an existing directory.
        self.root_directory: Path = root_directory

        # These are the media duration limits in seconds.
        self.minimum_duration: int = minimum_duration
        self.maximum_duration: int = maximum_duration

        # This is set after the run_command calls. It should be the last external command exit code.
        self.last_run_code: int = -1

        # The rip function will call _eject if this is set and last_run_code == 0
        self.eject_on_rip: bool = eject

        # This will control how videos are remuxed (including not remuxing).
        self.remux_profile = remux_profile

        # This must be one of VIDEO_GENERIC, VIDEO_MOVIE, VIDEO_SHOW
        self.media_type: str = media_type

        # These extensions are the only extensions considered valid.
        self.extensions: list[str] = [".mkv"]

        # If movie and feature_only, skip everything with duration < (movie_minimum * longest title) during rip.
        self.movie_minimum: float = 0.9
        self.feature_only = True

        # Setup media directory but don't create the directory.
        # This should be a directory named after the show, movie, etc.
        media_name = "{}".format(self.title)
        if self.year:
            media_name += " ({})".format(self.year)
        self.media_directory: Path = self.root_directory.joinpath(
            "{}".format(media_name)
        )

        # Setup videos directory but don't create the directory.
        # This may be named similarly to "ripper1". It's wherever the MKV files are written to initially.
        # Note that there are potential naming conflicts with this directory and contained files
        self.videos_directory = self.media_directory.joinpath(self.raw_filename.stem)

    def _process_video_remux(
        self,
        filename: Path,
        audio_languages: list[str],
        subtitle_languages: list[str],
        preferred_audio_language: str,
        preferred_subtitle_language: str,
    ):
        """Remux video to remove unwanted streams.

        The audio and subtitle languages streams will be kept.
        All other streams will be removed.
        Any prefered languages will set a corresponding stream as default, if available.
        """
        c = Container(filename)
        self.logger.debug(
            "Filtering audio streams to {}".format(
                "{}".format(" ".join(audio_languages))
            )
        )
        self.logger.debug(
            "Filtering subtitle streams to {}".format(" ".join(subtitle_languages))
        )
        c.remux_by_language(audio_languages, subtitle_languages)

        self.logger.debug(
            "Setting default audio to {}".format(preferred_audio_language)
        )
        c.set_preferred_audio_by_language(preferred_audio_language)

        if preferred_subtitle_language:
            self.logger.debug(
                "Setting default subtitles to {}".format(preferred_subtitle_language)
            )
            c.set_preferred_subtitles_by_language(preferred_subtitle_language)
        else:
            c.clear_default_subtitles()

    def _process_video_remux_profile(self, filename: Path):
        """This function calls _process_video_remux based upon the instance's remux_profile."""
        match self.remux_profile:
            case Ripper.REMUX_ENGLISH_ONLY:
                self._process_video_remux(
                    filename=filename,
                    audio_languages=[StreamData.LANG_ENG],
                    subtitle_languages=[StreamData.LANG_ENG],
                    preferred_audio_language=StreamData.LANG_ENG,
                    preferred_subtitle_language="",
                )
            case Ripper.REMUX_JAPANESE_ONLY:
                self._process_video_remux(
                    filename=filename,
                    audio_languages=[StreamData.LANG_JPN],
                    subtitle_languages=[StreamData.LANG_JPN],
                    preferred_audio_language=StreamData.LANG_JPN,
                    preferred_subtitle_language="",
                )
            case Ripper.REMUX_ANIME_DUBS:
                self._process_video_remux(
                    filename=filename,
                    audio_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                    subtitle_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                    preferred_audio_language=StreamData.LANG_ENG,
                    preferred_subtitle_language="",
                )
            case Ripper.REMUX_ANIME_SUBS:
                self._process_video_remux(
                    filename=filename,
                    audio_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                    subtitle_languages=[StreamData.LANG_ENG, StreamData.LANG_JPN],
                    preferred_audio_language=StreamData.LANG_JPN,
                    preferred_subtitle_language=StreamData.LANG_ENG,
                )
            case Ripper.REMUX_NONE:
                self.logger.debug("No remuxing was requested. Skipping remuxing.")

    def _process_video_rename(self, filename: Path, title_number: int) -> Path:
        """Process video after extracting from disc.

        This is generally to rename the file and move it to something predictable.
        """

        # Set new filename
        media_title = self.title
        if self.year:
            media_title += " ({})".format(self.year)
        name = "{} I{}T{}{}".format(
            media_title,
            str(self.id).zfill(2),
            str(title_number).zfill(2),
            filename.suffix,
        )
        new_filename = self.videos_directory.joinpath(name)

        # Reset new filename of show episode to use season and season directory
        # Create season directory if it does not exist
        if self.media_type == Ripper.VIDEO_SHOW:
            if type(self.season) is int:
                if self.season >= 0:
                    season_directory = self.media_directory.joinpath(
                        "Season {}".format(str(self.season).zfill(2))
                    )
                    season_directory.mkdir(exist_ok=True)
                    name = "{} I{}S{}T{}{}".format(
                        media_title,
                        str(self.id).zfill(2),
                        str(self.season).zfill(2),
                        str(title_number).zfill(2),
                        filename.suffix,
                    )
                    new_filename = season_directory.joinpath(name)

        # Reset new filename of movie to move media directory
        if self.media_type == Ripper.VIDEO_MOVIE:
            name = "{} I{}T{}{}".format(
                media_title,
                str(self.id).zfill(2),
                str(title_number).zfill(2),
                filename.suffix,
            )
            new_filename = self.media_directory.joinpath(name)

        # Rename file as long as new filename does not exist
        if filename.is_file() and not new_filename.is_file():
            old_filename = filename
            filename = filename.rename(new_filename)
            self.logger.debug("Renamed {} to {}.".format(old_filename, filename))
        return filename

    def _eject(self, time_limit: int = 60) -> bool:
        """Function that unlocks end ejects the disc.

        The function effectively ejects in a loop until the tray is open or the time limit is reached.
        Returns true if the disc tray is ultimately open, otherwise it returns false.
        """
        timeout = time.time() + time_limit
        while True:
            self.disc.unlock_tray()
            self.disc.eject_tray()
            if self.disc.get_drive_status(self.disc.filename) == Disc.CDS_TRAY_OPEN:
                return True
            elif time.time() > timeout:
                return False

    def rip(self) -> None:
        """
        Rip the disc according to the disc type.
        If the disc is DVD or Blu-Ray,
            - makemkvcon is run
            - process_video is run if makemkvcon is successful

        Disc should eject if previous steps exited OK (unless eject attribute is False)
        An ejected disc SHOULD indicate that everything worked and the rip is complete
        """

        # Set thread name for logging purposes when not main thread
        if threading.main_thread != threading.current_thread():
            threading.current_thread().name = self.raw_filename.stem

        # Get time to track ripping time
        start = time.time()

        # Rip based on detected disc
        self.disc.query()

        match self.disc.disc_status:
            case Disc.CDS_DATA_1:
                # Parser for messaages
                # This also holds title information found in mmkv.titles
                mmkv = MakeMKVParser()

                # Setup makemkvcon for info
                makemkvcon = check_command("makemkvcon")
                command = [makemkvcon.as_posix()]
                command += ["--minlength={}".format(self.minimum_duration)]
                command += ["--robot"]
                command += ["--noscan"]
                command += ["info", "dev:{}".format(self.disc.filename.resolve())]
                self.logger.debug("Raw command: {}".format(" ".join(command)))

                # Run makemkvcon info to populate titles
                last_message = ""

                mmkv_info = GeneratorExit(run_command(command))
                for line in mmkv_info:
                    mmkv.parse(line)
                    if mmkv.message:
                        if mmkv.message != last_message:
                            self.logger.debug(mmkv.message)
                            last_message = mmkv.message
                self.last_run_code = mmkv_info.code

                # Exit if no titles are left
                if not mmkv.titles:
                    self.logger.debug("No titles were collected for ripping.")
                    return

                # Ensure media directory exists.
                # I.e "/media/shows/The Greatest Show of All Time"
                Path.mkdir(self.media_directory, exist_ok=True)

                # Ensure the videos directory exists.
                # I.e. "/media/shows/The Greatest Show of All Time/ripper1"
                Path.mkdir(self.videos_directory, exist_ok=True)

                # Filter titles with a duration outside of the given range
                max_duration = 0
                for title_number in mmkv.titles:
                    duration = mmkv.titles[title_number][
                        MakeMKVMessage.ATTR_ID.Duration
                    ]
                    if duration < self.minimum_duration:
                        mmkv.titles.pop(title_number)
                    if duration > self.maximum_duration:
                        mmkv.titles.pop(title_number)

                    if duration >= max_duration:
                        max_duration = duration

                    # Filter any titles < (max_duration * movie_minimum) if feature_only set
                    if self.media_type == Ripper.VIDEO_MOVIE and self.feature_only:
                        if duration < (max_duration * self.movie_minimum):
                            mmkv.titles.pop(title_number)

                # Set real title count to match what will be processed
                self.title_count = len(mmkv.titles)

                # Iterate over titles found previously
                for title_number in mmkv.titles:
                    filename = self.videos_directory.joinpath(
                        mmkv.titles[title_number][MakeMKVMessage.ATTR_ID.OutputFileName]
                    )

                    # Delete the video file if it already exists
                    filename.unlink(missing_ok=True)

                    # Setup makemkvcon for ripping
                    makemkvcon = check_command("makemkvcon")
                    command = [makemkvcon.as_posix()]
                    command += ["--minlength={}".format(self.minimum_duration)]
                    command += ["--robot"]
                    command += ["--noscan"]
                    command += [
                        "mkv",
                        "dev:{}".format(self.disc.filename.resolve()),
                        "{}".format(title_number),
                    ]
                    command += ["{}".format(self.videos_directory)]
                    command += ["--messages={}".format("-stdout")]
                    command += ["--progress={}".format("-same")]
                    self.logger.debug("Raw command: {}".format(" ".join(command)))

                    # Run makemkvcon mkv
                    last_message = ""
                    mmkv_mkv = GeneratorExit(run_command(command))
                    for line in mmkv_mkv:
                        mmkv.parse(line)
                        if mmkv.message:
                            if mmkv.message != last_message:
                                self.logger.debug(mmkv.message)
                                last_message = mmkv.message
                    self.last_run_code = mmkv_mkv

                    # Process video to ensure it is named something more predictable
                    filename = self._process_video_rename(filename, title_number)

                    # Remux video to remove extraneous streams based on given profile
                    filename = self._process_video_remux_profile(filename)

                # The videos directory may be empty after renaming all files
                # Delete the videos directory if it is empty
                if self.videos_directory.is_dir():
                    if not any(self.videos_directory.iterdir()):
                        self.videos_directory.rmdir()
            case _:
                pass

        # Always unlock the disc tray
        self.disc.unlock_tray()

        # Eject after processing if makemkvcon exited with 0
        if self.last_run_code == 0 and self.eject_on_rip:
            self._eject()

        time_elapsed = time.time() - start
        self.logger.debug("Rip Duration: {:.2f}s".format(time_elapsed))


def process_disc_devices(
    devices: list[Path], devices_root: Path = Path("/dev")
) -> list[Path]:
    """Process all disc devices in list of devices to remove duplicates.

    This function will process each device given and removes duplicates that resolve to the same device.
    The first symbolic link given for a device is kept over another symlink or raw device path.
    This supports udev rules and other common use cases where the kernel names are not desired.
    """

    # Fix partial items if full path was not given (assuming devices_root is valid)
    index = 0
    for device in devices[:]:
        if not device.is_absolute():
            device = devices_root.joinpath(device.stem)
            if device.is_block_device():
                devices[index] = device
        index += 1

    # Filter block devices and split out symlinks
    devices = [x for x in devices if x.is_block_device()]
    symlinks = [x for x in devices if x.is_symlink()]
    direct_links = list(set([x for x in devices if not x.is_symlink()]))

    # Filter symbolic links such that there is only 1 link for each target
    # The symlinks are removed from the end of the list
    symlinks.reverse()
    for device in symlinks[:]:
        if [x.resolve() for x in symlinks].count(device.resolve()) > 1:
            symlinks.remove(device)
    symlinks.reverse()

    # Remove items that have both a direct link and symlink for the same target, keeping the symbolic link
    for device in [x.resolve() for x in symlinks]:
        if device in [x.resolve() for x in direct_links]:
            direct_links.remove(device)

    devices = symlinks + direct_links
    devices.sort()
    return devices


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--devices",
        type=Path,
        help="The disc devices to rip from. Multiple device can be specified, separated by spaces",
        nargs="+",
        default=[],
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("/storage"),
        help="This set the root output directory.",
    )
    parser.add_argument(
        "-m",
        "--minimum",
        type=int,
        help="This set the minimum content duration (s).",
    )
    parser.add_argument(
        "-x",
        "--maximum",
        type=int,
        default=99999,
        help="This sets the maximum content duration (s).",
    )
    media_parser = parser.add_mutually_exclusive_group(required=True)
    media_parser.add_argument(
        "--video",
        help="Process content as generic video with given title. Use it when movie or show do not make sense",
    )
    media_parser.add_argument(
        "--movie",
        help="Process content as a movie with given title. Sets minimum duration to 3600 seconds unless given",
    )
    media_parser.add_argument(
        "--show",
        help="Process content as a show with given title. Sets minimum duration to 900 seconds unless given",
    )
    parser.add_argument(
        "--season",
        action="store",
        type=int,
        help='If media is a show, this will move files into a "Season" folder',
    )
    parser.add_argument(
        "--year",
        action="store",
        type=int,
        help="The year will be added to the output folder name. This should be the air year",
    )
    parser.add_argument(
        "--no-eject",
        action="store_true",
        default=False,
        help="Do not eject the disc regardless of ripping status.",
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

    # Set media_type and title based on required option
    if args.video:
        media_type = Ripper.VIDEO_GENERIC
        title = args.video
    elif args.show:
        media_type = Ripper.VIDEO_SHOW
        title = args.show
    elif args.movie:
        media_type = Ripper.VIDEO_MOVIE
        title = args.movie

    # Set remux profile
    remux_profile = Ripper.REMUX_NONE
    if args.remux_english:
        remux_profile = Ripper.REMUX_ENGLISH_ONLY
    elif args.remux_japanese:
        remux_profile = Ripper.REMUX_JAPANESE_ONLY
    elif args.remux_subs:
        remux_profile = Ripper.REMUX_ANIME_SUBS
    elif args.remux_dubs:
        remux_profile = Ripper.REMUX_ANIME_DUBS

    # Process duration limits
    # Set minimum duration based on type if not specified
    # Otherwise, set minimum duration to 0 if not defined > 0
    # Raise an error if maximum duration is not greater than minimum
    minimum_duration = args.minimum
    maximum_duration = args.maximum
    if media_type == Ripper.VIDEO_MOVIE and not minimum_duration:
        minimum_duration = 3600
    elif media_type == Ripper.VIDEO_SHOW and not minimum_duration:
        minimum_duration = 900
    elif not minimum_duration or minimum_duration < 0:
        minimum_duration = 0
    if maximum_duration <= minimum_duration:
        raise ValueError("Maximum duration must be greater than minimum!")

    # Check year is within 1888 to current year
    # 1888 is year for oldest surviving film, the "Roundhay Garden Scene"
    year = args.year
    if year:
        min_year = 1888
        max_year = int(time.strftime("%Y"))
        if year < min_year or year > max_year:
            raise ValueError(
                "The given year was not within {}-{}!".format(min_year, max_year)
            )

    # Check if season is valid
    # 0 is a common value for a season representing any "specials", so it is valid
    season = args.season
    if season:
        if season < 0:
            raise ValueError("The given season was less than 0!")

    # Determine output directory name based on title and year (if given)
    root_directory = args.output

    # Process given optical drives
    devices = args.devices
    devices = process_disc_devices(devices)

    # Set whether to eject disc after ripping
    eject = not args.no_eject

    # Rip media
    rippers = []
    futures = []
    thread_time_limit = 3600 * 5

    with ThreadPoolExecutor() as ex:
        for dev in devices:
            ripper = Ripper(
                dev,
                root_directory,
                minimum_duration,
                maximum_duration,
                media_type,
                title,
                season,
                year,
                eject,
                remux_profile,
            )
            rippers += [ripper]
            futures += [ex.submit(ripper.rip)]

        for future in futures:
            future.result(thread_time_limit)


if __name__ == "__main__":
    main()
