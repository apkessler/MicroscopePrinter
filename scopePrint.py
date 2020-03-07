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

def getFileList(path):
    return dict ([(f, None) for f in os.listdir (path)])

def printPicture(fileName):
    """
        Send the given filename to the printer to print.
    """
    print("Printing %s..." % fileName, flush=True)
    sts = subprocess.run("lp %s" % fileName, shell=True, capture_output=True)
    #sts = subprocess.run(["pwd"], shell=True, capture_output=True)    
    print(sts.stdout, flush=True)
    time.sleep(1)
    print("...done!", flush=True)
    #TODO: should wait for printer to be done
    

def mountUSB(isFake):
    """ 
        Mount the USB drive (virtually plug in)
    """

    print("Mounting USB side!", flush=True)
    if (not isFake):
   sts = subprocess.call("sudo modprobe g_mass_storage file=/piusb.bin stall=0 ro=0 removeable=1", shell=True)
    print(sts)

def unmountUSB(isFake):
    """
        Unmount the USB drive (virtually unplug)
    """
    
    print("Unmounting USB side.", flush=True)
    sts = subprocess.call("sudo modprobe g_mass_storage -r", shell=True)
    print(sts)

def mountLocal(isFake):
    """
        Mount the mirror of the shared memory on the local file system.
    """
    
    print("Mounting local side.", flush=True)
#    sts = subprocess.call("sudo mount -a", shell=True)
    sts = subprocess.call("sudo mount -t vfat /piusb.bin /mnt/usb_share -r")
    print(sts)    



def unmountLocal(isFake):
    """ 
        Unmount the mirror of the shared memory on the local system.
    """
    print("Unmounting local side.", flush=True)
    sts = subprocess.call("umount /mnt/usb_share", shell=True)
    print(sts)
 
def main():

    if sys.version_info[0] < 3:
        raise Exception("Must be using Python 3!")

    parser = argparse.ArgumentParser(description='Monitor for new files')
    parser.add_argument('-p','--pathToWatch', default='/mnt/usb_share/EVOS/', description="Path to watch for new files")
    parser.add_argument('-f','--fake', type=boolean, default=False, action='store_true', description="Do not make OS calls.")
    args = parser.parse_args()


    print("Running! Press Ctrl+c to quit at any time.", flush=True)

    #Try to connect to printer, and clear out print queue
    conn = cups.Connection()
    printers = conn.getPrinters()
    if (len(printers) == 0):
        print("No printers found!", flush=True)
        sys.exit()
    else:
        for prntr in printers:
            print("Found %s" % prntr, flush=True)
        #TODO: explicitly select first?

    #For now, just move forward with default
    print("Clearing print queue...", flush=True)
    subprocess.call("cancel -a", shell=True)    

    

    #TODO: Mount locally, and clear out EVOS folder, then unmount

    #Now mount the USB side of the system so flash drive appears to scope
    mountUSB()


    filesBefore = getFileList(args.pathToWatch)
    try:
        while 1:
            print("\nWaking up!", flush=True)
            mountLocal(args.fake)
            filesAfter = getFileList(args.pathToWatch)

            addedFiles = [f for f in filesAfter if not f in filesBefore]
            print("Added files: " + ", ".join(addedFiles), flush=True)

            #TODO: sort by modified date
            if (len(addedFiles) >= 1):
                unmountUSB(args.fake)
                print("Going to try to print %s!" % addedFiles[0])
                printPicture(addedFiles[0])

                unmountLocal(args.fake) #unmount local
                mountUSB(args.fake) #mount USB
            else:
                print("No new pictures.", flush=True)
                unmountLocal(args.fake) #unmount local

            filesBefore = filesAfter


            time.sleep(5)

    except KeyboardInterrupt:
        print ("Ending!", flush=True)
        sys.exit()


if __name__ == "__main__":
    main()
