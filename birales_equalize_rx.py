#!/usr/bin/env python
"""
Read adc power and BEST-2 receivers attenuation. 

 
"""

import corr,time,numpy,struct,sys,logging,pylab,matplotlib
import birales_conf_parse,datetime
import os, socket
import curses
import thread

config_file='.'
fpga = []

RXPKT_HEAD   = 1
RXPKT_MASTER = 124
RXPKT_CMD = 111 # set_data
RXPKT_COUNT  = 1
RXPKT_DATA_TYPE = 8 # U8
RXPKT_PORT_TYPE = 4 # DIO
RXPKT_PORT_NUMBER = 97 # 08_15 # Attenuation


def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    try:
        fpga.stop()
    except: pass
    raise
    exit()

def exit_clean():
    try:
        fpga.stop()
    except: pass
    exit()

def check_adc_sync():
    rv = fpga.read_uint('adc_sync_test')
    while (rv&0b111) != 1:
        fpga.write_int('adc_spi_ctrl', 1)
        time.sleep(.05)
        fpga.write_int('adc_spi_ctrl', 0)
        time.sleep(.05)
        print '    ERROR: adc sync test returns %i'%rv
        rv = fpga.read_uint('adc_sync_test')
    print '    SUCCESS: adc sync test returns %i (1 = ADC syncs present & aligned)' %rv

def bit_string(val, width):
    bitstring = ''
    for i in range(width):
        bitstring += str((val & (1<<i))>>i)
    return bitstring

def adc_cal(calreg='x64_adc_ctrl', debug=False):
    # Some Addresses...
    CTRL       = 0
    DELAY_CTRL = 0x4
    DATASEL    = 0x8
    DATAVAL    = 0xc

    for j in range(0,8):
        if debug: print '%d: '%(j)
        #select bit
        fpga.blindwrite(calreg, '%c%c%c%c'%(0x0,0x0,0x0,j//2), DATASEL)
        #reset dll
        fpga.blindwrite(calreg, '%c%c%c%c'%(0x0,0x0,0x0,(1<<j)), DELAY_CTRL)
        if debug: print "ready\tstable\tval0"
        stable = 1
        prev_val = 0
        while(stable==1):
            fpga.blindwrite(calreg, '%c%c%c%c'%(0x0,0xff,(1<<j),0x0), DELAY_CTRL)
            #val = numpy.fromstring(fpga.read(calreg,4,DATAVAL), count=4, dtype='uint8')
            val    = struct.unpack('>L', (fpga.read(calreg,4,DATAVAL)))[0]
            val0   = (val & ((0xffff)<<(16*(j%2))))>>(16*(j%2))
            stable = (val0&0x1000)>>12
            ready  = (val0&0x2000)>>13
            fclk_sampled = bit_string((val0&0x0fff),12)
            if val0 != prev_val and prev_val != 0:
                break
            prev_val = val0
            if debug: print '%d\t%d\t%s' %(ready, stable, fclk_sampled)
        if debug: print ''
        for i in range(10):
            fpga.blindwrite(calreg, '%c%c%c%c'%(0x0,0xff,(1<<j),0x0), DELAY_CTRL)
            #val = numpy.fromstring(fpga.read(calreg,4,DATAVAL), count=4, dtype='uint8')
            val    = struct.unpack('>L', (fpga.read(calreg,4,DATAVAL)))[0]
            val0   = (val & ((0xffff)<<(16*(j%2))))>>(16*(j%2))
            stable = (val0&0x1000)>>12
            ready  = (val0&0x2000)>>13
            fclk_sampled = bit_string((val0&0x0fff),12)
            if debug: print '%d\t%d\t%s' %(ready, stable, fclk_sampled)
        if debug:print ''

def prog_feng(roach,bitstream):
    print '   Deprogramming FPGAs'
    fpga.progdev('')
    time.sleep(.1)
    print '   Programming %s with bitstream %s' %(roach,bitstream)
    fpga.progdev(bitstream)
    time.sleep(.1)

    print   '   Calibrating ADC on %s' %(roach)
    adc_cal();
    time.sleep(0.05)
    fpga.write_int('adc_spi_ctrl', 1)
    time.sleep(.05)
    fpga.write_int('adc_spi_ctrl', 0)
    time.sleep(.05)
    time.sleep(0.5)
    check_adc_sync()
    time.sleep(0.5)
    check_adc_sync()
    time.sleep(0.5)
    check_adc_sync()
    time.sleep(0.5)
    check_adc_sync()
    time.sleep(0.5)
    check_adc_sync()

def get_adc_power(antenna):
    adc_levels_acc_len = 32
    adc_bits = 12

    ##clear the screen:
    #print '%c[2J'%chr(27)

    #while True:
    # move cursor home
    #overflows = inst.feng_read_of(fpga)
    fpga.write_int('adc_sw_adc_sel',antenna)
    time.sleep(.05)
    rv=fpga.read_uint('adc_sw_adc_sum_sq')
            
    pwrX = float(rv)
    rmsX = numpy.sqrt(pwrX/adc_levels_acc_len)/(2**(adc_bits-1))
    bitsX = max(numpy.log2(rmsX * (2**(adc_bits))), 0.)

    #if ant<10: print '\tADC0%i:     polX:%.5f (%2.2f bits used)     polY:%.5f (%2.2f bits used)'%(ant,rmsX,bitsX,rmsY,bitsY)
    #else: print '\tADC%i:     polX:%.5f (%2.2f bits used)     polY:%.5f (%2.2f bits used)'%(ant,rmsX,bitsX,rmsY,bitsY)
    return  bitsX

def get_eq_power(antenna):
    adc_levels_acc_len = 32
    adc_bits = 12

    ##clear the screen:
    #print '%c[2J'%chr(27)

    #while True:
    # move cursor home
    #overflows = inst.feng_read_of(fpga)
    fpga.write_int('eq_amp_sel',antenna)
    time.sleep(.1)
    rv=fpga.read_uint('eq_amp_sum_sq')
    #print rv
            
    pwrX = float(rv)
    rmsX = numpy.sqrt(pwrX/adc_levels_acc_len)/(2**(adc_bits-1))
    bitsX = max(numpy.log2(rmsX * (2**(adc_bits))), 0.)

    #if ant<10: print '\tADC0%i:     polX:%.5f (%2.2f bits used)     polY:%.5f (%2.2f bits used)'%(ant,rmsX,bitsX,rmsY,bitsY)
    #else: print '\tADC%i:     polX:%.5f (%2.2f bits used)     polY:%.5f (%2.2f bits used)'%(ant,rmsX,bitsX,rmsY,bitsY)
    return  bitsX

def write_ctrl_sw(ctrl='ctrl_sw'):
    fpga.write_int(ctrl,0)

def change_ctrl_sw_bits(lsb, msb, val, ctrl='ctrl_sw'):
    num_bits = msb-lsb+1
    if val > (2**num_bits - 1):
        print 'ctrl_sw MSB:', msb
        print 'ctrl_sw LSB:', lsb
        print 'ctrl_sw Value:', val
        raise ValueError("ERROR: Attempting to write value to ctrl_sw which exceeds available bit width")
    # Create a mask which has value 0 over the bits to be changed
    mask = (2**32-1) - ((2**num_bits - 1) << lsb)
    # Remove the current value stored in the ctrl_sw bits to be changed
    ctrl_sw_value = fpga.read_uint(ctrl)
    ctrl_sw_value = ctrl_sw_value & mask
    # Insert the new value
    ctrl_sw_value = ctrl_sw_value + (val << lsb)
    # Write
    fpga.write_int(ctrl,ctrl_sw_value)

def arm_sync():
    change_ctrl_sw_bits(11,11,0)
    change_ctrl_sw_bits(11,11,1)

def send_sync():
    change_ctrl_sw_bits(12,12,0)
    change_ctrl_sw_bits(12,12,1)
    
def set_fft_shift(shift):
    change_ctrl_sw_bits(0,10,shift)

def use_phase_cal(val):
    change_ctrl_sw_bits(20,20,int(val))

def status_flag_rst():
    change_ctrl_sw_bits(19,19,1)
    change_ctrl_sw_bits(19,19,0)

def initialise_ctrl_sw(ctrl='ctrl_sw'):
    """Initialises the control software register to zero."""
    write_ctrl_sw(ctrl=ctrl)

def feng_arm():
    """Arms all F engines, records arm time in config file and issues SPEAD update. Returns the UTC time at which the system was sync'd in seconds since the Unix epoch (MCNT=0)"""
    #wait for within 100ms of a half-second, then send out the arm signal.
    ready=(int(time.time()*10)%5)==0
    while not ready:
        ready=(int(time.time()*10)%5)==0
    trig_time=time.time()
    arm_sync() #implicitally affects all FPGAs
    sync_time=trig_time
    #self.sync_arm_rst()
    send_sync()
    # Nel vecchio veniva scritto in un file chiamato come il file di conf.
    #
    #base_dir = os.path.dirname(config_file)
    #base_name = os.path.basename(config_file)
    #pkl_file = base_dir + "/sync_" + base_name.split(".xml")[0]+".pkl"
    #pickle.dump(sync_time, open(pkl_file, "wb"))
    
    # Nel nuovo lo scrivo in un software register chiamato t_start
    fpga.write_int('t_zero',int(trig_time))
    return trig_time

def read_status(trig=True, sleeptime=3):
    if trig:
        status_flag_rst()
        time.sleep(sleeptime)
    value = fpga.read_uint('status')
    return {     'Amp EQ Overflow'               :{'val':bool(value&(1<<1)),  'default':False},
                 'FFT Overflow'                  :{'val':bool(value&(1<<2)),  'default':False},
                 'Phase EQ Overflow'             :{'val':bool(value&(1<<4)),  'default':False},
                 'Sync Gen Armed'                :{'val':bool(value&(1<<6)), 'default':False}}


def eq_retta(x1,y1,x2,y2):
    m=float(y2-y1)/(x2-x1)
    q=y1-(m*x1)
    def retta(x):
        return m*x + q
    return retta
    
def bit2db(val):
    for i in range(len(adc_curve)):
        if adc_curve[i][1] > val:
            break
    if i>0:
        r= eq_retta(adc_curve[i][1],adc_curve[i][0],adc_curve[i-1][1],adc_curve[i-1][0])
    else: 
        r= eq_retta(adc_curve[1][1],adc_curve[1][0],adc_curve[0][1],adc_curve[0][0])
    return r(val)

def openfiles(tempo,pol_h,pol_v,fname):
    files = []
    for i in range(len(pol_h)):
        foutname="ADCPWR/"+time.strftime("%Y-%m-%d_%H%M%S")+"_ADCPWR_"+pol_h[i][0]+fname+".txt"
        files += [open(foutname,"a")]
        foutname="ADCPWR/"+time.strftime("%Y-%m-%d_%H%M%S")+"_ADCPWR_"+pol_v[i][0]+fname+".txt"
        files += [open(foutname,"a")]
    foutname="ADCPWR/"+time.strftime("%Y-%m-%d_%H%M%S")+"_ADCPWR_STATUS.txt"
    files += [open(foutname,"a")]
    return files

def openfile(tempo,fname):
    foutname="ADCPWR/"+time.strftime("%Y-%m-%d_%H%M%S")+"_MAD-18-ADC_"+fname+".txt"
    ofile = open(foutname,"a")
    return ofile

def closefiles(files):
    for i in range(len(files)):
        files[i].close()

def bit2att(val):
    attenuazione  = ((val&2**0)>>0) * 0.5
    attenuazione += ((val&2**1)>>1) * 16
    attenuazione += ((val&2**2)>>2) * 1
    attenuazione += ((val&2**3)>>3) * 8
    attenuazione += ((val&2**4)>>4) * 2
    attenuazione += ((val&2**5)>>5) * 4
    return attenuazione  

def att2bit(val):
    #print "\natt2bit(",val,")\tBin:",bin(val),
    val = int(val*2)
    #print val,")\tBin:",bin(val),
    attenuazione  = ((val&2**0)>>0) * 1
    attenuazione += ((val&2**1)>>1) * 4
    attenuazione += ((val&2**2)>>2) * 16
    attenuazione += ((val&2**3)>>3) * 32
    attenuazione += ((val&2**4)>>4) * 8
    attenuazione += ((val&2**5)>>5) * 2
    #print attenuazione,bin(attenuazione)
    return attenuazione  

def get_att_value(s,ip,slave):
    RXPKT_CMD = 110 # get_data
    msg = struct.pack('>BBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 3, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER)
    s[ip].send(msg)
    a=s[ip].recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]==0:
        att=bit2att(struct.unpack('>'+str(len(a))+'B',a)[10])
    else:
        att=-1
    return att

def set_att_value(s,ip,slave,value):
    value=round(value*2)/2  # 0.5 dB is the step for attenuation
    RXPKT_CMD = 111 # set_data
    msg = struct.pack('>BBBBBBBBBB', RXPKT_HEAD, slave, RXPKT_MASTER, RXPKT_CMD, RXPKT_COUNT, 4, RXPKT_DATA_TYPE, RXPKT_PORT_TYPE, RXPKT_PORT_NUMBER,att2bit(value))
    s[ip].send(msg)
    a=s[ip].recv(32)
    if struct.unpack('>'+str(len(a))+'B',a)[5]!=0:
        print "Cmd returned an error!!!"

def get_list(rx_file):
    antennas=[]  
    rx_h = open(rx_file)
    rx_list=rx_h.readlines()
    for i in xrange(len(rx_list)):
        antennas += [rx_list[i].split()]
        antennas[i][1] = int(antennas[i][1])
        antennas[i][2] = int(antennas[i][2])
        antennas[i][3] = int(antennas[i][3])
    rx_h.close()
    return antennas
    
def get_net_list(rx_net_file):
    net_h = open(rx_net_file)
    net_list=net_h.readlines()
    net_h.close()
    for i in xrange(len(net_list)):
        net_list[i]=net_list[i].split()[0]
    return net_list


def open_connections(net_list):
    s=[]
    for i in range(len(net_list)):
        print "Connetion to ",net_list[i],":5002...",
        s += [socket.socket(socket.AF_INET, socket.SOCK_STREAM)]
        s[i].connect((net_list[i],5002))
        print "ok!"
    return s
    
def close_connections(s,net_list):
    for i in range(len(net_list)):
        s[i].close()
    print "All connections have been closed!"
    
def get_addr(rx):
    ip = -1
    slave = 0
    if (rx > 0) and (rx < 33):
        ip = (rx//8)-1
        slave = rx%8
        if slave == 0:
            slave = 8
        else:
            ip += 1
    else:
        print "ERROR: RX # must be between 1 and 32 !!!"
    return ip,slave
  
if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('birales_equalize_rx.py [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--config_file', dest='config_file', type='str',default='configura_birales.conf',
        help='Configuration File [Default: "./configura.conf"]')
    p.add_option('-r', '--roach_name', dest='roach_name', type='str',default='',
        help='Configuration File [Default: "./configura.conf"]')
    p.add_option('-f', '--file_name', dest='fname', type='str',default='',
        help='String to be added to the output file name')
    p.add_option('-i', '--iteration', dest='iter_count', type='int',default='5',
        help='Number of iteration for equalization (Default: 5)')
    p.add_option('-e', '--eqvalue', dest='eqvalue', type='float',default='-50',
        help='Equalization Value (Default: -50 which means do not equalize)')
    p.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
            help='Print lots of lovely debug information')

    opts, args = p.parse_args(sys.argv[:])
    config_file = opts.config_file
    fname = opts.fname
     
    configura,base_conf =  birales_conf_parse.parse_settings(config_file)
    #print configura
    if opts.roach_name == '':
        roach      = configura['roach_name']
    else:
        roach=opts.roach_name
    katcp_port = configura['katcp_port']
    adc_debug  = configura['adc_debug']
    bitstream  = configura['bitstream']
    rx_network = configura['rx_network']
    rx_map     = configura['rx_map']
        
    adc_curve=[]
    f_adc_curve = open(configura["adc_curve"])
    adc_curve_list=f_adc_curve.readlines()
    for i in range(len(adc_curve_list)):
        adc_curve += [[adc_curve_list[i][:-1].split(' ')[0],adc_curve_list[i][:-1].split(' ')[2]]]
        adc_curve[i][0] = float(adc_curve[i][0])
        adc_curve[i][1] = float(adc_curve[i][1])
    f_adc_curve.close()
    
    print('Connecting to ROACH board named "%s"... '%roach),
    fpga = corr.katcp_wrapper.FpgaClient(roach)
    time.sleep(1)
    if fpga.is_connected():
        print 'ok'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    powA=[]
    antennas=[]
    antennas = get_list(rx_map)
    net_list = get_net_list(rx_network)
    s = open_connections(net_list)
    ofile=openfile(time.time(),fname) 

    #print antennas 
  
    if opts.verbose: 

	    eqvalue = opts.eqvalue
            print "Debug mode!\n"
	    ntempo=time.time()
	    tempo=str(datetime.datetime.utcfromtimestamp(ntempo))
	    #print str(ntempo)+"\t"+str(tempo)+"\t",
            print "\n  BEST\t\tFeng\tBits\t dBm \tRxdB\tdiff",
            if not opts.eqvalue == -50:
                print "\t\t dBm \tRxdB\tdiff\n-------------------------------------------------------      -------------------------"
            else:
                print "\n------------------------------------------------------- "
	    for i in xrange(len(antennas)):
		#powH = get_adc_power(pol_h[i][1])  corretta
		powA = get_adc_power(antennas[i][1])
		rx_att_A = get_att_value(s,antennas[i][2],antennas[i][3])
                if (i == 0) and (opts.eqvalue == -50):
                    eqvalue = bit2db(powA)
		diffA = eqvalue-bit2db(powA)
		print('%s\t\t %s\t%2.2f\t%2.2f\t%2.1f\t%2.1f'%(antennas[i][0],antennas[i][1],powA,bit2db(powA),rx_att_A,diffA)),

                if not opts.eqvalue == -50:
                    if diffA<0:
                        set_att_value(s,antennas[i][2],antennas[i][3],numpy.clip([rx_att_A+abs(diffA)],0,31.5)[0])
                    else:
                        set_att_value(s,antennas[i][2],antennas[i][3],numpy.clip([rx_att_A-diffA],0,31.5)[0])

		    powA = get_adc_power(antennas[i][1])
		    rx_att_A = get_att_value(s,antennas[i][2],antennas[i][3])
		    diffA = eqvalue-bit2db(powA)
		    print('\t-->\t%2.2f\t%2.1f\t%2.1f'%(bit2db(powA),rx_att_A,diffA))
                else:
                    print " "
    else:
	    try:
		from msvcrt import getch
	    except ImportError:
		def getch():
		    import sys, tty, termios
		    fd = sys.stdin.fileno()
		    old_settings = termios.tcgetattr(fd)
		    try:
			tty.setraw(sys.stdin.fileno())
			ch = sys.stdin.read(1)
		    finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		    return ch

	    char = None

	    def keypress():
		global char
		char = getch()
	     
	    thread.start_new_thread(keypress, ())

	    screen=curses.initscr()
	    dims=screen.getmaxyx()
	    
	    equalizing = False
	    iter_count = 0
	    iter_counts=opts.iter_count
	    startup = True
	    
	    eqvalue = opts.eqvalue

	    try:
		while char != "q":
		    #curses.noecho()
		    screen.clear()
		    x=0
		    #print "\n HPOL\tBITS\t  dB \t  eq \tVPOL\tBITS\t  dB  \t  eq \n----------------------------------------------"    
		    #print "\n HPOL\tBITS\t  dB \tVPOL\tBITS\t  dB \n----------------------------------------------"
		    screen.addstr(x,2,"\n  BEST\t\tFeng\tBits\t dBm \tRxdB\tdiff\n---------------------------------------------------")
		    x=4    
		    powA=[]
		    rx_att_A=[]
		    eqpowA=[]
		    diffA=[]
		    n=0
		    ntempo=time.time()
		    tempo=str(datetime.datetime.utcfromtimestamp(ntempo))
		    record=str(ntempo)+"\t"+str(tempo)+"\t"
		    for i in xrange(len(antennas)):
			#powH = get_adc_power(pol_h[i][1])  corretta
			powA += [get_adc_power(antennas[i][1])]
			record+= ("%2.2f"%(bit2db(powA[i]))+"\t")
			if startup or equalizing:
			    #ip, slave = get_addr(pol_h[i][2])
			    rx_att_A += [get_att_value(s,antennas[i][2],antennas[i][3])]
                            if (startup==True) and (eqvalue == -50):
                                eqvalue=bit2db(powA[i])
                            #startup = False
			diffA += [eqvalue-bit2db(powA[i])]
			#n=n+1
		    for i in xrange(len(antennas)):
			screen.addstr(x,1,'%s\t\t %s\t%2.2f\t%2.2f\t%2.1f\t%2.1f'%(antennas[i][0],antennas[i][1],powA[i],bit2db(powA[i]),rx_att_A[i],diffA[i]))
			#screen.addstr(x,1,'%s\t%2.2f\t%2.2f\t%2.2f\t%s\t%2.2f\t%2.2f\t%2.2f'%(pol_h[i][0],powH[i],bit2db(powH[i]),eqpowH[i],pol_v[i][0],powV[i],bit2db(powV[i]),eqpowV[i]))
			#screen.refresh()
			x=x+1
			#print "."
		    screen.addstr(x+1,1,str(datetime.datetime.utcfromtimestamp(time.time()))+" UTC")
		    ofile.write(record+"\n")
		    starup = False
	    
		    status_flag_rst()
		    time.sleep(0.01)
		    status = fpga.read_uint('status')
		    if (status&(1<<1)):
			screen.addstr(x+4,1,"    !!!!!!   Amp EQ Overflow   !!!!!!")
		    else:
			screen.addstr(x+4,1,"                                     ")
		    if (status&(1<<2)):
			screen.addstr(x+5,1,"    !!!!!!     FFT Overflow    !!!!!!")
		    else:
			screen.addstr(x+5,1,"                                     ")
		    if (status&(1<<4)):
			screen.addstr(x+6,1,"    !!!!!!  Phase EQ Overflow  !!!!!!")
		    else:
			screen.addstr(x+6,1,"                                     ")
		    if (status&(1<<6)):
			screen.addstr(x+7,1,"    !!!!!!    Sync Gen Armed   !!!!!!")
		    else:
			screen.addstr(x+7,1,"                                     ")

		    screen.addstr(x+12,1,"Press [q] key to Exit")
		    if equalizing:
			iter_count=iter_count +1
			if (iter_count==iter_counts):
			    if char == 'e':
			        screen.move(x+9,1)
			        screen.addstr(x+9,1,"Antenna Equalization with %2.1f dBm  (%d/%d) done!"%(eqvalue,iter_count,iter_counts))
			        #time.sleep(0.2)
			    char = None
			    thread.start_new_thread(keypress, ())
			    iter_count=0
			    equalizing=False
			else:
			    if char == 'h':
			        screen.move(x+9,1)
			        screen.addstr(x+9,1,"Equalizing Antennas with %2.1f dBm, please wait...  (%d/%d)"%(eqvalue,iter_count,iter_counts))
			#screen.refresh()
		       
		    else:
			if char == 'e':
			    screen.addstr(x+9,1,"Equalization target value (dBm): ")
			    screen.addstr(x+10,1,"                                                          ")
			    screen.move(x+9,44)
			    screen.refresh()
			    lettura=screen.getstr()
			    eqvalue = float(lettura)
			    equalizing=True
			        
			    
			if char == None:
			    screen.addstr(x+9,1,"Press [e] key to Equalize Antennas      ")
			
		    
		    screen.move(dims[0]-1,dims[1]-1)
		    screen.refresh()
	    
		    if equalizing:
			for i in xrange(len(antennas)):
			    if char=='e':
			        #ip, slave = get_addr(pol_h[i][2])
			        if abs(max(diffA)-min(diffA))>0.5:
			            time.sleep(0.1)
			            if diffA[i]<0:
			                set_att_value(s,antennas[i][2],antennas[i][3],numpy.clip([rx_att_A[i]+abs(diffA[i])],0,31.5)[0])
			            else:
			                set_att_value(s,antennas[i][2],antennas[i][3],numpy.clip([rx_att_A[i]-diffA[i]],0,31.5)[0])

		curses.endwin(); 
		ofile.close()
		close_connections(s,net_list)
		del s
		del ofile
		del powA
		del eqpowA
		del tempo
		del adc_curve
		del antennas
		del diffA
		del rx_att_A
		exit();
		    
	    except KeyboardInterrupt:
		#closefiles(files)
		#curses.echo()
		curses.endwin(); 
		ofile.close()
		close_connections(s,net_list)
		del s
		del ofile
		del powA
		del eqpowA
		del tempo
		del adc_curve
		del antennas
		del diffA
		del rx_att_A
		exit();
        
        
           
