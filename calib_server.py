#!/usr/bin/env python

# Copyright (C) 2016, Osservatorio di RadioAstronomia, INAF, Italy.
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# 
# Correspondence concerning this software should be addressed as follows:
#
#	Andrea Mattana
#	Radiotelescopi di Medicina
#       INAF - ORA
#	via di Fiorentina 3513
#	40059, Medicina (BO), Italy

"""
Provides a socket comunication between the RS-232 lane 
of the Northern Cross Pointing System Computer 
done by Andrea Maccaferri for the Pulsar Scheduler(1990)
"""

# Python modules
import SocketServer
import struct
import socket
import time

import datetime
import logging
import logging.handlers
import os,sys

__author__ = "Andrea Mattana"
__copyright__ = "Copyright 2016, Osservatorio di RadioAstronomia, INAF, Italy"
__credits__ = ["Andrea Mattana, Andrea Maccaferri"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Andrea Mattana"


# Handy aliases
BUFF_LEN = 1024

# Server Status Code
STATUS_CODE=["OK: xeng_spead_rx is active!",		#0
             "Error: The path does not exist!",	#1
             "Error: Server not started!",	#2
             "Other TBI!",	#3
            ]

class SpeadRx():
    def __init__(self, path="/tpm", config = "$CALIBCONFIG", minutes=20):
        logger.info("Creating the object SpeadRx...")
        self.status=0
        self.path=path
        self.config=config
        self.minutes=minutes
        try:
            os.chdir(self.path)
            logger.info("Check if path exist...ok! Current workdir: "+os.path.curdir())
        except:
            logger.error("The path %s does not exist!"%(self.path))
            self.status=1
            return self.status
        
        try:
            cmd="xeng_spead_rx_time.py %s -t %d & > spead_rx.log"%(self.config,self.minutes)
            logger.info("Commanding: %s..."%cmd)
            os.system(cmd)
        except:
            logger.error("ERROR: An error occurer while starting the server with the command:\t\t- "%(cmd))
            self.status=2
            return self.status
        print "Fin qui ci siamo"
        return self.status

    def start(self):
        os.chdir(self.path)
        cmd="xeng_spead_rx_time.py %s -t %d & > spead_rx.log"%(config,minutes)
        logger.info("Commanding: %s..."%cmd)
        return self.status

    def get_server_status(self):
        return STATUS_CODE[self.status]



class CalibTCPHandler(SocketServer.BaseRequestHandler):
    
    def handle(self):
        #try:
        #while True:
            logger.info("Accepted connection from "+ self.client_address[0] + ".")
            #conn, addr = self.accept()
            while True:
	        #self.data = self.rfile.readline().strip()
                self.data = self.request.recv(1024)
                #print len(self.data), self.data
                if not self.data:
                    logger.info("Closing connection from "+self.client_address[0]+"...")
                    time.sleep(0.1)
                    self.request.close()
                    break
	        logger.info("Command received: %s (%d bytes)"%(self.data,len(self.data)))
                #if not self.data: break
	        args = self.data.split()
	        try:
	            res = self.server.execute(args)
                    self.request.send(res)
	        except:
	            logger.error("Bad request from "+self.client_address[0])
                    #self.server.shutdown()
                    #self.server.finish()
                    time.sleep(1)
                    #break
        #except KeyboardInterrupt:
            #sys.exit(0)

    def finish(self):
        logger.info("Disconnected from "+self.client_address[0]+".")

class CalibTCPServer(SocketServer.TCPServer):
    def __init__(self, addr):
        try:
            logger.info("Starting the Socket Server")
            SocketServer.TCPServer.__init__(self, addr, CalibTCPHandler)
            logger.info("Socket is listening on Port "+str(addr[1]))
        except:
            logger.error("Socket Failure! Address might be already in use")
        self.rec = 0
        self.commands = {
                         "start": self.start,
                         "close": self.close,
                         "abort": self.abort,
                        }

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def execute(self, args):
        if not self.commands.has_key(args[0]):
            res = "Command \'%s\' not found."%(args[0],)
            logger.error(res)
        else:
            if len(args) > 1:
                try:
                    res = self.commands[args[0]](*(args[1:]))
                except TypeError, te:
                    logger.error("501 This exception has not been managed!")
                    time.sleep(0.1)
                    #res = "Command \'%s\' not found."%(args[0],)
                    #logger.error(res)
            else:
                try:
                    res = self.commands[args[0]]()
                except TypeError, te:
                    logger.error("502 This exception has not been managed!")
                    time.sleep(0.1)
                    #res = "Command \'%s\' not found."%(args[0],)
                    #logger.error(res)
        return res

    def start(self, path="/tpm", config = "$CALIBCONFIG", minutes=20):
        logger.info("Executing cmd start with:")
        logger.info("\tPATH: %s"%path)
        logger.info("\tCONFIG: %s"%config)
        logger.info("\tMINUTES: %s"%(str(minutes)))
        os.path.os.chdir(path)
        logger.info("Check if path exist...ok! Current workdir: "+path)

        cmd="xeng_spead_rx_time.py "+config+" -t "+str(minutes)+" > spead_rx.log &"
        logger.info("Commanding: %s..."%(cmd))
        os.system(cmd)
        return STATUS_CODE[0]

    def close(self):
        logger.info("Terminating the server")
        self.rec = 0
        P.close()
        del(P)
        return ans

    def abort(self):
        logger.info("Executing cmd abort...")
        self.rec = 0
        P.close()
        del(P)
        return "aborted!"


#Setting up logging    
log_filename = "calib_server.log"
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

if __name__=="__main__":
    from optparse import OptionParser

    #command line parsing
    op = OptionParser()
    op.add_option("-p", "--port", type="int", dest="port", default=7210)
    #op.add_option("-c", "--config", dest="config", default="$CALIBCONFIG")
    opts, args = op.parse_args(sys.argv[:])

    logger.info("Starting the program with options:")
    #logger.info("\t- IP: " + str(opts.addr))
    logger.info("\t- Port: " + str(opts.port))

    try:
        while True:
            server = CalibTCPServer(("", opts.port))
            ip, port = server.server_address # find out what port we were given
            #logger.info("server listening on port: " + str(opts.port))
            server.serve_forever()

    except KeyboardInterrupt:
        logger.info("Closing Comunication.")
	del(server)
        logger.info("Ended Successfully")




