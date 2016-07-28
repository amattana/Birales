#!/usr/bin/env python
"""
Setup the Jack's F-engine and X-engine correlator to calibrate the BEST-2 Array 

 
"""

import numpy,struct
import logging
import logging.handlers
import os,sys
import time, datetime
import socket

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

BASE_PATH = "/mnt/"
BUFFER_SIZE = 1024
BEST2_POINTING_ADDR = "127.0.0.1"
BEST2_POINTING_PORT = 7200

BEST2_POINTING_CURVE = [[0.0, 0],[28.5,163],[46.6,263]]

BACKEND_CALIB_CONFIG = "/home/lessju/Working/feng_xeng_calib.xml"
BACKEND_SOURCE_PATH  = "/home/lessju/Code/medicina/poxy/config/src/"

WEATHER_SCRIPT = "./birales_get_temp.py -v -n"
RECEIVERS_SCRIPT = "./birales_equalize_rx.py -v "

def gps2dec(angolo):
    g, p, s = angolo.strip().split(":")
    return '%3.1f'%(float(g)+(((float(s)/60)+float(p))/60))

def eq_retta(x1,y1,x2,y2):
    m=float(y2-y1)/(x2-x1)
    q=y1-(m*x1)
    def retta(x):
        return m*x + q
    return retta

def time2move(val):
    for i in range(len(BEST2_POINTING_CURVE)):
        if BEST2_POINTING_CURVE[i][0] > val:
            break
    if i>0:
        r= eq_retta(BEST2_POINTING_CURVE[i][0],BEST2_POINTING_CURVE[i][1],BEST2_POINTING_CURVE[i-1][0],BEST2_POINTING_CURVE[i-1][1])
    else: 
        r= eq_retta(BEST2_POINTING_CURVE[1][0],BEST2_POINTING_CURVE[1][1],BEST2_POINTING_CURVE[0][0],BEST2_POINTING_CURVE[0][1])
    return r(val)


#Setting up logging    
log_filename = "log/best2_calib.log"
logger = logging.getLogger('DataLogger')
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s", "%Y/%m/%d_%H:%M:%S")
logging.Formatter.converter = time.gmtime
console_log = logging.StreamHandler()
console_log.setFormatter(formatter)
file_log = logging.handlers.RotatingFileHandler(log_filename, maxBytes=8388608, backupCount=5)
file_log.setFormatter(formatter)
logger.addHandler(console_log)
logger.addHandler(file_log)

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('birales_calib.py [options]')
    p.set_description(__doc__)
    p.add_option('-s', '--source', dest='source',default="cyg",
        help='Choose a RadioSource between: \'cyg\', \'casa\', \'tau\' and \'virgo\'')
    p.add_option('-t', '--acqtime', dest='acqtime', default=20, type='float',
        help='How many minutes of data to collect.  Default: 20 (minutes)')
    p.add_option('-n', '--now', dest='now',action='store_true', default=False, 
        help='Do not wait for the transit time')
    p.add_option('-m', '--move', dest='move',action='store_true', default=False, 
        help='Do not move the antenna')

    p.add_option('-v', '--verbose', dest='verbose',action='store_true', default=False, 
        help='Be verbose about errors.')
    opts, args = p.parse_args(sys.argv[1:])

    logger.info("========================================================")
    logger.info("Starting the program with options:")
    logger.info("\t- Do not wait for transit: " + str(opts.now))
    logger.info("\t- Source: " + str(opts.source))
    logger.info("\t- Acq Time: " + str(opts.acqtime))
    
    if opts.source.count(",") > 0:
        sources = opts.source.split(",")
    
    index=0
    while index < len(sources):
        
        # Checking the transit time of the source
        logger.info("Checking the transit time of the source: "+sources[index])
        ans=os.popen('./calib_source.py -r '+sources[index]).read()
        source=ans.split('\n')
        source.pop(len(source)-1)
    
        for i in source:
            if i.split()[1]==sources[index]:
                transit_utc = i.split()[11]+" "+i.split()[12]
                transit_ra  = i.split()[4]
                transit_dec = float(gps2dec(i.split()[6]))
                logger.info("\t- Transit time: %s (UTC), RA: %s, DEC: %3.1f"%(transit_utc, transit_ra, transit_dec))
                transit_utc = datetime.datetime.strptime(transit_utc, "%Y/%m/%d %H:%M:%S")
            else:
                logger.error("Radiosource not found!")
                exit()
        logger.info("SOURCE \'"+sources[index]+"\' transits in "+str(((transit_utc - datetime.datetime.utcfromtimestamp(time.time()))/60).seconds)+" minutes")

        # Wait for 90 minutes before the transits to point the antenna
        while (((transit_utc - datetime.datetime.utcfromtimestamp(time.time()))/60).seconds > 90 ) and opts.now == False:
            time.sleep(60)

        # Point the antenna to source declination
        if opts.move == False:
            pointing = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pointing.connect((BEST2_POINTING_ADDR, BEST2_POINTING_PORT))
            pointing.settimeout(60)
            pointing.sendall("best")
            time.sleep(2)
            starting_time = datetime.datetime.utcfromtimestamp(time.time())
            starting_pos = pointing.recv(BUFFER_SIZE)
            logger.info("BEST-2 Actual Declination: "+starting_pos)
            if abs(float(starting_pos)-transit_dec) > 1:
                logger.info("BEST-2 Moving the antennas to: "+str(transit_dec))
                expected_time = starting_time+datetime.timedelta(0,time2move(abs(float(starting_pos)-transit_dec)))
                # Fixed time for safety check and alarms before to move + extra delay
                logger.info("Pointing requires: "+"%3.1f"%(time2move(abs(float(starting_pos)-transit_dec))+30)+" seconds")
                #expected_time += datetime.timedelta(0,25+5)            
                logger.info("Antenna expected on source at: "+expected_time.strftime("%H:%M:%S (UTC) of %Y/%m/%d"))
                pointing.sendall("best "+str(transit_dec))
                time.sleep((expected_time-starting_time).seconds)
                try:
                    data = pointing.recv(BUFFER_SIZE)
                    if data == "ONSOURCE":
                        time.sleep(1)
                        pointing.sendall("best")
                        time.sleep(1)
                        data = pointing.recv(BUFFER_SIZE)
                        if abs(float(starting_pos)-float(data)) > 0.3:
                            logger.info("Antenna pointed at declination "+data)
                        else:
                            logger.error("Antenna pointed at declination "+data+", expected to be at "+str(transit_dec))
                except:
                    logger.error("Socket Timeout occurred! Maybe the 380 Volt breaker was down!")
            else:
                logger.info("BEST-2 current position is within 1 deg wrt source dec, leaving as it is")
        


        # Creating the directory where the hdf5 data will be stored
        data_dir = BASE_PATH+"%04d/%02d-%02d/%s"%(transit_utc.year,transit_utc.month,transit_utc.day,str(sources[index]))
        logger.info("Creating directory: "+data_dir)
        if not os.path.exists(data_dir):
            try:
                os.makedirs( data_dir, 0755 )
            except:
                print "ERROR creating dir"
        os.chdir(data_dir)

        # Creating Log files
        feng_log = str(datetime.datetime.utcfromtimestamp(time.time())).split()[0]+"_feng_"+sources[index]+".log"
        xeng_log = str(datetime.datetime.utcfromtimestamp(time.time())).split()[0]+"_xeng_"+sources[index]+".log"
        logger.info("\t- F-engine Log File: " + feng_log)
        logger.info("\t- X-engine Log File: " + xeng_log)

        # Starting the calibration backend
        logger.info("Starting F-engine")
        os.system("feng_init.py -s "+BACKEND_CALIB_CONFIG+" > "+feng_log)
        logger.info("Starting X-engine")
        os.system("xeng_init.py  "+BACKEND_CALIB_CONFIG+" > "+xeng_log)

        # Starting the Server on the right place
        logger.info("Starting the SPEAD Rx Server")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 7210))
        socket_string=("start "+data_dir+" "+BACKEND_CALIB_CONFIG+" "+str(opts.acqtime))
        #logger.info("\t- "+socket_string)
        s.sendall(socket_string)
        ans = s.recv(BUFFER_SIZE)
        if ans.count("OK") == 0: # An error occurred while starting the server
            logger.error("Error code received from the SPEAD Rx server: "+ans)
            exit()
        logger.info("Waiting for the transit time to issue SPEAD Metadata...")

        # Issuing the SPEAD metadata packet at right time
        if (((transit_utc - datetime.datetime.utcfromtimestamp(time.time()))).seconds > ((opts.acqtime/2)*60) ) and opts.now == False:
            time.sleep((((transit_utc - datetime.datetime.utcfromtimestamp(time.time()))).seconds - (opts.acqtime/2)*60) +1)
        else:
            logger.info("Observation started in late, transit time will be not at the center of the file")
        logger.info("Issuing the SPEAD packet for source: "+sources[index])
        os.system("sudo xeng_spead_issue.py "+BACKEND_CALIB_CONFIG+" "+BACKEND_SOURCE_PATH+sources[index]+".xml > /dev/null")
        logger.info("Acquiring "+sources[index]+"!")

        # Getting data from weather station at transit time
        while transit_utc > datetime.datetime.utcfromtimestamp(time.time()) and opts.now == False:
            time.sleep(60)
        logger.info("Getting weather conditions")
        os.chdir("/home/oper/Birales")
        os.system(WEATHER_SCRIPT+" > "+data_dir+"/weather_conditions.txt")
    
        # Take a snapshot of the receivers attenuators and 20 MHz band power
        logger.info("Saving a snapshot of ADC power and the Receivers configurations")
        os.system(RECEIVERS_SCRIPT+" > "+data_dir+"/adc_power_receivers_attenuators.txt")

        # End of recording
        time.sleep((opts.acqtime/2)*60)
        logger.info("End of registration")

        # End of recording
        index = index +1
        if index == len(sources):
            index = 0

        logger.info("Scheduling next source: \""+sources[index]+"\"")
        logger.info("Acquisition length set to: " + str(opts.acqtime) + " minutes")

        


    


