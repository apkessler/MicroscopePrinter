#!/usr/bin/python3

"""
Look for new microscope files, and print them
"""
import argparse
import sys
import os, time
import subprocess
import cups
from loguru import logger
import yaml


def get_file_list(path: str):
    return dict([(f, None) for f in os.listdir(path)])


class PrinterHelper:
    def __init__(self):
        pass

    def find_printer(self, max_attempts: int = 5, holdoff_sec: float = 3) -> bool:
        """Try to find a printer

        Parameters
        ----------
        max_attempts : int, optional
            Max number of times to look for printers, by default 5
        holdoff_sec : float, optional
            How long to wait between search attempets, by default 3

        Returns
        -------
        bool
            True if printers found
        """
        conn = cups.Connection()

        for attempt in range(max_attempts):
            logger.info(f"Printer attempt {attempt + 1}/{max_attempts}")
            printers = conn.getPrinters()
            if len(printers) == 0:
                logger.error("No printers found!")

            else:
                for prntr in printers:
                    logger.success(f"Found printer: {prntr}!")
                    return True


            time.sleep(holdoff_sec)

        return False

    def print_picture(self, filename: str):
        """
        Send the given filename to the printer to print.
        """
        logger.info(f"Printing {filename}...")
        sts = subprocess.run(["lp", filename], capture_output=True)
        if sts.returncode == 0:
            # If successful, lp will print b'request id is <job-id> (1 file(s))\n'
            jobId = (sts.stdout.decode("utf-8").split())[3]
            logger.info(f"Started {jobId=}")
        else:
            logger.error(f"lp error {sts.returncode}!: {sts.stderr.decode('utf-8')}")

        # Now wait for job to complete
        status = ""
        while status != "idle.":  # TODO: This is a bit hacky, but it works.
            time.sleep(2)
            sts = subprocess.run(["lpstat", "-p"], capture_output=True)
            status = (sts.stdout.decode("utf-8").split())[3]
            logger.info(status)

        logger.success(f"Done printing {filename}!")


class VirtualFlashDrive:
    def __init__(
        self,
        local_mount_dir: str,
        watch_dir: str,
        binary_file: str,
        simulate: bool = False,
    ):
        self.local_mount_dir = local_mount_dir
        self.watch_dir = watch_dir
        self.binary_file = binary_file
        self.simulate = simulate

        self.is_usb_mounted: bool = False

    def mount_local(self):
        """
        Mount the mirror of the shared memory on the local file system.
        """
        logger.info("Local mount")
        if not self.simulate:
            subprocess.call("sudo mount -a", shell=True)

    def unmount_local(self):
        """
        Unmount the mirror of the shared memory on the local system.
        """
        logger.info("Unmounting local side.")
        if not self.simulate:
            subprocess.call(f"umount {self.local_mount_dir}", shell=True)

    def mount_USB(self):
        """
        Mount the USB drive (virtually plug in)
        """

        logger.info("Mounting USB side")

        if not self.simulate:
            subprocess.call(
                f"sudo modprobe g_mass_storage file={self.binary_file} stall=0 ro=0 removeable=1",
                shell=True,
            )
        self.is_usb_mounted = True

    def unmount_USB(self):
        """
        Unmount the USB drive (virtually unplug)
        """

        logger.info("Unmounting USB side")

        if not self.simulate:
            subprocess.call("sudo modprobe g_mass_storage -r", shell=True)
        self.is_usb_mounted = False

    def get_local_files(self) -> list:
        """Get files in local folder

        Returns
        -------
        list
            List of files in local mount directory
        """
        return get_file_list(self.watch_dir)


def get_new_files(files_before: list, files_after: list) -> list:
    return [f for f in files_after if f not in files_before]


def main():

    if sys.version_info[0] < 3:
        raise Exception("Must be using Python 3!")

    parser = argparse.ArgumentParser(
        description="Monitor for new files, and print them"
    )
    parser.add_argument("config_file", help="Config file")
    args = parser.parse_args()

    with open(args.config_file) as f:
        config_data = yaml.safe_load(f)

    logger.info("Starting Scope printer service")

    vfd = VirtualFlashDrive(
        local_mount_dir=config_data["local_mount_dir"],
        watch_dir=config_data["watch_dir"],
        binary_file=config_data["binary_file"],
        simulate=config_data["simulate"],
    )

    # Try to connect to printer, and clear out print queue

    ph = PrinterHelper()
    printer_found = ph.find_printer()
    if not printer_found:
        logger.error("Unable to find a printer!")
        sys.exit(1)

    logger.info("Clearing print queue...")
    subprocess.call("cancel -a", shell=True)

    # TODO: Mount locally, and clear out EVOS folder, then unmount
    vfd.mount_local()
    logger.info("Removing all existing images")
    if not config_data["simulate"]:
        subprocess.call(f"rm {vfd.watch_dir}/*.jpg", shell=True)
    vfd.unmount_local()

    # Now mount the USB side of the system so flash drive appears to scope
    vfd.mount_USB()

    files_before = vfd.get_local_files()

    while 1:
        logger.debug("Waking up!")
        vfd.mount_local()
        files_after = vfd.get_local_files()

        addedFiles = get_new_files(files_before, files_after)
        logger.debug(f"Found {len(addedFiles)} new files.")

        # TODO: sort by modified date?
        # Only print the first picture in new list, to avoid spamming
        if len(addedFiles) >= 1:
            vfd.unmount_USB()
            logger.debug(f"Going to try to print {addedFiles[0]}")
            ph.print_picture(os.path.join(vfd.watch_dir, addedFiles[0]))

            vfd.unmount_local()  # unmount local
            vfd.mount_USB()  # mount USB
        else:
            logger.debug("No new pictures.")
            vfd.unmount_local()  # unmount local

        files_before = files_after

        time.sleep(config_data["check_interval_sec"])


def test_get_new_files():

    assert ["a"] == get_new_files([], ["a"])
    assert ["a", "b"] == get_new_files([], ["a", "b"])
    assert [] == get_new_files(["a", "b"], ["a", "b"])
    assert ["c"] == get_new_files(["a", "b"], ["a", "b", "c"])
    assert ["c"] == get_new_files(["a", "b"], ["c"])


if __name__ == "__main__":
    main()
