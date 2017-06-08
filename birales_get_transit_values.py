#!/usr/bin/env python

import datetime
import sys,os
import struct
import time
import numpy as np
from matplotlib import pyplot
from matplotlib.font_manager import FontProperties
fontP = FontProperties()
fontP.set_size('xx-small')
import subprocess

tzero=1493385523

fullcorr=[]
i=0
j=0
while i < 32:
    j=i+1
    while j < 32:
        fullcorr += [str(i)+"-"+str(j)]
        j=j+1
    i=i+1


calibrazioni_joseph=[    1+0j, # 1N-1-1
                1.01320-73.8j, # 1N-3-1
                 1.03883-6.0j, # 1N-5-1
               1.05692-105.8j, # 1N-7-1
                1.23148-34.7j, # 1N-2-1 
               1.07147-153.4j, # 1N-4-1
               1.05794-104.6j, # 1N-6-1
               1.01880+154.3j, # 1N-8-1
                1.12404+21.7j, # 1N-1-2
               1.08150-40.45j, # 1N-3-2 
                1.13493-22.5j, # 1N-5-2 
               1.09354-118.1j, # 1N-7-2
                1.35692+45.7j, # 1N-2-2 
                1.10159+64.2j, # 1N-4-2
                1.16382-30.2j, # 1N-6-2
                1.07941-54.4j, # 1N-8-2
               1.12408+114.2j, # 1N-1-3
                1.16472+50.2j, # 1N-3-3 
                1.11993+51.3j, # 1N-5-3
                1.15251-89.0j, # 1N-7-3 
                1.30501+41.2j, # 1N-2-3 
                1.18613-20.8j, # 1N-4-3
                1.15295+38.5j, # 1N-6-3 
               1.08310-121.5j, # 1N-8-3 
               1.16490+173.9j, # 1N-1-4
                1.17760+43.1j, # 1N-3-4
               1.15337+132.5j, # 1N-5-4
                 1.25172+4.5j, # 1N-7-4
               1.34344+105.1j, # 1N-2-4
                 1.32123+7.4j, # 1N-4-4
                1.22923+90.0j, # 1N-6-4
                1.23430-62.8j] # 1N-8-4

calibrazioni=[ 
        1.00000000-0.j        ,  0.0+0.0j,
        0-0.0j, -0.0-0.0j ,
        0+0.0j,  0.0-0.0j ,
        0+0.0j,  0.0-0.0j,
        0.767274888390421-0.711468999940500j, -0.0+0.0j ,
        0.0+0.0j,  0.0+0.86310352j,
       -0.0+0.0j,  0.0-0.12980674j,
       -0.0+0.0j, -0.0+0.85049762j,
        0.983904398926433-0.114401690059313j, -0.0+0.0j,
        0.0+0.0j,  0.0-0.0j,
       -0.0+0.0j, -0.0+0.0j,
        0.0+0.0j,  0.0+0.0j,
        1.026922773831322-0.144272075711708j, -0.0-0.0j,
       -0.0-0.0j , -0.0+0.0j,
        0.0-0.0j, -0.0+0.0j,
       -0.0-0.0j, -0.0-0.0j]

calibrazioni=[1+0j,
0.85182-0.6994j,
1.0009-0.11412j,
1.0313-0.28181j,
-0.28584+1.0937j,
-0.63829+1.1525j,
0.64158+1.034j,
0.64175+0.93952j,
-0.91291-0.43865j,
-1.0661+0.014606j,
-1.0045-0.40839j,
-0.68419+0.76099j,
0.058641-0.99251j,
0.48699+1.0272j,
0.12454-1.1054j,
-0.51298-1.1041j,
-0.95078-0.38246j,
-0.44845+1.0078j,
-0.63609+0.79868j,
-0.93447+0.47313j,
-0.52131-0.99331j,
-0.46946-0.97592j,
-0.30854-1.0185j,
-0.52663-0.99606j,
1.0754+0.34395j,
0.53475-0.94856j,
-0.25695-1.1007j,
0.36185-1.0117j,
0.57973+0.78816j,
-0.8436+0.57809j,
0.96751+0.19829j,
1.0368+0.076295j] 


'''
calibrazioni=[1+0j,
0.85182-0.6994j,
1.0009-0.11412j,
1.0313-0.28181j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j,
0+0.0j] 
'''

remap=[ 0,  8, 16, 24,
        4, 12, 20, 28,
        1,  9, 17, 25,
        5, 13, 21, 29,
        2, 10, 18, 26, 
        6, 14, 22, 30,
        3, 11, 19, 27,
        7, 15, 23, 31]

'''
remap=[ 0,  1,  2,  3,
        4,  5,  6,  7,
        8,  9, 10, 11,
       12, 13, 14, 15,
       16, 17, 18, 19, 
       20, 21, 22, 23,
       24, 25, 26, 27,
       28, 29, 30, 31]
'''


def rescale(x):
    return x/2.**13

def pow(c):
    return c.real*c.real+c.imag*c.imag

def correlate(a,b):
    return a*b.conjugate()

def calibra(re,im, calib):
    zre=[]
    zim=[]
    for i in range(len(re)): 
        zre += [(re[i]*calib[remap[i%32]].real)-(im[i]*calib[remap[i%32]].imag)]
        zim += [(re[i]*calib[remap[i%32]].imag)+(im[i]*calib[remap[i%32]].real)]
    return zre, zim


def correla(re,im,baseline):
    a_re=re[remap[int(baseline.split("-")[0])]::32]
    a_im=im[remap[int(baseline.split("-")[0])]::32]
    b_re=re[remap[int(baseline.split("-")[1])]::32]
    b_im=im[remap[int(baseline.split("-")[1])]::32]
    c_re=[]
    c_im=[]
    for i in range(len(a_re)):
        c_re += [a_re[i]*b_re[i]+a_im[i]*b_im[i]]
        c_im += [a_re[i]*b_im[i]-a_im[i]*b_re[i]]
    return c_re, c_im


if __name__ == '__main__':
    from optparse import OptionParser
    p = OptionParser()
    p.set_usage('birales_get_transit_values.py <raw_data_file.dat> [options]')
    p.set_description(__doc__)
    #p.add_option('-p', '--skip_prog', dest='prog_fpga',action='store_false', default=True, 
    #    help='Skip FPGA programming (assumes already programmed).  Default: program the FPGAs')
    p.add_option('-f', '--in_file', dest='input_file',default="",
        help='The input file containing the raw data udp packets')
    p.add_option('-o', '--out_file', dest='output_file',default="",
        help='The output file in which to save the results')
    p.add_option('-r', '--radiosource', dest='radiosource',default="casa",
        help='RadioSource name (lower case: i.e. casa [default])')

    opts, args = p.parse_args(sys.argv[1:])
    in_file = opts.input_file

    if in_file=="":
        print "\n\nPlease specify an input file name.\n\nUsage: birales_udp_plot.py <raw_data_file.dat> [options]\n\n"
        exit()


    sample_rate=40000000
    pfb=512
    ant_num=32
    pkt_sec=1/( 1./(sample_rate/pfb)*ant_num)

    file_size=os.path.getsize(in_file)
    listacorr=fullcorr

    correlazioni_real=[]
    correlazioni_imag=[]
    for i in range(len(listacorr)):
        correlazioni_real += [[]]
        correlazioni_imag += [[]]


    # Backend Time details
    print "\n\nBackend Startup time:\t",datetime.datetime.utcfromtimestamp(tzero), " (UTC)\n"

    # Input File details
    a=open(in_file,"rb")
    t_start=datetime.datetime.utcfromtimestamp((struct.unpack(">Q",a.read(8))[0])*(1./(sample_rate/pfb)*ant_num)+tzero)
    a.seek(-8200,2)
    t_end=datetime.datetime.utcfromtimestamp((struct.unpack(">Q",a.read(8))[0])*(1./(sample_rate/pfb)*ant_num)+tzero)
    print "\nFile Recording Time: \n\n    Started at:\t\t", t_start, " (UTC) \n      Ended at:\t\t", t_end, " (UTC)\n"

    # RadioSource transit details
    calib_source=subprocess.check_output(['/home/oper/Birales/calib_source.py', datetime.datetime.strftime(t_start, "%Y/%m/%d"), "-r", opts.radiosource]).split()
    transit_time=datetime.datetime(int(calib_source[11].split("/")[0]),int(calib_source[11].split("/")[1]),int(calib_source[11].split("/")[2]),int(calib_source[12].split(":")[0]), int(calib_source[12].split(":")[1]), int(calib_source[12].split(":")[2]))
    if not ( transit_time > t_start and transit_time < t_end):
        calib_source=subprocess.check_output(['/home/oper/Birales/calib_source.py', datetime.datetime.strftime(t_end, "%Y/%m/%d"), "-r", opts.radiosource]).split()
        transit_time=datetime.datetime(int(calib_source[11].split("/")[0]),int(calib_source[11].split("/")[1]),int(calib_source[11].split("/")[2]),int(calib_source[12].split(":")[0]), int(calib_source[12].split(":")[1]), int(calib_source[12].split(":")[2]))
        
    if not ( transit_time > t_start and transit_time < t_end):
        print "\nUnable to compute the transit time for the given radiosource"        
    else:
        print "\nThe Transit Time for Radio Source '"+opts.radiosource+"' is: ",datetime.datetime.strftime(transit_time, "%Y/%m/%d %H:%M:%S (UTC)\n") 


    # Get Values at Transit time, like a "binary search"
   
    # Coarse Search, Faster
    a.seek(0)
    trovato=False
    t_goal_start = transit_time - datetime.timedelta((1./(24*60*60))/2) # half second before transit time
    t_goal_end   = transit_time + datetime.timedelta((1./(24*60*60))/2) # half second after transit time
    print "\nTRANSIT TIME:", datetime.datetime.strftime(transit_time, "%Y/%m/%d %H:%M:%S.%f")[:-3]
    print "\nT_GOAL_START:", datetime.datetime.strftime(t_goal_start, "%Y/%m/%d %H:%M:%S.%f")[:-3]
    print "T_GOAL_END:  ", datetime.datetime.strftime(t_goal_end, "%Y/%m/%d %H:%M:%S.%f")[:-3]
    print "\n\nCoarse Search, Faster...\n"
    pos=int((file_size/8200)/100*int(50))*8200                          # start from the middle of the file (50%)
    while not trovato:
        a.seek(pos)
        t_pkt = datetime.datetime.utcfromtimestamp((struct.unpack(">Q",a.read(8))[0])*(1./(sample_rate/pfb)*ant_num)+tzero)
        sys.stdout.write("\r%3.2f%% - %s - Delta: %3.2f secs   "%((a.tell()*100./file_size), datetime.datetime.strftime(t_pkt, "%Y/%m/%d %H:%M:%S.%f")[:-3], (t_pkt - t_goal_start).total_seconds()))
        sys.stdout.flush()
        if t_pkt > t_goal_start and t_pkt < t_goal_end or t_pkt - t_goal_start < datetime.timedelta(0,2,0):
            trovato = True
            a.seek(a.tell()-8)
        elif t_pkt > t_goal_end:
            # seek to about the t_goal-start (without taking into account pkt loss)
            #print a.tell(), int((((t_pkt - t_goal_start).total_seconds())*pkt_sec)*8200), (t_pkt - t_goal_start).total_seconds() 
            pos = (a.tell()-8-(int(((t_pkt - t_goal_start).total_seconds()/2)*pkt_sec)*8200))
        elif t_pkt < t_goal_start:
            #print a.tell(), int((((t_goal_start-t_pkt).total_seconds())*pkt_sec)*8200), (t_goal_start-t_pkt).total_seconds() 
            pos = (a.tell()+8192+(int(((t_goal_start-t_pkt).total_seconds()/2)*pkt_sec)*8200))

    print "\n\nFine Search, slower...\n\n"
 
    # Fine Search, Slower
    pos = (a.tell()-int(2*pkt_sec)*8200)
    trovato=False
    while not trovato:
        a.seek(pos)
        t_pkt = datetime.datetime.utcfromtimestamp((struct.unpack(">Q",a.read(8))[0])*(1./(sample_rate/pfb)*ant_num)+tzero)
        sys.stdout.write("\r%3.2f%% - %s - Delta: %3.2f secs   "%((a.tell()*100./file_size), datetime.datetime.strftime(t_pkt, "%Y/%m/%d %H:%M:%S.%f")[:-3], (t_pkt - t_goal_start).total_seconds()))
        sys.stdout.flush()
        if t_pkt > t_goal_start:
            trovato=True
        else:
            pos = (a.tell()+8192)
             
    a.seek(a.tell()-8)
    print "\n\nPKT Time for 1 second of transit time starts at", datetime.datetime.strftime(t_pkt, "%Y/%m/%d %H:%M:%S.%f")[:-3], "(UTC)\n\n"

    iterazione=0
    if len(listacorr)>0:
        correlazione_real=[]
        correlazione_imag=[]
        for i in range(len(listacorr)):
            #correlazione += [[]]
            correlazione_real += [[]] 
            correlazione_imag += [[]] 

    while (t_pkt-t_goal_start)<datetime.timedelta(0,1):

        t_pkt = datetime.datetime.utcfromtimestamp((struct.unpack(">Q",a.read(8))[0])*(1./(sample_rate/pfb)*ant_num)+tzero)      

        data=a.read(8192)
        if not data or len(data)<8192:
            break
        v=struct.unpack(">"+str(2048)+"i",data)

        ant_re=v[0::2]
        ant_im=v[1::2]

        ant_re, ant_im = calibra(ant_re, ant_im, calibrazioni)

        if len(listacorr)>0:
            for i in range(len(listacorr)):
                corr_real, corr_imag = correla(ant_re, ant_im, listacorr[i])
                correlazione_real[i] += corr_real
                correlazione_imag[i] += corr_imag
        iterazione = iterazione + 1


    if len(listacorr)>0:
        for i in range(len(listacorr)):
            c=0
            for j in correlazione_real[i]:
                c = c + j
            correlazioni_real[i] += [c]
            c=0
            for j in correlazione_imag[i]:
                c = c + j
            correlazioni_imag[i] += [c]
            #correlazioni[i] += [c]

    out=open(opts.output_file, 'w')
    for i in range(len(listacorr)):
        if correlazioni_imag[i][0]>0:
            valore=str(int(listacorr[i].split("-")[0])+1)+" "+str(int(listacorr[i].split("-")[1])+1)+" "+str(correlazioni_real[i][0])+"+"+str(correlazioni_imag[i][0])+"j\n"
        else:
            valore=str(int(listacorr[i].split("-")[0])+1)+" "+str(int(listacorr[i].split("-")[1])+1)+" "+str(correlazioni_real[i][0])+str(correlazioni_imag[i][0])+"j\n"
        out.write(valore)
    out.close()
    


