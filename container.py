#!/usr/bin/env python3

import json
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import ClassVar

from common import check_command, get_logger

"""
References:
- Matroska Spec
    - https://www.matroska.org/technical/basics.html
"""


@dataclass
class AttachmentData:
    """A class to hold attachment data"""

    # References:
    # - https://www.matroska.org/technical/attachments.html

    IMG_JPEG: ClassVar[str] = "image/jpeg"
    IMG_PNG: ClassVar[str] = "image/png"

    IMG_TYPES = [IMG_JPEG, IMG_PNG]

    FONT_TTF: ClassVar[str] = "font/ttf"
    FONT_OTF: ClassVar[str] = "font/otf"
    FONT_SFNT: ClassVar[str] = "font/sfnt"
    FONT_WOFF: ClassVar[str] = "font/woff"
    FONT_WOFF2: ClassVar[str] = "font/woff2"
    FONT_COLLECTION: ClassVar[str] = "font/collection"

    # This font is equivalent to font/ttf or (sometimes) font/otf
    FONT_LEGACY_TTF: ClassVar[str] = "application/x-truetype-font"

    # This font is equivalent to font/ttf
    FONT_LEGACY_TTF2: ClassVar[str] = "application/x-font-ttf"

    # This font is equivalent to font/otf
    FONT_LEGACY_OTF: ClassVar[str] = "application/vnd.ms-opentype"

    # This font is equivalent to font/sfnt
    FONT_LEGACY_SFNT: ClassVar[str] = "application/font-sfnt"

    # This font is equivalent to font/woff
    FONT_LEGACY_WOFF: ClassVar[str] = "application/font-woff"

    FONT_TYPES = [
        FONT_TTF,
        FONT_OTF,
        FONT_SFNT,
        FONT_WOFF,
        FONT_WOFF2,
        FONT_COLLECTION,
        FONT_LEGACY_TTF,
        FONT_LEGACY_TTF2,
        FONT_LEGACY_OTF,
        FONT_LEGACY_SFNT,
        FONT_LEGACY_WOFF,
    ]

    # This is probaly a font, but must be examined to determine.
    # The attached file's extension can be used to indicate this.
    # .ttf, .otf, and .ttc are common extensions.
    # .ttc is for "collection"
    OCTET_STREAM: ClassVar[str] = "application/octet-stream"

    id: int = -1
    type: str = None
    filename: Path = None
    description: str = ""

    def is_valid(self) -> bool:
        """Returns a bool for whether the instance is valid"""
        if (
            self.type.lower() in (AttachmentData.IMG_TYPES + AttachmentData.FONT_TYPES)
            and self.filename
        ):
            return True
        elif self.type.lower() in [AttachmentData.OCTET_STREAM] and self.filename:
            if self.filename.suffix.lower() in [".ttf", ".otf", ".ttc"]:
                return True
        return False


@dataclass
class ChapterData:
    """A class to hold chapter data

    index: The chapter index starting from 1
    id: The chapter UID
    title: The chapter title
    start_time: The chapter start time
    end_time: The chapter end time
    duration: The result of end_time - start_time
    """

    index: int = None
    id: int = None
    title: str = None
    start_time: float = None
    end_time: float = None
    duration: float = None

    def __lt__(self, other: type["ChapterData"]) -> bool:
        if self.start_time < other.start_time:
            return True

    def __gt__(self, other: type["ChapterData"]) -> bool:
        if self.start_time > other.start_time:
            return True

    def __eq__(self, other: type["ChapterData"]) -> bool:
        if self.start_time == other.start_time:
            return True

    def is_valid(self) -> bool:
        """Returns a bool for whether the instance is valid"""
        if (
            isinstance(self.start_time, float)
            and isinstance(self.end_time, float)
            and isinstance(self.duration, float)
        ):
            return True
        return False


# type function to prevent name conflicts with instance variable "type"
_type_fn = type


@dataclass
class StreamData:
    # These are defined as track types in Matroska spec.
    # Other types not included here are complex, logo, buttons, control, and metadata
    VIDEO: ClassVar[str] = "video"
    AUDIO: ClassVar[str] = "audio"
    SUBTITLES: ClassVar[str] = "subtitles"

    # These are ISO-639-2 language codes.
    # More may be added if needed but previously observed languages are covered already.
    LANG_CHI: ClassVar[str] = "chi"
    LANG_DAN: ClassVar[str] = "dan"
    LANG_DUT: ClassVar[str] = "dut"
    LANG_ENG: ClassVar[str] = "eng"
    LANG_FIN: ClassVar[str] = "fin"
    LANG_FRE: ClassVar[str] = "fre"
    LANG_GER: ClassVar[str] = "ger"
    LANG_IND: ClassVar[str] = "ind"
    LANG_ITA: ClassVar[str] = "ita"
    LANG_JPN: ClassVar[str] = "jpn"
    LANG_KOR: ClassVar[str] = "kor"
    LANG_MAY: ClassVar[str] = "may"
    LANG_NOR: ClassVar[str] = "nor"
    LANG_POR: ClassVar[str] = "por"
    LANG_SPA: ClassVar[str] = "spa"
    LANG_SWE: ClassVar[str] = "swe"
    LANG_THA: ClassVar[str] = "tha"
    LANG_UND: ClassVar[str] = "und"

    type: str = None
    id: int = None
    uid: int = None
    title: str = None
    language: str = None
    bps: int = None
    default: bool = False
    frames: int = 0
    codec: str = None
    pixel_width: int = 0
    pixel_height: int = 0
    display_width: int = 0
    display_height: int = 0

    def __eq__(self, other: _type_fn["StreamData"]) -> bool:
        if self.type == other.type:
            return self.bps == other.bps
        return self.id == other.id

    def __gt__(self, other: _type_fn["StreamData"]) -> bool:
        if self.type == other.type:
            return self.bps > other.bps
        return self.id > other.id

    def __lt__(self, other: _type_fn["StreamData"]) -> bool:
        if self.type == other.type:
            return self.bps < other.bps
        return self.id < other.id

    def is_valid(self) -> bool:
        """Returns a bool for whether the instance is valid"""

        if not isinstance(self.id, int):
            return False
        else:
            if self.id < 0:
                return False

        if self.type not in [
            StreamData.VIDEO,
            StreamData.AUDIO,
            StreamData.SUBTITLES,
        ]:
            return False

        if self.type == StreamData.VIDEO:
            if (
                self.pixel_width <= 0
                or self.pixel_height <= 0
                or self.display_width <= 0
                or self.display_height <= 0
            ):
                return False

        return True


class Container:
    """This is a container class for any video file."""

    def __init__(self, filename: Path, logger_name="RIP"):
        self.last_run_code: int = -1
        self.logger: Logger = get_logger(logger_name)

        # The following are reset by reload().
        # These are defined here so all atrributes can be observed.
        self.filename: Path = filename
        if self.filename.is_file():
            self.size: int = self.filename.stat().st_size
        self.title: str = None
        self.duration: int = None
        self.streams: list[StreamData] = []
        self.chapters: list[ChapterData] = []
        self.attachments: list[AttachmentData] = []

        self.reload(filename)

    def __eq__(self, other: type["Container"]) -> bool:
        return self.filename == other.filename

    def __lt__(self, other: type["Container"]) -> bool:
        return self.filename < other.filename

    def __gt__(self, other: type["Container"]) -> bool:
        return self.filename > other.filename

    def __repr__(self) -> str:
        rv = [
            "{} (Valid={})\n".format(self.filename, self.is_valid()),
            "Duration: {}s\n".format(self.duration),
            "Chapters: {}\n".format(len(self.chapters)),
            "Streams: {}\n".format(len(self.streams)),
            "Attachments: {}\n".format(len(self.attachments)),
        ]
        return " ".join(rv)

    def reload(self, filename: Path):
        self.logger.debug("Reload called for {}".format(filename.as_posix()))
        self.filename: Path = filename
        if self.filename.is_file():
            self.size: int = self.filename.stat().st_size
        self.title = None
        self.duration = None
        self.streams = []
        self.chapters = []
        self.attachments = []
        self._process(filename)

    def _get_json(self, filename: Path, logger_name: str = "RIP") -> dict:
        """Returns JSON dictionary from the mkvmerge -J command.

        If the JSON cannot be decoded, an empty dictionary is returned instead.
        """
        logger = get_logger(logger_name)
        mkvmerge = check_command("mkvmerge")
        command = [mkvmerge.as_posix(), "-J", filename.as_posix()]
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        output, errors = p.communicate()
        if errors:
            for line in errors:
                line = line.strip()
                if line:
                    logger.error(line)
        if not output:
            raise ValueError("The mkvmerge JSON generation failed!")
        try:
            json_output = json.loads(output)
            return json_output
        except json.JSONDecodeError:
            return {}

    def _process_json_container(self, json: dict) -> None:
        """Process container section of mkvmerge -J output"""
        container = json.get("container", {})
        container_props = container.get("properties", {})
        self.title = container_props.get("title")
        try:
            duration = container_props.get("duration")
            timestamp_scale = container_props.get("timestamp_scale")
            self.duration = duration / timestamp_scale / 1000
        except TypeError:
            self.duration = None

    def _process_json_tracks(self, json: dict) -> None:
        """Process tracks section of mkvmerge -J output

        This will ultimately add stream objects into the streams list.
        """
        tracks = json.get("tracks", [])
        for track in tracks:
            track_properties = track.get("properties", {})
            stream_type = track.get("type")
            pixel_width, pixel_height = map(
                int, track_properties.get("pixel_dimensions", "0x0").split("x")
            )
            display_width, display_height = map(
                int, track_properties.get("display_dimensions", "0x0").split("x")
            )

            stream_info = StreamData(
                id=int(track.get("id")),
                uid=int(track_properties.get("uid")),
                type=stream_type,
                title=track_properties.get("track_name"),
                language=track_properties.get("language"),
                bps=track_properties.get("tag_bps"),
                default=track_properties.get("default_track"),
                codec=track_properties.get("codec_id"),
                frames=int(track_properties.get("tag_number_of_frames")),
                pixel_width=pixel_width,
                pixel_height=pixel_height,
                display_width=display_width,
                display_height=display_height,
            )
            if stream_info.is_valid():
                self.streams += [stream_info]

    def _process_json_attachments(self, json: dict) -> None:
        """Process attachments section of mkvmerge -J output"""
        attachments = json.get("attachments", [])
        for attachment in attachments:
            id = int(attachment.get("id"))
            attachment_info = AttachmentData(
                id=id,
                type=attachment.get("content_type"),
                filename=attachment.get("file_name"),
                description=attachment.get("description"),
            )
            if attachment_info.is_valid():
                self.attachments += [attachment_info]

    def _detect_chapter_gaps(self) -> bool:
        """
        This function returns True if there is a gap between any two consecutive chapters.
        """
        previous_chapter = None
        for chapter in sorted(self.chapters):
            if previous_chapter:
                delta = chapter.start_time - previous_chapter.end_time
                if delta > 0:
                    return True
            previous_chapter = chapter
        return False

    def _get_chapters(self) -> None:
        """
        Get chapters using mkvextract and process the file.
        """
        try:
            mkvextract = check_command("mkvextract")
            chapters_filename = Path("{}.chapters.xml".format(self.filename.name))
            command = [
                mkvextract.as_posix(),
                self.filename.as_posix(),
                "chapters",
                chapters_filename.as_posix(),
            ]
            self.last_run_code = subprocess.check_call(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            tree = ET.parse(chapters_filename)
            chapters = []
            root = tree.getroot()
            for chapter_atom in root.iter("ChapterAtom"):
                chapter = ChapterData()
                for child in chapter_atom.iter():
                    match child.tag:
                        case "ChapterUID":
                            chapter.id = int(child.text.strip())
                            chapter.index = len(chapters) + 1
                        case "ChapterTimeStart":
                            hours, minutes, seconds = map(float, child.text.split(":"))
                            seconds += (hours * 3600) + (minutes * 60)
                            chapter.start_time = seconds
                        case "ChapterTimeEnd":
                            hours, minutes, seconds = map(float, child.text.split(":"))
                            seconds += (hours * 3600) + (minutes * 60)
                            chapter.end_time = seconds
                        case "ChapterString":
                            chapter.title = child.text.strip()
                chapter.duration = chapter.end_time - chapter.start_time
                if chapter.is_valid():
                    chapters += [chapter]
            chapters.sort()
            self.chapters = chapters
        except subprocess.CalledProcessError:
            self.logger.error(
                "Failure to extract chapters of {}!".format(self.filename)
            )
        except FileNotFoundError:
            self.logger.error(
                "Failure to write chapters file for {}".format(self.filename)
            )
        finally:
            chapters_filename.unlink(missing_ok=True)

    def _process(self, filename: Path):
        "Process JSON for filename."
        _json = self._get_json(filename)
        self._process_json_container(_json)
        self._process_json_tracks(_json)
        self._process_json_attachments(_json)
        self._get_chapters()
        self.is_valid()

    def set_title(self, title: str) -> None:
        """
        Set title for a given MKV file
        """
        title = title.strip()
        mkvpropedit = check_command("mkvpropedit")
        command = [
            mkvpropedit.as_posix(),
            self.filename.as_posix(),
            "--edit",
            "info",
            "--set",
            "title={}".format(title),
        ]
        try:
            self.last_run_code = subprocess.check_call(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.title = title
        except subprocess.CalledProcessError:
            self.logger.error("Failed to set title for {}".format(self.filename))

    def remux_by_language(
        self, audio_languages: list[str], subtitle_languages: list[str]
    ) -> None:
        """Filter and remux video by audio and subtitle languages specified.

        This removes audio and subtitle streams of languages not specified to reduce filesize.
        Streams not specified by any language will be removed from output except for "undetermined", which is always kept unless all specified languages are available.
        If all specified languages are available, it is assumed that "undetermined" streams are not wanted.
        """

        mkvmerge = check_command("mkvmerge")

        # Always add "und" type to filter if not all languages are present
        # This ensures if the missing language is actually "und", it is kept
        if StreamData.LANG_UND not in audio_languages:
            und_flag = False
            for language in audio_languages:
                if not [
                    x
                    for x in self.streams
                    if x.language == language and x.type == StreamData.AUDIO
                ]:
                    und_flag = True
                    break
            if und_flag:
                audio_languages += [StreamData.LANG_UND]
                self.logger.warning("Undetermined audio streams will be included.")

        if StreamData.LANG_UND not in subtitle_languages:
            und_flag = False
            for language in subtitle_languages:
                if not [
                    x
                    for x in self.streams
                    if x.language == language and x.type == StreamData.SUBTITLES
                ]:
                    und_flag = True
                    break
            if und_flag:
                subtitle_languages += [StreamData.LANG_UND]
                self.logger.warning("Undetermined subtitle streams will be included.")

        # Set output filename for remuxed output
        output_filename = self.filename.parent.joinpath(
            self.filename.stem + ".remuxed" + self.filename.suffix
        )

        # Setup remuxing command with output filename
        command = [
            mkvmerge.as_posix(),
            "-o",
            output_filename.as_posix(),
        ]
        # Add audio streams that match specified languages
        # Add all audio streams if there are no matches
        if audio_languages:
            command += [
                "--audio-tracks",
                "{}".format(",".join(audio_languages)),
            ]
        else:
            self.logger.warning(
                "Specified audio languages not available! Audio streams will not be removed!"
            )
        # Add subtitles only if they match specified language, otherwise add none
        if subtitle_languages:
            command += [
                "--subtitle-tracks",
                "{}".format(",".join(subtitle_languages)),
            ]
        else:
            command += ["--no-subtitles"]
        # Add input filename
        command += [
            self.filename.as_posix(),
        ]

        # Remux
        self.logger.debug("Raw command: {}".format(" ".join(command)))
        try:
            self.last_run_code = subprocess.check_call(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            self.logger.error("Failure to remux {}!".format(self.filename))
            raise

        # Delete original file and rename remuxed file to match original
        # Reload data to update instance for newly remuxed file
        if output_filename.exists() and self.last_run_code == 0:
            self.filename.unlink(missing_ok=False)
            filename = output_filename.rename(self.filename.resolve())
            self.reload(filename)

    def _set_default_stream_by_language(
        self, language: str, stream_type: str, default_required=False
    ) -> None:
        """
        Set default stream for a given type of stream by language (using mkvpropedit)
        The default_required flag will force something of stream_type to be default regardless of language.
        """

        # Get streams of stream type that match the right language
        streams = [
            x for x in self.streams if x.type == stream_type and x.language == language
        ]

        # Log error for no streams of desired language
        if not streams:
            self.logger.error(
                "Failure to set default {} stream as {}! Nothing to set!".format(
                    stream_type, language
                )
            )

        # Reset streams if "something" needs to be set for the stream type
        if not streams and default_required:
            streams = [x for x in self.streams if x.type == stream_type]
            self.logger.warning(
                "Setting arbitrary stream as default {} stream!".format(stream_type)
            )

        # If a stream is available to mark as default, do it
        if streams:
            # If setting subtitles, sort such that the first stream is the "largest" stream
            # This is to avoid setting a subtitles stream with very few subttiles as default
            # E.g. There are subtitles for a show "opening" only instead of the full episode
            if stream_type == StreamData.SUBTITLES:
                streams.sort(key=lambda x: x.frames, reverse=True)

            stream = streams[0]
            if stream.default:
                self.logger.debug(
                    "Skipping setting default stream. Stream is already default."
                )
                return
            try:
                mkvpropedit = check_command("mkvpropedit")
                command = [
                    mkvpropedit.as_posix(),
                    self.filename.as_posix(),
                    "--edit",
                    "track:={}".format(stream.uid),
                    "--set",
                    "flag-default=1",
                ]
                self.logger.debug("Raw command: {}".format(" ".join(command)))
                self.last_run_code = subprocess.check_call(
                    command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                self.logger.debug(
                    "The {} stream id {} was set as default.".format(
                        stream.type, stream.id
                    )
                )
            except subprocess.CalledProcessError:
                self.logger.error(
                    "Failure to set default {} stream!".format(stream_type)
                )
            finally:
                self.reload(self.filename)

    def set_preferred_audio_by_language(
        self, language: str, default_required=True
    ) -> None:
        self._set_default_stream_by_language(
            stream_type=StreamData.AUDIO,
            language=language,
            default_required=default_required,
        )

    def set_preferred_subtitles_by_language(
        self, language: str, default_required=False
    ) -> None:
        self._set_default_stream_by_language(
            stream_type=StreamData.SUBTITLES,
            language=language,
            default_required=default_required,
        )

    def clear_default_audio(self) -> None:
        """Set no audio as default."""

        audio_streams = [x for x in self.streams if x.type == StreamData.AUDIO]
        if not audio_streams:
            return

        for stream in audio_streams:
            if stream.default:
                try:
                    mkvpropedit = check_command("mkvpropedit")
                    command = [
                        mkvpropedit.as_posix(),
                        self.filename.as_posix(),
                        "--edit",
                        "track:={}".format(stream.uid),
                        "--set",
                        "flag-default=0",
                    ]
                    self.logger.debug("Raw command: {}".format(" ".join(command)))
                    self.last_run_code = subprocess.check_call(
                        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError:
                    self.logger.error("Failure to clear default audio stream!")
                finally:
                    self.reload(self.filename)
                    break

    def clear_default_subtitles(self) -> None:
        """Set no subtitles as default."""

        subtitles_streams = [x for x in self.streams if x.type == StreamData.SUBTITLES]
        if not subtitles_streams:
            return

        for stream in subtitles_streams:
            if stream.default:
                try:
                    mkvpropedit = check_command("mkvpropedit")
                    command = [
                        mkvpropedit.as_posix(),
                        self.filename.as_posix(),
                        "--edit",
                        "track:={}".format(stream.uid),
                        "--set",
                        "flag-default=0",
                    ]
                    self.logger.debug("Raw command: {}".format(" ".join(command)))
                    self.last_run_code = subprocess.check_call(
                        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                except subprocess.CalledProcessError:
                    self.logger.error("Failure to clear default subtitles stream!")
                finally:
                    self.reload(self.filename)
                    break

    def is_valid(self) -> bool:
        """Validate instance to ensure minimum attributes are set.
        Returns True if instance is valid.
        """
        self._valid = bool(
            self.filename and self.streams and not self._detect_chapter_gaps()
        )
        return self._valid

    def split(self, chapter_indices: list[int], basename: str = "") -> None:
        """Split file into separate videos by chapter indices (using mkvmerge).
        If basename is not set, basename will be based on the input filename.
        The output directory is the location of the input filename.
        """
        if not basename:
            basename = self.filename.stem
        mkvmerge = check_command("mkvmerge")
        command = [
            mkvmerge.as_posix(),
            "-o",
            "{}-%02d{}".format(basename, self.filename.suffix),
            "--split",
            "chapters:{}".format(",".join(map(str, chapter_indices))),
            self.filename.as_posix(),
        ]
        try:
            self.last_run_code = subprocess.check_call(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=self.filename.parent.as_posix(),
            )
        except subprocess.CalledProcessError:
            self.logger.error("Failure to split {}!".format(self.filename))
