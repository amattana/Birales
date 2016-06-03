#!/usr/bin/env python
"""
Read calibratrion coefficients from the F-engine 

 
"""
import corr,time,struct,sys,os
import birales_conf_parse
import numpy as n

antenne = 32
parallel_stream = 4

ant_per_stream  = antenne / parallel_stream 
MAP = [0,2,4,6,1,3,5,7]

totalchan = 128


if __name__ == '__main__':
    from optparse import OptionParser


    p = OptionParser()
    p.set_usage('birales_read_coeff.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-c', '--config', dest='config_file',default="configura_birales.conf",
        help='Select the Configuration file')
    p.add_option('-f', '--freq_channel', dest='freq_channel', type='int',default='102',
        help='Select the Frequency Channel (Default: 102)')

    opts, args = p.parse_args(sys.argv[1:])
    config_file =  opts.config_file

    configura,base_conf =  birales_conf_parse.parse_settings(config_file)
    roach      = configura['roach_name']
    katcp_port = configura['katcp_port']
    adc_debug  = configura['adc_debug']
    fft_shift  = base_conf['fft_shift']
    bitstream  = configura['bitstream']

    
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

    chan = opts.freq_channel / 2 # Same coeff used for even and odd adjacent channels

    reg_name ='phase_EQ'
    reg_type ='_coeff_bram'
     
    print "\nReading FPGA BRAMs Coefficients for frequency channel # %d ...\n\n"%(opts.freq_channel)
    for i in range(parallel_stream):
        for j in range(ant_per_stream):
            re = struct.unpack('>h',fpga.read("phase_EQ"+str(i)+"_coeff_bram",2,(chan*4)+(totalchan*4*MAP[j])))[0]
            im = struct.unpack('>h',fpga.read("phase_EQ"+str(i)+"_coeff_bram",2,2+(chan*4)+(totalchan*4*MAP[j])))[0]
            phase=complex(re / 2**15.,im/ 2**15.)
            g = struct.unpack('>i',fpga.read("amp_EQ"+str(i)+"_coeff_bram",4,(chan*4)+(totalchan*4*MAP[j])))[0]

            print("   Antenna # %2d\t  Phase: %3.1f\tdegs\tGain: %1.5f"%(j+ant_per_stream*i,180./n.pi*n.angle(phase), g/2**16.))
    print('\n===================================\n')


