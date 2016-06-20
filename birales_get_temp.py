#!/usr/bin/env python
"""
Get temperature from Medicina weather station

 
"""
from socket import *
import sys
from xml.dom.minidom import parseString
import time
import os
import datetime

#dm01,wind dir ave [deg]
#sm01,wind speed ave [m/s]
#ta01,air temp [C]
#ua01,rel. humidity [%]
#pa01,air pressure [hPa]
#rc01,rain amount [mm]
#rd01,rain duration [s]
#ri01,rain intensity [mm/h]
#rp01,rain peak duration [s]
#hc01,hail amount [hits/cm2]
#hd01,hail duration [s]
#hi01,hail intensity [hits/cm2h]
#hp01,hail peak duration [s]

sensors = [["ta01","AirTemperature","degC"],
           ["pa01","Pressure","hPa"],
           ["ua01","Humidity","%"],
           ["sm01","WindSpeed","m/s"],
           ["dm01","WindDirection","deg"],
           ["ri01","RainIntensity","mm/h"],
           ["hi01","HailIntensity","hits/cm2h"]]

def decodeTime(self,timeStamp):
    year=int(timeStamp[0:4])
    month=int(timeStamp[4:6])
    day=int(timeStamp[6:8])
    hours=int(timeStamp[8:10])
    mins=int(timeStamp[10:12])
    secs=int(timeStamp[12:14])
    d=datetime.datetime(year,month,day,hours,mins,secs)
    return d

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('birales_get_temp.py [options]')
    p.set_description(__doc__)
    p.add_option('-n', '--ns', dest='not_save',action='store_true', default=False, 
        help='Do not save output, just show!')
    opts, args = p.parse_args(sys.argv[1:])

    if opts.not_save==True:
        print "Option: Don't save in a file!!!"
    client=socket(AF_INET,SOCK_DGRAM)
    client.connect(("192.167.189.101",5001))
    client.settimeout(4)
    client.send("r ta01")
    data=client.recv(1024)
    dom=parseString(data)
    xmlTag=dom.getElementsByTagName('Date')[0].toxml()
    date=xmlTag.replace('<Date>','').replace('</Date>','')
    xmlTag=dom.getElementsByTagName('Val')[0].toxml()
    temp=xmlTag.replace('<Val>','').replace('</Val>','')
    print("\nDate\t%s-%s-%s\nTime\t%s:%s:%s"%(date[0:4],date[4:6],date[6:8],date[8:10],date[10:12],date[12:14]))
    if opts.not_save==False:
        foutname="data/"+time.strftime("%Y-%m-%d_%H%M%S")+"_weather.txt"
        fout = open(foutname,"w")
        fout.write("Date\t%s-%s-%s\nTime\t%s:%s:%s"%(date[0:4],date[4:6],date[6:8],date[8:10],date[10:12],date[12:14]))


    for i in range(len(sensors)):
        client.send("r "+sensors[i][0])
        data=client.recv(1024)
        dom=parseString(data)
        xmlTag=dom.getElementsByTagName('Val')[0].toxml()
        
        print("%s\t%3.1f\t%s"%(sensors[i][1],float(xmlTag.replace('<Val>','').replace('</Val>','')),sensors[i][2]))
        if opts.not_save==False:
            fout.write("\n%s\t%3.1f\t%s"%(sensors[i][1],float(xmlTag.replace('<Val>','').replace('</Val>','')),sensors[i][2]))
           
    if opts.not_save==False:
        fout.close()

