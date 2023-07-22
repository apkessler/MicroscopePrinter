#!/usr/bin/python3

"""
Look for new microscope files, and print them
"""
import argparse
import sys
from datetime import datetime
import os, time
import subprocess
import cups
from loguru import logger


WATCH_DIR = "/mnt/usb_share/EVOS"

def get_file_list(path:str):
    return dict ([(f, None) for f in os.listdir (path)])

def print_picture(filename:str):
    """
        Send the given filename to the printer to print.
    """
    logger.info(f"Printing {filename}...")
    sts = subprocess.run(["lp", filename], capture_output=True)
    if (sts.returncode == 0):
        #If successful, lp will print b'request id is <job-id> (1 file(s))\n'
        jobId = (sts.stdout.decode('utf-8').split())[3]
        logger.info(f"Started {jobId=}")
    else:
        logger.error(f"lp error {sts.returncode}!: {sts.stderr.decode('utf-8')}")

    #Now wait for job to complete
    status = ''
    while (status != 'idle.'): #TODO: This is a bit hacky, but it works.
        time.sleep(2)
        sts = subprocess.run(['lpstat','-p'], capture_output=True)
        status = (sts.stdout.decode('utf-8').split())[3]
        logger.info(status)

    logger.success(f"Done printing {filename}!")


def mount_USB(is_fake:bool):
    """
        Mount the USB drive (virtually plug in)
    """

    logger.info("Mounting USB side")

    if (not is_fake):
        subprocess.call("sudo modprobe g_mass_storage file=/piusb.bin stall=0 ro=0 removeable=1", shell=True)


def unmount_USB(is_fake:bool):
    """
        Unmount the USB drive (virtually unplug)
    """

    logger.info("Unmounting USB side")

    if (not is_fake):
        subprocess.call("sudo modprobe g_mass_storage -r", shell=True)


def mount_local(is_fake:bool):
    """
        Mount the mirror of the shared memory on the local file system.
    """

    logger.info("Mounting local side.")
    if (not is_fake):
        subprocess.call("sudo mount -a", shell=True)




def unmount_local(isFake):
    """
        Unmount the mirror of the shared memory on the local system.
    """
    logger.info("Unmounting local side.", flush=True)
    if (not isFake):
        subprocess.call("umount /mnt/usb_share", shell=True)

def get_new_files(files_before:list, files_after:list) -> list:
   return [f for f in files_after if f not in files_before]

def main():

    if sys.version_info[0] < 3:
        raise Exception("Must be using Python 3!")

    parser = argparse.ArgumentParser(description='Monitor for new files, and print them')
    parser.add_argument('-f','--fake', default=False, action='store_true', help="Do not make OS calls.")
    parser.add_argument('-t','--test', default=None, help="Test printing given file")
    args = parser.parse_args()

    logger.info("Starting Scope printer service")

    #Try to connect to printer, and clear out print queue
    conn = cups.Connection()
    printers = conn.getPrinters()
    if (len(printers) == 0):
        logger.error("No printers found!")
        sys.exit(1)
    else:
        for prntr in printers:
            print("Found %s" % prntr, flush=True)
        #TODO: explicitly select first?

    if (args.test):
        print_picture(args.test)
        sys.exit()

    #For now, just move forward with default
    logger.info("Clearing print queue...")
    subprocess.call("cancel -a", shell=True)



    #TODO: Mount locally, and clear out EVOS folder, then unmount
    mount_local(args.fake)
    logger.info("Removing all existing images")
    if (not args.fake):
        subprocess.call(f"rm {WATCH_DIR}/*.jpg", shell=True)
    unmount_local(args.fake)



    #Now mount the USB side of the system so flash drive appears to scope
    mount_USB(args.fake)


    files_before = get_file_list(WATCH_DIR)

    while 1:
        logger.debug("Waking up!")
        mount_local(args.fake)
        files_after = get_file_list(args.pathToWatch)

        addedFiles = get_new_files(files_before, files_after)
        logger.debug(f"Found {len(addedFiles)} new files.")

        #TODO: sort by modified date?
        #Only print the first picture in new list, to avoid spamming
        if (len(addedFiles) >= 1):
            unmount_USB(args.fake)
            logger.debug(f"Going to try to print {addedFiles[0]}")
            print_picture(os.path.join(WATCH_DIR,addedFiles[0]))

            unmount_local(args.fake) #unmount local
            mount_USB(args.fake) #mount USB
        else:
            logger.debug("No new pictures.")
            unmount_local(args.fake) #unmount local

        files_before = files_after

        time.sleep(5)


def test_get_new_files():

    assert ['a'] == get_new_files([], ['a'])
    assert ['a', 'b'] == get_new_files([], ['a', 'b'])
    assert [] == get_new_files(['a', 'b'], ['a','b'])
    assert ['c'] == get_new_files(['a', 'b'], ['a','b', 'c'])
    assert ['c'] == get_new_files(['a', 'b'], ['c'])


if __name__ == "__main__":
    main()
