#!/usr/bin/env python
#https://pimylifeup.com/raspberry-pi-rfid-rc522/
#sudo pip3 install mfrc522

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from mfrc522 import BasicMFRC522
from mfrc522 import MFRC522
import time

from datetime import datetime, timedelta

import logging
level = logging.INFO
logging.basicConfig(level=level)
logger = logging.getLogger("mfrc522")
logger.debug("Starting reader")


#advanced = MFRC522()

def Read_UID(tries = 2, mentor_uid = None):
    reader = SimpleMFRC522()
    for i in range(0, tries):
        try:
            #uid, text = reader.read()
            #uid1 = reader.read_id()

            #id = self.BasicMFRC522.read_id_no_block()
            uid1 = BasicMFRC522.read_id_no_block()
    

            if (uid1 != None) and (uid1 != mentor_uid):
                uid = str(hex(int(uid1)))
                logger.debug(uid)
                return(uid)

        except Exception as e:
                logger.error(e)
    return None

def main():
    while True:
        Read_UID()

if __name__ == "__main__":
    main()
