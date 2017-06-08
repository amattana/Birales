#!/usr/bin/env python

import katcp, corr
import datetime, struct, time

fpga = corr.katcp_wrapper.FpgaClient("feng")
time.sleep(1)
if not fpga.is_connected():
    print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
    exit()

t_zero = datetime.datetime.utcfromtimestamp(struct.unpack(">I",fpga.read('header',4,0))[0])
print datetime.datetime.strftime(t_zero, "\nBackend startup time is: %Y/%m/%d %H:%M:%S"), "(UTC)"
print "Startup time in Unix standard time: %d\n" % struct.unpack(">I",fpga.read('header',4,0))[0]


