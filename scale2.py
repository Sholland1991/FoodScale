#!python2

import sys

#LOADCELL
loadcell_dr = 5
loadcell_sck = 6

import RPi.GPIO as GPIO
import time
from hx711 import HX711
hx = HX711(loadcell_dr,loadcell_sck)
hx.set_reading_format("LSB","MSB")

hx.set_reference_unit(-410)

def cleanAndExit():
    print ("Cleaning")
    GPIO.cleanup()
    sys.exit()

hx.reset()
hx.tare()

#CAMERA
from picamera import PiCamera
camera = PiCamera()
from time import sleep

import csv
import datetime

#NFC
import binascii
import sys

import Adafruit_PN532 as PN532
CS   = 18
MOSI = 23
MISO = 24
SCLK = 25
pn532 = PN532.PN532(cs=CS, sclk=SCLK, mosi=MOSI, miso=MISO)
pn532.begin()
ic, ver, rev, support = pn532.get_firmware_version()
pn532.SAM_configuration()

#Sheet Upload
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
GDOCS_OAUTH_JSON       = 'scale-data-uploa-1538438346380-a75d1ad2713c.JSON'
GDOCS_SPREADSHEET_NAME = 'SCALEData'

def login_open_sheet(oauth_key_file, spreadsheet):
    """Connect to Google Docs spreadsheet and return the first worksheet."""
    try:
        scope =  ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print('Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)

worksheet = None

#GOOGLE DRIVE FOLDER ID
fid ='11n-Owqd8uCoQB14_yOt0jzVShN1881YZ'

#Button:
button_pin = 21
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


#MAIN LOOP
print('Waiting')

while True:
        uid = pn532.read_passive_target(timeout_sec=1000)
        if uid is None:
            continue

        tag = str(format(binascii.hexlify(uid)))
        print('On Scale')
        print('Found card with UID: 0x{0}'.format(binascii.hexlify(uid)))

        mass = max(0,int(hx.get_weight(5))) #read mass from scale. cannot be less than 0
        plate_id = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") #create timestamp

        with open('data.csv','a') as f: #open data.csv and add data
            writer = csv.writer(f, delimiter=' ')
            writer.writerow([plate_id,",",tag,",",mass])

            img_name = "/home/pi/Scale/img/"+ plate_id +".jpg"

            print('Capturing Image')
            camera.capture(img_name)
            camera.stop_preview()


        if worksheet is None:
            worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)
        try:
            worksheet.append_row((plate_id, tag, mass, datetime.datetime.now().strftime("%m/%d/%Y"),datetime.datetime.now().strftime("%H:%M:%S")))
            print('Upload Complete')
        except:
            # Error appending data, most likely because credentials are stale.
            # Null out the worksheet so a login is performed at the top of the loop.
            print('Append error, logging in again')
            worksheet = None
            time.sleep(5)
            continue

        print ([plate_id,tag,mass])

        hx.power_down()
        hx.power_up()
        sleep(.5)

        print ('Waiting')

#    except (KeyboardInterrupt, SystemExit):
 #       cleanAndExit()

