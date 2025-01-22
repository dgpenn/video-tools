#!/usr/bin/env python3

"""

References:
- https://github.com/torvalds/linux/blob/ac865f00af293d081356bec56eea90815094a60e/include/uapi/linux/cdrom.h
- http://www.cdrlabs.com/forums/mode-versus-mode-discs-t8075.html
- https://www.soundonsound.com/techniques/compact-disc-formats-explained

"""

import argparse
import fcntl
import os
from pathlib import Path
from typing import ClassVar


def fd_command(filename: Path, command: int, arg: int = 0) -> int:
    """This function wraps the function fcntl.ioctl and returns the status.

    This is to allow a device Path object to be specified directly.
    """
    status = None
    fd = os.open(filename.as_posix(), os.O_NONBLOCK)
    status = fcntl.ioctl(fd, command, arg)
    os.close(fd)
    return status


class Disc:
    """A simple class to query drive status, disc status, and send simple commands using ioctl calls."""

    MAJOR_DEV_SCSI_CDROM: ClassVar[int] = 11

    CDROM_DRIVE_STATUS: ClassVar[int] = 0x5326
    CDROM_DISC_STATUS: ClassVar[int] = 0x5327
    CDROM_EJECT: ClassVar[int] = 0x5309
    CDROM_CLOSETRAY: ClassVar[int] = 0x5319
    CDROM_LOCKDOOR: ClassVar[int] = 0x5329

    CDS_NO_INFO: ClassVar[int] = 0
    CDS_NO_DISC: ClassVar[int] = 1
    CDS_TRAY_OPEN: ClassVar[int] = 2
    CDS_DRIVE_NOT_READY: ClassVar[int] = 3
    CDS_DISC_OK: ClassVar[int] = 4

    CDS_AUDIO: ClassVar[int] = 100
    CDS_DATA_1: ClassVar[int] = 101
    CDS_DATA_2: ClassVar[int] = 102
    CDS_XA_1: ClassVar[int] = 103
    CDS_XA_2: ClassVar[int] = 104
    CDS_MIXED: ClassVar[int] = 105

    CDS_DRIVE_STATUS: ClassVar[dict[int, str]] = {}
    CDS_DRIVE_STATUS[0] = "No Info"
    CDS_DRIVE_STATUS[1] = "No Disc"
    CDS_DRIVE_STATUS[2] = "Tray Open"
    CDS_DRIVE_STATUS[3] = "Drive Not Ready"
    CDS_DRIVE_STATUS[4] = "Disc OK"

    CDS_COLOR_DEF: ClassVar[dict[int, str]] = {}
    CDS_COLOR_DEF[1] = "No Disc"
    CDS_COLOR_DEF[100] = "Audio (Red Book)"
    CDS_COLOR_DEF[101] = "Data (Yellow Book, Mode 1 Form 1)"
    CDS_COLOR_DEF[102] = "Data (Yellow Book, Mode 1 Form 2)"
    CDS_COLOR_DEF[103] = "XA Data (Green Book, Mode 2 Form 1)"
    CDS_COLOR_DEF[104] = "XA Data (Green Book, Mode 2 Form 2)"
    CDS_COLOR_DEF[105] = "Mixed"

    def __init__(self, filename: Path):
        self.filename: Path = filename
        self.valid: bool = False
        self.drive_status: int = self.CDS_NO_INFO
        self.disc_status: int = self.CDS_NO_DISC
        self.query()

    def __repr__(self) -> str:
        link = ""
        if self.filename.is_symlink():
            link = " ({})".format(self.filename.absolute())
        rv = ""
        rv += "Filename: {}{}\n".format(self.filename.resolve(), link)
        rv += "Valid: {}\n".format(self.valid)
        rv += "Drive_Status: {}\n".format(self.drive_status)

        status = self.disc_status
        if status in Disc.CDS_COLOR_DEF:
            status = Disc.CDS_COLOR_DEF[status]
        rv += "Disc_Status: {}".format(status)

        return rv

    def __lt__(self, other: type["Disc"]) -> bool:
        if self.filename.is_symlink() and other.filename.is_symlink():
            return self.filename.absolute() < other.filename.absolute()
        elif self.filename.is_symlink():
            return True
        else:
            return self.filename < other.filename

    def __gt__(self, other: type["Disc"]) -> bool:
        if self.filename.is_symlink() and other.filename.is_symlink():
            return self.filename.absolute() > other.filename.absolute()
        elif self.filename.is_symlink():
            return True
        else:
            return self.filename > other.filename

    def __eq__(self, other: type["Disc"]) -> bool:
        if self.filename.is_symlink() and other.filename.is_symlink():
            return self.filename.absolute() == other.filename.absolute()
        elif self.filename.is_symlink():
            return True
        else:
            return self.filename == other.filename

    def query(self) -> None:
        if self.filename.exists():
            self.valid = self.validate_disc_device(self.filename)

        if self.valid:
            self.drive_status = self.get_drive_status(self.filename)
            self.disc_status = self.get_disc_status(self.filename)

    def name(self) -> Path:
        if self.filename.is_symlink():
            return self.filename
        return self.filename.resolve()

    def eject_tray(self) -> int:
        status = fd_command(self.filename, Disc.CDROM_EJECT)
        return status

    def close_tray(self) -> int:
        status = fd_command(self.filename, Disc.CDROM_CLOSETRAY)
        return status

    def unlock_tray(self) -> int:
        status = fd_command(self.filename, Disc.CDROM_LOCKDOOR, 0)
        return status

    def lock_tray(self) -> int:
        status = fd_command(self.filename, Disc.CDROM_LOCKDOOR, 1)
        return status

    @staticmethod
    def validate_disc_device(filename: Path) -> bool:
        rdev = Path(filename).stat().st_rdev
        if os.major(rdev) == Disc.MAJOR_DEV_SCSI_CDROM:
            return True
        return False

    @staticmethod
    def get_drive_status(filename: Path) -> int:
        status = fd_command(filename, Disc.CDROM_DRIVE_STATUS)
        match status:
            case (
                Disc.CDS_NO_INFO
                | Disc.CDS_NO_DISC
                | Disc.CDS_TRAY_OPEN
                | Disc.CDS_DRIVE_NOT_READY
                | Disc.CDS_DISC_OK
            ):
                return status
            case _:
                raise ValueError("Unknown drive status! --> {}".format(status))

    @staticmethod
    def get_disc_status(filename: Path) -> int:
        status = fd_command(filename, Disc.CDROM_DISC_STATUS)
        match status:
            case (
                Disc.CDS_AUDIO
                | Disc.CDS_DATA_1
                | Disc.CDS_DATA_2
                | Disc.CDS_XA_1
                | Disc.CDS_XA_2
                | Disc.CDS_MIXED
                | Disc.CDS_NO_DISC
                | Disc.CDS_NO_INFO
            ):
                return status

            case _:
                raise ValueError("Unknown disc status --> {}".format(status))

    @staticmethod
    def query_all_drives(
        devices_directory: Path = Path("/dev"),
        only_symbolic_links: bool = False,
        blacklist: list[str] = [],
    ) -> list[type["Disc"]]:
        discs = []
        for device in devices_directory.iterdir():
            if not device.is_block_device():
                continue

            if only_symbolic_links and not device.is_symlink():
                continue

            if device.name in blacklist:
                continue

            disc = Disc(device)
            if disc.valid:
                discs += [disc]
        discs.sort()
        return discs


if __name__ == "__main__":
    epilog = "If no arguments are given, each drive status is printed."
    parser = argparse.ArgumentParser(epilog=epilog)
    locking_group = parser.add_mutually_exclusive_group()
    locking_group.add_argument(
        "--unlock",
        action="store_true",
        default=False,
        help="Send the unlock tray command to each drive specified",
    )
    locking_group.add_argument(
        "--lock",
        action="store_true",
        default=False,
        help="Send the lock tray command to each drive specified",
    )

    tray_group = parser.add_mutually_exclusive_group()
    tray_group.add_argument(
        "--eject",
        action="store_true",
        default=False,
        help="Send the eject tray command to each drive specified",
    )
    tray_group.add_argument(
        "--close",
        action="store_true",
        default=False,
        help="Send the close tray command to each drive specified",
    )
    parser.add_argument(
        "--query",
        action="store",
        default=Path("/dev"),
        type=Path,
        help="Scan given directory when looking for devices to query if no devices are given as args",
    )
    parser.add_argument(
        "disc_devices", type=Disc, metavar="device", action="store", nargs="*"
    )
    parser.add_argument(
        "--blacklist",
        action="append",
        type=list[str],
        default=["cdrom", "dvd"],
        help="Add device names to ignore blacklist",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="When scanning for devices, include all devices instead of only the symbolic links",
    )
    args = parser.parse_args()

    disc_devices = args.disc_devices
    blacklist = args.blacklist
    query = args.query
    unlock = args.unlock
    lock = args.lock
    eject = args.eject
    close = args.close

    only_symbolic_links = not args.all

    if not only_symbolic_links:
        blacklist = []

    if not query.exists():
        print("The given device query path could not be found!")
    elif not disc_devices:
        disc_devices = Disc.query_all_drives(
            query,
            only_symbolic_links=only_symbolic_links,
            blacklist=blacklist,
        )

    for d in disc_devices:
        if d.valid:
            if unlock:
                print("Unlocking {}".format(d.name()))
                d.unlock_tray()
            elif lock:
                print("Locking {}".format(d.name()))
                d.lock_tray()
            if eject:
                print("Ejecting {}".format(d.name()))
                d.eject_tray()
            elif close:
                print("Closing {}".format(d.name()))
                d.close_tray()
            if not (unlock or lock or eject or close):
                print("{}\n".format(d))
        else:
            print("Bad Device: {}\n".format(d.name()))
