#!/usr/bin/env python
"""
Start the processing of the Medicina's Correlator hdf5 file 

 
"""

import numpy,struct
import logging
import logging.handlers
import os,sys
import time, datetime
import socket
import glob

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"

BASE_PATH = "/mnt/2016/"
BUFFER_SIZE = 1024
BEST2_POINTING_ADDR = "127.0.0.1"
BEST2_POINTING_PORT = 7200
SCRIPT_PATH = "/home/oper/Birales"
BEST2_POINTING_CURVE = [[0.0, 0],[28.5,163],[46.6,263]]

BACKEND_CALIB_CONFIG = "/home/lessju/Working/feng_xeng_calib.xml"
BACKEND_SOURCE_PATH  = "/home/lessju/Code/medicina/poxy/config/src/"

WEATHER_SCRIPT = "./birales_get_temp.py -v -n"
RECEIVERS_SCRIPT = "./birales_equalize_rx.py -v "

PROC_FIX_MED = "fix_med_corr.py "
GEOMETRY_FILE = "med5673.py" 
PROC_PHS2SRC = "phs2src_h5.py -C "+GEOMETRY_FILE[:-3]+" "
PROC_AMPLITUDE = "plot_corr_h5.py -c 600 --chan -a 0_31 -p xx -m log "
PROC_CALIB = "gaincal.py -t 60_80 -c 400_700 "


def gps2dec(angolo):
    g, p, s = angolo.strip().split(":")
    return '%3.3f'%(float(g)+(((float(s)/60)+float(p))/60))

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
log_filename = "log/best2_process.log"
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
    p.set_usage('birales_processing.py [options]')
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

    #sources = [opts.source]
    #if opts.source.count(",") > 0:
        #sources = opts.source.split(",")
    

    lista_dir = os.listdir(BASE_PATH)
    for daily_obs_dir in sorted(lista_dir):

        lista_obs = os.listdir(BASE_PATH+daily_obs_dir)
        for source_obs in sorted(lista_obs):
           
            skip_dir=0
            #transit_utc  = datetime.datetime(int("2016"),int(daily_obs_dir[:2]),int(daily_obs_dir[4:]))

            # Checking if this directory has to be processed
            #data_dir = BASE_PATH+"%04d/%02d-%02d/%s"%(transit_utc.year,transit_utc.month,transit_utc.day,source_obs)+"/"
            data_dir = BASE_PATH+daily_obs_dir+"/"+source_obs+"/"
            os.system("sudo chown -R oper.oper "+data_dir)
            os.chdir(data_dir)

            if glob.glob("corr*h5")==[]:
                logger.info("Skipping directory "+data_dir[:-1]+", no corr file found!")
                continue

            corr_file=glob.glob("corr*h5")[0]
 
            if os.path.isfile(corr_file+"c."+source_obs+".cal.pkl"):
                logger.info("Skipping directory "+data_dir[:-1]+", data is aleady calibrated!")
                os.system("sudo rm -rf "+corr_file)
                continue

            # Starting processing
            logger.info("Starting processing "+data_dir)
            source_string = BASE_PATH[-5:-1]+"-"+daily_obs_dir+"_"+source_obs
   

            # Fix single to dual pol
            logger.info("PROCESSING: Fixing single to dual pol")
            os.system(PROC_FIX_MED+corr_file+" > /dev/null")
            corr_file_h5c = corr_file+'c'

            # Save Fringes Plot
            logger.info("PROCESSING: Saving Fringes Plot: "+data_dir+source_string+"_fringes.png")
            os.system("plot_corr_h5.py -p xx -a 0 -c 600_800 -w -m phs " + corr_file_h5c + " -s "+source_string+"_fringes.png > /dev/null")

            # Checking the transit time of the source
            datestring = source_string.split('_')[0].replace('-','/') 
            #logger.info("Checking the transit time of the source: "+source_obs)
            ans=os.popen(SCRIPT_PATH+'/calib_source.py -r '+source_obs + " "+ datestring).read()
            source=ans.split('\n')
            source.pop(len(source)-1)
    
            for i in source:
                if i.split()[1]==source_obs:
                    transit_utc = i.split()[11]+" "+i.split()[12]
                    transit_ra  = i.split()[4]
                    transit_dec = i.split()[6]
                    logger.info("PROCESSING: Transit time of "+source_obs+": %s (UTC), RA: %s, DEC: %s"%(transit_utc, transit_ra, transit_dec))
                    transit_utc = datetime.datetime.strptime(transit_utc, "%Y/%m/%d %H:%M:%S")
                else:
                    logger.error("Unknown Radiosource! Path: "+daily_obs_dir+"/"+source_obs)
                    error_dir=1
            if skip_dir==1:
                logger.info("Skipping this directory!")
                continue
        
            # Phasing data to source
            os.system("cp "+SCRIPT_PATH+"/"+GEOMETRY_FILE+" "+data_dir)
            logger.info("PROCESSING: Phasing data to source")
            os.system(PROC_PHS2SRC+"-s "+transit_ra+"_"+transit_dec+" "+corr_file_h5c+" > phs2src.log")
            corr_file_h5c_phased = corr_file_h5c+"."+source_obs
            os.system("mv "+corr_file_h5c+"."+transit_ra+"_"+transit_dec+" "+corr_file_h5c_phased)

            # Save Phased Data Plot
            logger.info("PROCESSING: Saving Phased Data Plot: "+data_dir+source_string+"_phased.png")
            os.system("plot_corr_h5.py -p xx -a 0 -c 600_800 -w -m phs " + corr_file_h5c_phased + " -s "+source_string+"_phased.png > /dev/null")

            # Save Amplitude Plot of a single baseline to check SNR
            logger.info("PROCESSING: Saving Amplitude Plot of a single baseline to check SNR: "+data_dir+source_string+"_amplitude_baseline-0-31_channel-600.png")
            os.system(PROC_AMPLITUDE+corr_file_h5c_phased+" -s "+source_string+"_amplitude_baseline-0-31_channel-600.png  > /dev/null")

            # Calibrate the data
            logger.info("PROCESSING: Calibrating data")
            os.system(PROC_CALIB+" -s "+source_string+" "+corr_file_h5c_phased+" > gaincal.log")
            os.system("sudo chown -R oper.oper "+data_dir)

            # Clean temporary data
            os.system("sudo rm -rf "+corr_file+" "+corr_file_h5c_phased+" "+corr_file_h5c)

        


    


