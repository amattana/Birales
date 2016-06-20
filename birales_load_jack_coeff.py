#!/usr/bin/env python

import corr,time,numpy,struct,sys,logging,pylab,matplotlib
import birales_conf_parse
import os

config_file='.'
fpga = []

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


def get_adc_power(antenna):
    adc_levels_acc_len = 32
    adc_bits = 12

    ##clear the screen:
    #print '%c[2J'%chr(27)

    #while True:
    # move cursor home
    #overflows = inst.feng_read_of(fpga)
    fpga.write_int('adc_sw_adc_sel',antenna)
    time.sleep(.1)
    rv=fpga.read_uint('adc_sw_adc_sum_sq')
            
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
        print "%d > %d"%(val,(2**num_bits - 1))
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
    #change_ctrl_sw_bits(11,11,0)

def send_sync():
    change_ctrl_sw_bits(12,12,0)
    change_ctrl_sw_bits(12,12,1)
    #change_ctrl_sw_bits(12,12,0)
    
def set_fft_shift(shift):
    change_ctrl_sw_bits(0,10,shift)

def jump_eq_amp(val):
    change_ctrl_sw_bits(20,20,int(val))

def status_flag_rst():
    change_ctrl_sw_bits(19,19,1)
    change_ctrl_sw_bits(19,19,0)

def initialise_ctrl_sw(ctrl='ctrl_sw'):
    """Initialises the control software register to zero."""
    ctrl_sw=0
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
    #if send_sync:
    send_sync()
    #send_sync()
    # Nel vecchio veniva scritto in un file chiamato come il file di conf.
    #
    #base_dir = os.path.dirname(config_file)
    #base_name = os.path.basename(config_file)
    #pkl_file = base_dir + "/sync_" + base_name.split(".xml")[0]+".pkl"
    #pickle.dump(sync_time, open(pkl_file, "wb"))
    
    # Nel nuovo lo scrivo in un software register chiamato t_start
    #fpga.write_int('t_zero',int(trig_time))
    return int(trig_time)

def read_status(trig=True, sleeptime=3):
    if trig:
        status_flag_rst()
        time.sleep(sleeptime)
    value = fpga.read_uint('status')
    return {     'Amp EQ Overflow'               :{'val':bool(value&(1<<1)),  'default':False},
                 'FFT Overflow'                  :{'val':bool(value&(1<<2)),  'default':False},
                 'Phase EQ Overflow'             :{'val':bool(value&(1<<4)),  'default':False},
                 'Sync Gen Armed'                :{'val':bool(value&(1<<6)), 'default':False}}


def head_get_keys(head_file):
    header = []
    f_head = open(head_file)
    head_list=f_head.readlines()
    #print head_list
    for i in range(len(head_list))[2:]:
        header += [head_list[i].split('#')[0].split('\t')[:-1]]
        header[i-2][0] = int(header[i-2][0])
        header[i-2][1] = int(header[i-2][1])
    f_head.close()
    #Example [[0, 4, 'T_ZERO', 'num'], [4, 4, 'HEAD_LEN', 'num']]
    return header

def head_get_info(key,header):
    #print "Looking for key=%s in header list (len=%d)"%(key,len(header))
    for i in range(len(header)):
        if header[i][2] == key:
            break
    if header[i][2] != key:
        print 'Key Error on Header: %s'%(key)
        exit()
    return header[i]
    
def write_head(val,offset,bram_header='header'):
    #print val,offset
    #print "Writing ",struct.unpack('>B',val)[0]," in offset ", offset
    fpga.write(bram_header,val,offset)
    
def write_header(field,val,header):
    record=head_get_info(field,header)
    #print record, field, val
    if record[3] == 'num':
        #if record[1] == 1:
            #valore=struct.pack('>B',val) NON FUNZIONA, ALMENO 2 BYTE!!
        #if record[1] == 2:
            #valore=struct.pack('>H',val)
        #if record[1] == 4:
        valore=struct.pack('>I',val)
    if record[3] == 'numarr':
        valore=struct.pack('>32L',val)
    if record[3] == 'str': 
        valore=val.ljust(record[1])       
    write_head(valore,record[0])
    
def read_header(field,header):
    record=head_get_info(field,header)
    if record[3] == 'num':
        #if record[1] == 1:
            #valore=struct.unpack('>B',fpga.read('header',1,record[0]))[0]
        #if record[1] == 2:
            #valore=struct.unpack('>H',fpga.read('header',2,record[0]))[0]
        #if record[1] == 4:
        valore=struct.unpack('>I',fpga.read('header',4,record[0]))[0]
    if record[3] == 'numarr':
        valore=struct.unpack('>32L',fpga.read('header',128,record[0]))        
    if record[3] == 'str': 
        valore=fpga.read('header',record[1],record[0])       
    return valore
    
def write_base_header(base_conf,header):
    for i in range(len(base_conf)):
        #print "Writing: ", base_conf.items()[i][0], base_conf.items()[i][1],
        write_header(base_conf.items()[i][0],base_conf.items()[i][1],header)
        #print " Read: ", read_header(base_conf.items()[i][0],header)
    
#def write_polbram(val,offset,bram):
 #   fpga.write(bram,val.ljust(record[1]),offset)

if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('birales_grab_jack_coeff.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--config', dest='config_file',default="configura_birales.conf",
        help='Select the Configuration file')
    p.add_option('-f', '--calib_file', dest='calib_file',default="amp_phase_coeff_from_jack.dat",
        help='Select the Configuration file')

    opts, args = p.parse_args(sys.argv[1:])
    config_file =  opts.config_file

    configura,base_conf =  birales_conf_parse.parse_settings(config_file)
    roach      = configura['roach_name']
    katcp_port = configura['katcp_port']
    adc_debug  = configura['adc_debug']
    fft_shift  = base_conf['fft_shift']
    bitstream  = configura['bitstream']
    header_file  = configura['header']
    header = head_get_keys(header_file)

    
    print('\n===================================\n')
    #fpga = corr.katcp_wrapper.FpgaClient('roach0')
    print('Connecting to ROACH board named "%s"... '%roach),
    fpga = corr.katcp_wrapper.FpgaClient(roach)
    time.sleep(1)
    if fpga.is_connected():
        print 'ok'
    else:
        print 'ERROR connecting to server %s on port %i.\n'%(roach,katcp_port)
        exit_fail()

    print('\n===================================\n')

    JACK_BRAM = 512 * 4 * 8 # NCoeff * DataWidth * Ants
    NEW_BRAM  = 128 * 4 * 8 # NCoeff * DataWidth * Ants

    print "Using calib file: "+opts.calib_file
    ofile = open(opts.calib_file,'r')

    reg_name ='amp_EQ'
    reg_type ='_coeff_bram'
     
    print "\nLoading Gain coefficients...",
    for i in range(4):
        amp=ofile.read(JACK_BRAM)
        new_amp = "".join([ a+b+c+d for a,b,c,d in  zip(amp[slice(0, len(amp), 16)], amp[slice(1, len(amp), 16)], amp[slice(2, len(amp), 16)], amp[slice(3, len(amp), 16)])])
        fpga.write(reg_name+str(i)+reg_type,new_amp,0) 
    print "done!"

    reg_name ='phase_EQ'
    reg_type ='_coeff_bram'

    print "\nLoading Phase coefficients...",
     
    for i in range(4):
        phase=ofile.read(JACK_BRAM)
        new_phase = "".join([ a+b+c+d for a,b,c,d in  zip(phase[slice(0, len(phase), 16)], phase[slice(1, len(phase), 16)], phase[slice(2, len(phase), 16)], phase[slice(3, len(phase), 16)])])
        fpga.write(reg_name+str(i)+reg_type,new_phase,0) 
    print "done!"

    os.system('./birales_read_coeff.py')

    ofile.close()
    





