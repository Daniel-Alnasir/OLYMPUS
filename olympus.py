import time
import json
from datetime import datetime, timedelta
import traceback
import logging, sys
import hmac
import sh
from pathlib import Path

USERS_PATH="data/offline_json.json"
LOG_PATH="data/logs/olympus.log"

#level = logging.DEBUG
level = logging.INFO
logging.basicConfig(level=level)
logger = logging.getLogger("olympus")
logging.getLogger("sh").setLevel(logging.WARNING) # silence sh's commands on INFO level
#logger.addHandler(sys.stdout)
# python3 olympus.py --log=debug  # to try different level # not in code

import functools
def debug(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__}()")
        result = func(*args, **kwargs)
        return result
    return wrapper

import qrcode
logger.debug("finished imports for std lib")

#import custom packages
#TODO test the below imports with an esp
# import board
# import digitalio
# from digitalio import DigitalInOut
# from adafruit_pn532.i2c import PN532_SPI

import Check_Gsheet_UID
import Read_MFRC522
import Get_Buttons
import Pi_to_OLED
logger.debug("finished imports for custom")

import firebase_admin
from firebase_admin import credentials, db
#https://console.firebase.google.com/u/0/project/noisebridge-rfid-olympus/
#https://www.freecodecamp.org/news/how-to-get-started-with-firebase-using-python/
#https://firebase.google.com/docs/database/security/get-started?hl=en&authuser=2
# Circuit Python port for MFRC522 https://github.com/domdfcoding/circuitpython-mfrc522

#TODO: change firebase rules so that Members can only add guests and memebrs
#TODO: change firebase so guests to only view their experation date
logger.debug("finished imports for firebase")
logger.debug("finished imports")

# Add an authorized UID to the database
level_3 = "Gods"
level_2 = "Members"
level_1 = "Guests"

#ref.child('Mytikas').child(level_3).set({"uid":"08174ab9"})

# Retrieve authorized UIDs from the database
#authorized_uids = ref.child('Mytikas').get()
#print("Authorized UIDs:", authorized_uids)

local_cache = {}

@debug
def strike_the_door():
    print("Striking the door")
    logger.info("Striking the door")
    Pi_to_OLED.OLED_off(7)
    Pi_to_OLED.New_Message("Striking the door")
    
    Get_Buttons.set_pin(20, True)
    time.sleep(6)
    Get_Buttons.set_pin(20, False)

@debug
def uid_is_valid(UID, cache):
    #Check cache if the UID exists, else check the server
    #print("Checking Validity")
    logger.debug("Checking Validity")
    
    def not_expired(card):
        #print("Checking Expiration")
        logger.debug(f"Checking Expiration")
        present_date = datetime.now()
        present_unix_timestamp = datetime.timestamp(present_date)*1000
        end_unix_date = card["expire_date"]
        is_valid_now = (present_unix_timestamp < end_unix_date or end_unix_date == 0)
        logger.info(f"Expiration, {is_valid_now=}: {present_date=} < {card['exp']=}")
        return is_valid_now
            
    
    card = cache.get(UID)
    if card:
        print("Card is found in cache")
        logger.info("Card is found in cache")
        if not_expired(card):
            return True
    else:
        return False
  
@debug
def rewrite_user_dict(users):
    rewrite_json(json.dumps(users))

@debug
def rewrite_json(new_json):
    if not new_json:
        raise ValueError("tried to write nothing")
    logger.debug(f"{new_json=}")
    with open(USERS_PATH, "w") as f:
        f.write(new_json)

@debug
def load_json():
    with open(USERS_PATH, "r") as f:
        user_dict = json.loads(f.read())
        return user_dict        

@debug
def add_uid(mentor_UID, new_UID, mentor_clearance_level, prodigy_clearance_level, user_dict):
    #Adds a user to the server
    print("Adding User")
    logger.info("Adding User")
    #send_user_message("Adding User")
    #TODO test this part
    current_time = datetime.now()
    current_unix_timestamp = datetime.timestamp(current_time)*1000


    if (mentor_clearance_level == level_2) or (mentor_clearance_level == level_3):
        if (prodigy_clearance_level == level_2) or (mentor_clearance_level == level_3):
            # member
            new_tag_data = {
                'clearance': prodigy_clearance_level,  # Replace with your actual tag ID
                'expire_date': 0,
                'issue_date': current_unix_timestamp,
                'exp': "NA",
                'iss': str(current_time),
                'uid': new_UID,
                'user_handle': "",
                'mentor': mentor_UID
            }
        elif prodigy_clearance_level == level_1:
            # 30 day
            expiration_time = current_time + timedelta(days=30)
            expiration_unix_timestamp = datetime.timestamp(expiration_time)*1000
            new_tag_data = {
                'clearance': prodigy_clearance_level,  # Replace with your actual tag ID
                'expire_date': expiration_unix_timestamp,
                'issue_date': current_unix_timestamp,
                'exp': str(expiration_time),
                'iss': str(current_time),
                'uid': new_UID,
                'user_handle': "",
                'mentor': mentor_UID
            }
        
        #New User getting added to either big M or guests
        new_user = { new_tag_data['uid']: new_tag_data }
        if new_tag_data['uid'] not in user_dict:
            user_dict.update(new_user)
            rewrite_user_dict(user_dict)
        
            print("Added User", new_UID, "to", prodigy_clearance_level)
            logger.info(f"Added User {new_UID} to {prodigy_clearance_level}")
            send_log(("Added Acess from " + mentor_UID + " to " + new_UID + " at " + str(datetime.now())))
            
            Pi_to_OLED.New_Message("New User: Please Scan QR Code (25s)")
            time.sleep(2)
            Pi_to_OLED.New_UID_QR_Image(new_UID)
            time.sleep(23)
            Pi_to_OLED.OLED_off(1)
            return user_dict
        
        #Guest getting upgraded to big M
        elif (new_tag_data['clearance'] == level_2) and (new_tag_data['uid'] in user_dict):
            user_dict.update(new_user)
            rewrite_user_dict(user_dict)
            print("Added User", new_UID, "to", prodigy_clearance_level)
            logger.info(f"Added User {new_UID} to {prodigy_clearance_level}")

            Pi_to_OLED.New_Message("30 Day Member ---> Big M")
            Pi_to_OLED.OLED_off(5)
            return user_dict
        
        #Guest getting a 30 day refreshed
        elif (new_tag_data['clearance'] == level_1) and (new_tag_data['uid'] in user_dict):
            user_dict.update(new_user)
            rewrite_user_dict(user_dict)
            print("Added User", new_UID, "to", prodigy_clearance_level)
            logger.info(f"Added User {new_UID} to {prodigy_clearance_level}")
            Pi_to_OLED.OLED_off(3)
            Pi_to_OLED.New_Message(f"30 Days refreshed, expires on {new_tag_data['exp']}")
            time.sleep(1)
            Pi_to_OLED.OLED_off(1)
            return user_dict           


        #This UID already has this level of access
        elif (new_tag_data['uid'] in user_dict) and (new_tag_data['clearance'] == user_dict['uid']['clearance']):
            print("User a", new_UID, "to", prodigy_clearance_level)
            logger.info(f"User {new_UID} already present as {user_dict[new_tag_data['uid']]}")
            Pi_to_OLED.OLED_off(3)
            Pi_to_OLED.New_Message("This user already has this level of access")
            time.sleep(1)
            return False
        
        #Uncaught case, probably an error
        else:    
            logger.info(f"User {new_UID} already present as {user_dict[new_tag_data['uid']]}")
            Pi_to_OLED.OLED_off(3)
            Pi_to_OLED.New_Message("There was an error, please contact the access control gods")
            time.sleep(5)
            return False
    
    else:
        print("Only big M Members can do this action")
        logger.info("Only big M Members can do this action")
        Pi_to_OLED.OLED_off(3)
        Pi_to_OLED.New_Message("Only big M Members can add access")
        time.sleep(1)

@debug
def send_log(log):
    #Inform sever of unauthorized scanning, succesful scanning, and give a time stamp, inform of users added and by whom
    #ref.child('Ourea').push().set(log)
    with open(LOG_PATH, "a+") as log_file:
        print(log, file=log_file)

@debug
def read_user_action(switch, button):
    #reads state of buttons to determine whether we are adding a guest or Big M Member
    #TODO test the reading of these buttons
    #TODO investigate the use of https://docs.python.org/3/library/signal.html

    if switch and button:
        return level_2
    else:
        return level_1       
       
@debug
def look_up_clearance_level(card_uid, cache):
    #formatted_UID = f'"{card_uid}"'
    card = cache.get(card_uid)
    if card:
        clearance = card.get('clearance')
        return clearance
    else:
        logger.info(f"error card id {card_uid} returns {card}")
        logger.info(f"{cache=}")

@debug
def generate_QR(new_UID):
    url = f"https://docs.google.com/forms/d/e/1FAIpQLSdXIPnJPoPdBreH9FOQjW-s5nUuZ4QHThNK59u3kmUDplx3Bg/viewform?usp=pp_url&entry.181306502={new_UID}"
    return

@debug
def main():
    user_dict = load_json()
    logger.debug("Done caching")

    Pi_to_OLED.OLED_off(3)
    Pi_to_OLED.New_Message("REBOOTED and READY (3s)")
    
    count = 0
    activity_pin = True
    while True:
        time.sleep(.1)

        if count % 10 == 0:
            Get_Buttons.set_pin(16, activity_pin)
            activity_pin = not activity_pin
        count += 1

        card_uid = Read_MFRC522.Read_UID()
        logger.debug(f"{card_uid=}")	
        
        switch, button = Get_Buttons.read()
        
        clearance = look_up_clearance_level(card_uid, user_dict)
        
        is_valid = uid_is_valid(card_uid, user_dict)
        logger.info(f"{card_uid=} {is_valid=} {switch=} {button=}") # log every scan (incl valid & switch/button state)


        #Easter Egg
        if not card_uid and button:
            time.sleep(.5)
            switch, button = Get_Buttons.read()
            
            if button:
                Pi_to_OLED.New_Message("HACK THE PLANET!")
                Pi_to_OLED.OLED_off(4)
            

        if card_uid and is_valid and not switch:
            print(switch, button)
            logger.info(f"{switch=} {button=}")
            strike_the_door()
            Pi_to_OLED.New_Message(f'Your access expires on {user_dict[card_uid]["exp"]}')
            time.sleep(1)
            Pi_to_OLED.OLED_off(3)
            time.sleep(1)
            send_log(("Opened door to "+card_uid+" at "+str(datetime.now())))
        
        elif card_uid and is_valid and (switch == True) and ((clearance == level_2) or (clearance == level_3)):
            #TODO provide some feedback that we are going into a special mode here to add users
            
            Pi_to_OLED.New_Message("SUDO engaged")
            Pi_to_OLED.OLED_off(100)
            time.sleep(1)
            Pi_to_OLED.New_Message("If adding a big M, hold down the red button")
            time.sleep(5)
            switch, button = Get_Buttons.read()
            prodigy_level = read_user_action(switch,button)
            if prodigy_level == level_2:
                Pi_to_OLED.New_Message("BIG M selected")
                time.sleep(2)
            mentor_clearance = look_up_clearance_level(card_uid, user_dict)
            
            Pi_to_OLED.New_Message("Place new member card on the reader now")
            new_UID = Read_MFRC522.Read_UID(30, card_uid)
            
            if new_UID != "":
                tmp = add_uid(card_uid, new_UID, mentor_clearance, prodigy_level, user_dict)
                if tmp:
                    user_dict = tmp
                    # send_log(("Added Acess from " + card_uid + " to " + new_UID + " at " + str(datetime.now())))
                    # Pi_to_OLED.New_Message("New User: Please Scan QR and enter name (25s)")
                    # Pi_to_OLED.New_UID_QR_Image(new_UID)
                    # time.sleep(25)
                    # Pi_to_OLED.OLED_off(1)
                else:
                    #send_log(f"Added Acess from {card_uid}  to {new_UID} at {str(datetime.now()}")
                    #Pi_to_OLED.New_Message(f"Existing user with {user_dict[card_uid]['clearance']} role")
                    Pi_to_OLED.New_Message(f"Error adding user with {user_dict[card_uid]['clearance']} role")
                    time.sleep(8)
                    Pi_to_OLED.OLED_off(1)
                    
            else:
                print("Card reading timed out")
                logger.info("Card reading timed out")
                Pi_to_OLED.OLED_off(5)
                Pi_to_OLED.New_Message("Reading timed out, Mifare NFC tags only")
                time.sleep(3)
                
        
        elif card_uid and is_valid and (switch == True) and (clearance == level_1):
            print("Need Big M to do this")
            logger.info("Need Big M to do this")
            Pi_to_OLED.New_Message("Need a Big M to do this, please turn switch off")
            Pi_to_OLED.OLED_off(5)
            time.sleep(2)
        
        elif card_uid and not is_valid:

            logger.info("Access expired")
            Pi_to_OLED.New_Message(f'Your 30 access expired on {user_dict[card_uid]["exp"]}')
            time.sleep(1)
            Pi_to_OLED.New_Message('Please renew access by talking to a big M Member')
            Pi_to_OLED.OLED_off(5)
            time.sleep(5)
        
        elif card_uid:
            print("Access Denied")
            logger.info("Access Denied")
            Pi_to_OLED.New_Message(f"Access Denied: whois {card_uid}")
            Pi_to_OLED.OLED_off(3)
            time.sleep(2)
            send_log(("Denied Access to " + card_uid + " at "+str(datetime.now())))
        else:
            continue
    
if __name__ == "__main__":
    try:
        file_version = sh.git("hash-object","./olympus.py").strip()
        logger.info(f"starting log: {level=}, version: {file_version} (git hash-object ./olympus.py)")
        main()
    except Exception:
        print(traceback.format_exc())
        error_message = traceback.format_exc()
        error_first = error_message[40:]
        error_last = error_message[-40:-1]
        Pi_to_OLED.New_Message(error_first)
        time.sleep(4)
        Pi_to_OLED.OLED_off(5)
        Pi_to_OLED.New_Message(error_last)
        time.sleep(4)
        Pi_to_OLED.OLED_off(5)
        logger.error(traceback.format_exc())
        main()
