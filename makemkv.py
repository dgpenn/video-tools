#!/usr/bin/env python3

from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

"""
A not-so-fancy class to help interpret makemkvcon's mkv --robot output.

References:
- A large portion of the defined MakeMKVMessage class below is "trial and error" fromm observing makemkvcon's output.
    - Some of it has been misunderstood well enough to be badly defined and misunderstood more later.
- The open portions of the makemkvoss source code (https://forum.makemkv.com/forum/viewtopic.php?f=3&t=224) contains more defined helpful code.
    - See the ./makemkvgui/inc/lgpl/apdefs.h file.
    - Buy MakeMKV. It's worth it!
"""


@dataclass
class MakeMKVMessage:
    """A dataclass to define data parsed from makemkvcon's --robot output."""

    PRGV: ClassVar[str] = "PRGV"
    DRV: ClassVar[str] = "DRV"
    MSG: ClassVar[str] = "MSG"
    PRGT: ClassVar[str] = "PRGT"
    PRGC: ClassVar[str] = "PRGC"
    CINFO: ClassVar[str] = "CINFO"
    SINFO: ClassVar[str] = "SINFO"
    TINFO: ClassVar[str] = "TINFO"
    TCOUNT: ClassVar[str] = "TCOUNT"

    class UI_MSG(IntEnum):
        YES: int = 0
        NO: int = 1
        STREAM_AV_SYNC_ISSUE: int = 16
        DEBUG: int = 32
        HIDDEN: int = 64
        EVENT: int = 128
        BOX_OK: int = 260
        BOX_ERROR: int = 516
        BOX_YES_NO: int = 776
        BOX_WARNING: int = 1028
        BOX_YES_NO_ERR: int = 1288
        BOX_YES_NO_REG: int = 1544
        BOX_MASK: int = 3854
        VT_ITEM_BASE: int = 5200
        HAVE_URL: int = 131072
        FILE_AV_SYNC_ISSUES: int = 131088
        TITLE_SKIP_MIN_LENGTH: int = 16777216
        READ_ERRORS: int = 16908288

    class MSG_CODE(IntEnum):
        ITEM_INFO: int = 0  # This is a guess.
        LIBMKV_TRACE: int = 1002
        MAKEMKV_VERSION: int = 1005
        USING_LIBREDRIVE_MODE: int = 1011
        UDF_NODE_FAILED: int = 1012
        SCSI_ERROR: int = 2003
        READ_FASTER_THAN_WRITE = 2008
        HASH_CHECK_ERROR: int = 2023
        BAD_BACKUP_OFFSET: int = 3002
        USING_DIRECT_ACCESS_MODE: int = 3007
        TITLE_SKIP: int = 3025
        TITLE_DVD_ADDED: int = 3028
        CELLS_REMOVED: int = 3037
        TITLE_END_CELLS_REMOVED: int = 3038
        OPENING_DVD_DISC: int = 3100
        PROCESSING_TITLE_SETS: int = 3102
        PROCESSING_TITLES: int = 3103
        DECRYPTING_DVD_DATA: int = 3104
        SCANNING_CONTENTS: int = 3120
        TITLE_BD_ADDED: int = 3307
        DUPLICATE_TITLE_SKIPPED: int = 3309
        USING_JAVA_RUNTIME: int = 3344
        PROCESSING_AV_CLIPS: int = 3400
        PROCESSING_MOVIE_PLAYLISTS: int = 3401
        DECRYPTING_BD_DATA: int = 3402
        OPENING_BLURAY_DISC: int = 3404
        PROCESSING_BD_PLUS_CODE: int = 3406
        CORRUPT_SOURCE_FILE: int = 4004
        TITLE_AV_SYNC_ISSUE: int = 4007
        STREAM_AV_SYNC_ISSUE: int = 4008
        TOO_MANY_AV_SYNC_ISSUES: int = 4009
        TRACK_AV_SYNC_ISSUE: int = 4047
        ASK_OVERWRITE_FILE: int = 5001
        TITLE_SAVE_FAIL: int = 5003
        TITLES_SAVE_FAIL: int = 5004
        EVENT: int = 5005
        DISC_OPEN_FAIL: int = 5010
        OPERATION_COMPLETE: int = 5011
        SAVING_IN_DIR: int = 5014
        SAVING_TO_MKV_FILE: int = 5017
        SCANNING_CDROM_DEVICES: int = 5018
        SAVING_TITLES_TO_MKV_FILES: int = 5024
        COPY_COMPLETE: int = 5036
        COPY_COMPLETE_TITLES_FAILED: int = 5037
        EVALUATION_PERIOD_EXPIRED: int = 5051
        EVALUATION_PERIOD_EXPIRED_FREE_FUNC_ONLY: int = 5052
        EVALUATION_PERIOD_EXPIRED_X_DAYS_AGO: int = 5054
        EVALUATION_PERIOD_EXPIRED_NO_SHARE_FUNC: int = 5055
        ANALYZING_SEAMLESS_SEGMENTS: int = 5057
        HASH_CHECK_FAILURE: int = 5076
        TOO_MANY_HASH_CHECK_FAILURES: int = 5077
        LOADED_CONTENT_HASH_TABLE: int = 5085
        LOSSLESS_CONVERSION: int = 5088
        AUDIO_STEREO: int = 5091
        AUDIO_SURROUND: int = 5092
        ITEMINFO_SOURCE: int = 6119
        ITEMINFO_TITLE: int = 6120
        ITEMINFO_TRACK: int = 6121
        TRACK_VIDEO: int = 6201
        TRACK_AUDIO: int = 6202
        TRACK_SUBTITLES: int = 6203
        TYPE_DVD: int = 6206
        TYPE_BD: int = 6209
        TYPE_HDDVD: int = 6212

    class DISC_FLAG(IntEnum):
        UNKNOWN: int = 0
        DVD: int = 1
        HD_DVD: int = 2
        BD: int = 4
        AACS: int = 8
        BDSVM: int = 16

    class DRIVE_STATE(IntEnum):
        EMPTY_CLOSED: int = 0
        EMPTY_OPEN: int = 1
        INSERTED: int = 2
        LOADING: int = 3
        NO_DRIVE: int = 256
        UNMOUNTING: int = 257

    class ATTR_ID(IntEnum):
        Unknown: int = 0
        Type: int = 1
        Name: int = 2
        LangCode: int = 3
        LangName: int = 4
        CodecId: int = 5
        CodecShort: int = 6
        CodecLong: int = 7
        ChapterCount: int = 8
        Duration: int = 9
        DiskSize: int = 10
        DiskSizeBytes: int = 11
        StreamTypeExtension: int = 12
        Bitrate: int = 13
        AudioChannelsCount: int = 14
        AngleInfo: int = 15
        SourceFileName: int = 16
        AudioSampleRate: int = 17
        AudioSampleSize: int = 18
        VideoSize: int = 19
        VideoAspectRatio: int = 20
        VideoFrameRate: int = 21
        StreamFlags: int = 22
        DateTime: int = 23
        OriginalTitleId: int = 24
        SegmentsCount: int = 25
        SegmentsMap: int = 26
        OutputFileName: int = 27
        MetadataLanguageCode: int = 28
        MetadataLanguageName: int = 29
        TreeInfo: int = 30
        PanelTitle: int = 31
        VolumeName: int = 32
        OrderWeight: int = 33
        OutputFormat: int = 34
        OutputFormatDescription: int = 35
        SeamlessInfo: int = 36
        PanelText: int = 37
        MkvFlags: int = 38
        MkvFlagsText: int = 39
        AudioChannelLayoutName: int = 40
        OutputCodecShort: int = 41
        OutputConversionType: int = 42
        OutputAudioSampleRate: int = 43
        OutputAudioSampleSize: int = 44
        OutputAudioChannelsCount: int = 45
        OutputAudioChannelLayoutName: int = 46
        OutputAudioChannelLayout: int = 47
        OutputAudioMixDescription: int = 48
        Comment: int = 49
        OffsetSequenceId: int = 50

    MSG_CODE_ERRORS: ClassVar[set[int]] = (
        MSG_CODE.LIBMKV_TRACE,
        MSG_CODE.UDF_NODE_FAILED,
        MSG_CODE.SCSI_ERROR,
        MSG_CODE.HASH_CHECK_ERROR,
        MSG_CODE.CORRUPT_SOURCE_FILE,
        MSG_CODE.TOO_MANY_AV_SYNC_ISSUES,
        MSG_CODE.TITLE_SAVE_FAIL,
        MSG_CODE.TITLES_SAVE_FAIL,
        MSG_CODE.DISC_OPEN_FAIL,
        MSG_CODE.COPY_COMPLETE_TITLES_FAILED,
        MSG_CODE.EVALUATION_PERIOD_EXPIRED_FREE_FUNC_ONLY,
        MSG_CODE.EVALUATION_PERIOD_EXPIRED_NO_SHARE_FUNC,
        MSG_CODE.HASH_CHECK_FAILURE,
        MSG_CODE.TOO_MANY_HASH_CHECK_FAILURES,
    )

    MSG_CODE_SUCCESS: ClassVar[set[int]] = (MSG_CODE.OPERATION_COMPLETE,)


class MakeMKVParser:
    def __init__(self) -> None:
        # This is the last raw message received from parse().
        self.raw_message: str = ""

        # This is the last message type parsed by parse().
        self.message_type: str = ""

        # TCOUNT
        self.title_count: int = -1

        # PRGV
        # The "progress" refers to the current title.
        # The "total_progress" refers to the overall progress.
        self.progress: float = 0
        self.total_progress: float = 0

        # DRV
        self.drive_index: int = -1
        self.drive_visible: int = -1
        self.drive_enabled: int = -1
        self.disc_flags: int = -1
        self.drive_name: str = ""
        self.disc_name: str = ""

        # MSG | PRGC | PRGT
        # The flags, format, and params items are reset for PRGC and PRGT messages.
        self.operation: str = ""
        self.title_number: int = -1
        self.message: str = ""
        self.message_code: int = -1
        self.message_flags: int = -1
        self.message_format: str = ""
        self.message_params: list[str] = []

        # Populated via CINFO messags
        # Keys are simply MakeMKVMessage.ATTR_ID names, values are the associated values.
        self.disc: dict[str, str] = {}

        # Populated via TINFO messages
        # Each key is a title number while values are dicts representing an individual title.
        # Each title dict contains the associated MakeMKVMessage.ATTR_ID names and values.
        # Each title dict also contains also contains a "streams"  key, with a dict for each stream.
        # Each stream dict's keys and values are the MakeMKVMessage.ATTR_ID names and values.
        # I.e.
        # For "Duration" of title #0: self.titles[0][MakeMKVMessage.ATTR_ID.Duration]
        # For stream #2 of title #0: self.titles[0]["streams"][2]
        self.titles: dict[int, dict] = {}

        # This is incremented whenever a MSG code in MakeMKVMessage.MSG_CODE_ERRORS is received
        # Generally, this is an indication that the "makemkvcon <command>" has failed or may fail soon.
        # This is reset whenever a code in MakeMKVMessage.MSG_CODE_SUCCESS is received
        self.message_error_count: int = 0

        # This is incremented whenever a MSG code in MakeMKVMessage.MSG_CODE_SUCCESS is received
        # Generally, this is an indication of successful completion of an operation
        # It is not reset.
        self.message_success_count: int = 0

    def _process_id(self, id: int, raw_value: str) -> int | str:
        """Process the attr id and value from MakeMKV {C,T,S}INFO messages

        This removes the double quotes from any "value" strings.
        The value will be converted to an int or other type when it makes sense.

        There is a special case for "Duration", where it will be returned as an integer in seconds.

        """
        raw_value = raw_value.replace('"', "")
        match id:
            case MakeMKVMessage.ATTR_ID.Duration:
                hours, minutes, seconds = map(int, raw_value.split(":", 2))
                seconds += hours * 3600
                seconds += minutes * 60
                return seconds
            case (
                MakeMKVMessage.ATTR_ID.OrderWeight
                | MakeMKVMessage.ATTR_ID.ChapterCount
                | MakeMKVMessage.ATTR_ID.DiskSizeBytes
                | MakeMKVMessage.ATTR_ID.SegmentsCount
                | MakeMKVMessage.ATTR_ID.StreamFlags
                | MakeMKVMessage.ATTR_ID.AudioChannelsCount
                | MakeMKVMessage.ATTR_ID.AudioSampleRate
                | MakeMKVMessage.ATTR_ID.AudioSampleSize
            ):
                return int(raw_value)
            case _:
                return raw_value

    def parse(self, message: str) -> None:
        """
        Parse makemkvcon --robot option's output
        All of the message that can be parsed is parsed but not all data is kept.
        This is to ensure if the data is needed, it can be added easily.

        The appropriate fields in the instance are updated depending on message.
        Fields will not be cleared, so the state depends on the last message parsed.
        """
        self.raw_message = message.strip()

        try:
            self.message_type, content = self.raw_message.split(":", 1)
            match self.message_type:
                # Progress message for current operation and total progress
                case MakeMKVMessage.PRGV:
                    current, total, maximum_progress = map(float, content.split(",", 2))
                    self.progress = current / maximum_progress
                    self.total_progress = total / maximum_progress

                # Individual disc drive message
                case MakeMKVMessage.DRV:
                    index, visible, enabled, flags, drive_name, disc_name = (
                        content.split(",", 5)
                    )
                    self.drive_index = int(index)
                    self.drive_visible = int(visible)
                    self.disc_flags = int(flags)
                    self.drive_enabled = int(enabled)
                    self.drive_name = drive_name
                    self.disc_name = disc_name

                    try:
                        MakeMKVMessage.DRIVE_STATE(self.drive_visible)
                    except ValueError:
                        raise ValueError(
                            "The DRV visible value {} was not found!".format(
                                self.drive_visible
                            )
                        )

                    try:
                        MakeMKVMessage.DISC_FLAG(self.disc_flags)
                    except ValueError:
                        raise ValueError(
                            "The DRV flags value {} was not found!".format(
                                self.disc_flags
                            )
                        )

                # Literally "a message"; Content varies by message.
                case MakeMKVMessage.MSG:
                    code, flags, count, message, content = content.split(",", 4)

                    self.message_code = int(code)
                    self.message_flags = int(flags)
                    count = int(count)

                    if message:
                        self.message = message.replace('"', "")

                    try:
                        self.message_format, params = content.split(",", 1)
                    except ValueError:
                        self.message_format = content

                    if count:
                        self.message_params = params.split(",", count - 1)
                    else:
                        self.message_params = []

                    try:
                        MakeMKVMessage.UI_MSG(self.message_flags)
                    except ValueError:
                        raise ValueError(
                            "The MSG flags value {} was not found!".format(flags)
                        )

                    try:
                        MakeMKVMessage.MSG_CODE(self.message_code)
                    except ValueError:
                        raise ValueError(
                            "The MSG code value {} was not found!".format(code)
                        )

                    if code in list(MakeMKVMessage.MSG_CODE_ERRORS):
                        self.message_error_count += 1

                    if code in list(MakeMKVMessage.MSG_CODE_SUCCESS):
                        self.message_success_count += 1
                        # Reset erorr count when operation is successful.
                        self.message_error_count = 0

                # Current / Total Progress Title
                case MakeMKVMessage.PRGC | MakeMKVMessage.PRGT:
                    code, id, name = content.split(",", 2)
                    self.message_code = int(code)
                    self.title_number = int(id)
                    self.message = name.replace('"', "")
                    self.operation = MakeMKVMessage.MSG_CODE(self.message_code)

                    # Reset MSG items
                    self.message_flags = -1
                    self.message_format = ""
                    self.message_params = []

                # Disc Information
                case MakeMKVMessage.CINFO:
                    id, code, value = content.split(",", 2)
                    id = int(id)
                    code = int(code)
                    value = self._process_id(id, value)
                    self.disc[MakeMKVMessage.ATTR_ID(id)] = value

                # Title Information
                case MakeMKVMessage.TINFO:
                    title_number, id, code, value = content.split(",", 3)
                    title_number = int(title_number)
                    id = int(id)
                    code = int(code)
                    value = self._process_id(id, value)

                    # Add new title
                    if title_number not in self.titles:
                        self.titles[title_number] = {}
                        self.titles[title_number]["streams"] = {}

                    # Populate title information
                    self.titles[title_number][MakeMKVMessage.ATTR_ID(id)] = value

                # Stream Information
                case MakeMKVMessage.SINFO:
                    title_number, stream_number, id, code, value = content.split(",", 4)
                    title_number = int(title_number)
                    stream_number = int(stream_number)
                    id = int(id)
                    code = int(code)
                    value = self._process_id(id, value)

                    # Add new title; This is not expected to ever be needed unless messages are out of order.
                    if title_number not in self.titles:
                        self.titles[title_number] = {}
                        self.titles[title_number]["streams"] = {}

                    # Add new stream
                    if stream_number not in self.titles[title_number]["streams"]:
                        self.titles[title_number]["streams"][stream_number] = {}

                    # Populate stream information
                    self.titles[title_number]["streams"][stream_number][
                        MakeMKVMessage.ATTR_ID(id)
                    ] = value

                # Title Count
                case MakeMKVMessage.TCOUNT:
                    self.title_count = int(content)

                # This should not be reached unless a new message type is added.
                case _:
                    self.message = "Unknown MakeMKV Type! - {}".format(self.raw_message)

        except Exception as e:
            exception_message = (
                "Parsing Exception: {exception:}\nRaw Message: {raw_message:}".format(
                    exception=e, raw_message=self.raw_message
                )
            )
            self.message = exception_message
