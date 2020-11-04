import time
import subprocess
import sensors
import configparser
import elevate
import syslog
import atexit

sensors.init()
config = configparser.ConfigParser()
elevate.elevate()
config.read('IPMI-config.ini')

def getHottestCore():
    highest = -1
    for chip in sensors.iter_detected_chips():
        for feature in chip:
            if(feature.get_value() > highest):
                highest = feature.get_value()
    return highest

def cleanup():
    subprocess.run("/usr/bin/ipmitool raw 0x30 0x30 0x01 0x01", shell=True)
    syslog.syslog("Fan controller exiting")
atexit.register(cleanup)

try:
    #Initial Sanity Check
    maxTemp = getHottestCore()

    if maxTemp == -1:
        cleanup()
        raise Exception("Failed to read temperature data.")

    if maxTemp > int(config['CONFIG']['cutoutTemp']) or maxTemp <= int(config['CONFIG']['errorTemp']):
        cleanup()
        raise Exception("Temperature outside of config limits! Returning to automatic fan control.")

    #Take Manual Control
    subprocess.run("/usr/bin/ipmitool raw 0x30 0x30 0x01 0x00", shell=True)

    #Main Loop
    while True:
        #Check Temperatures
        maxTemp = getHottestCore()

        #Sanity and Safety Checks
        if maxTemp == -1:
            subprocess.run("/usr/bin/ipmitool raw 0x30 0x30 0x01 0x01", shell=True) #Restore Auto
            raise Exception("Failed to read temperature data.")

        if maxTemp > int(config['CONFIG']['cutoutTemp']):
            subprocess.run("/usr/bin/ipmitool raw 0x30 0x30 0x01 0x01", shell=True) #Restore Auto
            raise Exception("Temperature above set maximum! Returning to automatic fan control.")

        #Get Appropriate Fan Percentage
        fanspeed = config['CONFIG']['speedStage1']

        if (maxTemp > int(config['CONFIG']['tempStage1'])):
            fanspeed = config['CONFIG']['speedStage2']

        if (maxTemp > int(config['CONFIG']['tempStage2'])):
            fanspeed = config['CONFIG']['speedStage3']

        #Send it to ipmi
        subprocess.run("/usr/bin/ipmitool raw 0x30 0x30 0x02 0xff 0x" + fanspeed, shell=True)

        syslog.syslog("Temperature Read: " + str(maxTemp) + " Fan Speed: " + str(fanspeed))

        #wait
        time.sleep(2)

except Exception as e:
    print("Oof, we encountered an error:")
    print(e)
    cleanup()
