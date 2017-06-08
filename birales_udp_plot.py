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
'''
calibrazioni=[1+0j,
0.87434-0.71788j,
0.93409-0.10651j,
1.0002-0.27331j,
-0.2973+1.1375j,
-0.6617+1.1948j,
0.64874+1.0455j,
0.66346+0.97131j,
-0.92194-0.44299j,
-1.0165+0.013927j,
-0.98464-0.40032j,
-0.69397+0.77186j,
0.053716-0.90916j,
0.46077+0.97193j,
0.13392-1.1887j,
-0.53444-1.1503j,
-0.95103-0.38256j,
-0.47461+1.0666j,
-0.6238+0.78326j,
-0.91671+0.46414j,
-0.53038-1.0106j,
-0.47153-0.98023j,
-0.3106-1.0253j,
-0.50201-0.94948j,
1.1127+0.35591j,
0.55647-0.98708j,
-0.26922-1.1533j,
0.34809-0.97327j,
0.59131+0.80392j,
-0.82876+0.56791j,
0.95533+0.19579j,
1.016+0.074763j
]
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
    p.set_usage('birales_udp_plot.py <raw_data_file.dat> [options]')
    p.set_description(__doc__)
    #p.add_option('-p', '--skip_prog', dest='prog_fpga',action='store_false', default=True, 
    #    help='Skip FPGA programming (assumes already programmed).  Default: program the FPGAs')
    p.add_option('-a', '--autocorr', dest='auto',action='store_true', default=False, 
        help='Compute and plot autocorrelations')
    p.add_option('-b', '--beamf', dest='beam',action='store_true', default=False, 
        help='Compute and plot the Beam')
    p.add_option('-f', '--in_file', dest='input_file',default="",
        help='The input file containing the raw data udp packets')
    p.add_option('-i', '--integr', dest='integration',default=1.0,
        help='Integration time (unit: seconds, default 1.0)')
    p.add_option('-c', '--correlate', dest='correlate',default="",
        help='Antenna to be correlated like 0-2,0-3, (no space between ant name)')
    p.add_option('-p', '--phase', dest='fasi',default="",
        help='The Correction Phases File')
    p.add_option('-s', '--skip', dest='start_time',default=0,
        help='Start computing from percentage of the file (i.e.: 20 for 20%)')
    p.add_option('-d', '--decimation', dest='decimation',default=1.0,
        help='Decimation factor (seconds)')
    p.add_option('-r', '--radiosource', dest='radiosource',default="casa",
        help='RadioSource name (lower case: i.e. casa [default])')

    p.add_option('-e', '--end', dest='end_time',default=100,
        help='Stop at percentage of the file (i.e.: 70 for 70%)')

    opts, args = p.parse_args(sys.argv[1:])
    in_file = opts.input_file

    if opts.auto:
        print "\nAutoCorrelations enabled!"

    if in_file=="":
        print "\n\nPlease specify an input file name.\n\nUsage: birales_udp_plot.py <raw_data_file.dat> [options]\n\n"
        exit()


    sample_rate=40000000
    pfb=512
    ant_num=32
    pkt_sec=1/( 1./(sample_rate/pfb)*ant_num)

    file_size=os.path.getsize(in_file)

    integrazione = float(opts.integration) # per integrazioni di 1 secondo
    listacorr=opts.correlate.split(",")
    listacorr=fullcorr
    if listacorr==[""]:
        listacorr=[]
    #correlazione=[]
    #correlazioni=[]
    correlazioni_real=[]
    correlazioni_imag=[]
    for i in range(len(listacorr)):
        #correlazione += [[]]
        #correlazioni += [[]]
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


    a.seek(0)    
    if not int(opts.start_time)==0:
        pos=int((file_size/8200)/100*int(opts.start_time))*8200
        a.seek(pos)
    first_cont=struct.unpack(">Q",a.read(8))[0]
    a.close()
    started=time.time()
    auto=[]

    if not opts.fasi == "":
        print "\nData will be calibrated by using the file "+opts.fasi
        if os.path.exists(opts.fasi):
            calibrazioni=leggi_fasi()
        else:
            print "\n * The given file for phase calibration doesn't exists!"
            exit()

    if opts.beam:
        beam=[]

    print "\n"
    prev_cont = first_cont-1

    try:
        a=open(in_file,"rb")

        if not int(opts.start_time)==0:
            pos=int((file_size/8200)/100*int(opts.start_time))*8200
            a.seek(pos)
            print "\nJumping to byte #", a.tell()," ("+opts.start_time+"% of the file)...\n"

        while True:
            tempo=time.time()
            iterazione=0
            ants=[]
            if len(listacorr)>0:
                #correlazione=[]
                correlazione_real=[]
                correlazione_imag=[]
                for i in range(len(listacorr)):
                    #correlazione += [[]]
                    correlazione_real += [[]] 
                    correlazione_imag += [[]] 

            if opts.beam:
                beam_part=[]

            while iterazione<(pkt_sec*integrazione):
               
                # Contatore
                data=a.read(8)
                if not data:
                    break
                cont=struct.unpack(">Q",data)[0]
                if not int(opts.decimation)>1:
                    if not cont==prev_cont+1:
                        sys.stdout.write("* "+str(cont-prev_cont+1)+" * - ")
                        sys.stdout.flush()
                    prev_cont=cont

                #print "Count: ", cont
                # Dati, ogni pkt 32 samples * 32 antennas * 8Byte (4Re+4Im)
                data=a.read(8192)
                if not data or len(data)<8192:
                    break
                
                v=struct.unpack(">"+str(2048)+"i",data)

                ant_re=v[0::2]
                ant_im=v[1::2]

                #if not opts.fasi == "":
                ant_re, ant_im = calibra(ant_re, ant_im, calibrazioni)
                
                if opts.beam: 
                    for i in range(32):
                        beam_part += [np.power(np.abs(np.sum(np.array(ant_re[i*32:i*32+32]) + 1j* np.array(ant_im[i*32:i*32+32]))),2)] 

                if len(listacorr)>0:
                    for i in range(len(listacorr)):
                        corr_real, corr_imag = correla(ant_re, ant_im, listacorr[i])
                        #correlazione[i] += correla(ant_re, ant_im, listacorr[i])
                        correlazione_real[i] += corr_real
                        correlazione_imag[i] += corr_imag

                if opts.auto:    
                    for i in range(32):
                        c=0
                        cre=ant_re[i::32]
                        cim=ant_im[i::32]
                        for j in range(len(cre)):
                            c = c + cre[j]*cre[j]+cim[j]*cim[j]
                        ants += [c]

                iterazione = iterazione + 1

            if not data: 
                break

            if opts.beam:
                beam += [np.array(beam_part).sum()]

            if opts.auto:    
                for i in range(32):
                    c=0
                    for j in ants[i::32]:
                        c = c + j#/(pkt_sec*integrazione)
                    auto += [c]

            if len(listacorr)>0:
                for i in range(len(listacorr)):
                    c=0
                    for j in correlazione_real[i]:
                        c = c + j#/(pkt_sec*integrazione)
                    correlazioni_real[i] += [c]
                    c=0
                    for j in correlazione_imag[i]:
                        c = c + j#/(pkt_sec*integrazione)
                    correlazioni_imag[i] += [c]
                    #correlazioni[i] += [c]

            if opts.decimation>1:
                pos=a.tell()+((8200*2441)*int(opts.decimation))
                a.seek(pos)
                #print "\nJumping to byte #", a.tell()," ("+opts.start_time+"% of the file)...\n"
                

            percentage=(a.tell()*100./file_size)
            rem_time=(time.time()-started)/(percentage-int(opts.start_time))*(100-percentage)
            end_time=datetime.datetime.strftime(datetime.datetime.fromtimestamp(time.time()+rem_time),'%H:%M:%S')
            sys.stdout.write("\rProcessed %3.3f %%,  Integration done in %3.1f seconds, Remaining time is %02d:%02d:%02d, Finish at %s "%(percentage, time.time()-tempo, rem_time/3600, rem_time%3600/60, rem_time%3600%60, end_time))
            sys.stdout.flush()
        a.close()
        print "\nRead",cont-first_cont+1, "packets of","%3.1f"%((cont-first_cont+1)/pkt_sec),"seconds of acquisition in", "%3.1f"%(time.time()-started),"seconds"

        if opts.auto:    
            for i in range(32):
                pyplot.plot(auto[i::32], label="ANT-%2.0f"%(remap[i]))
            pyplot.legend(bbox_to_anchor=(1.05, 1), loc=1, borderaxespad=0., prop = fontP,fancybox=True,shadow=False,title='LEGEND')
            pyplot.show()

        if opts.beam:
            fig = pyplot.figure() 
            ax = fig.add_subplot(1,1,1)
            ax.plot(beam)
            #ax.set_yscale('log')    
            ax.set_title("BEAM")
            ax.yaxis.tick_left()
            pyplot.show()

        if len(listacorr)>0:
            for i in range(len(listacorr)):
                pyplot.plot(correlazioni_real[i], label="ANT-"+listacorr[i].split("-")[0]+"_ANT-"+listacorr[i].split("-")[1])
            pyplot.legend(bbox_to_anchor=(1.05, 1), loc=1, borderaxespad=0., prop = fontP,fancybox=True,shadow=False,title='LEGEND')
            pyplot.show()

    except KeyboardInterrupt:
        print "\nExiting before the end...\n"
        a.close()

        if opts.auto:  
            for i in range(32):
                pyplot.plot(auto[i::32], label="ANT-%2.0f"%(remap[i]))
            pyplot.legend(bbox_to_anchor=(1.05, 1), loc=1, borderaxespad=0., prop = fontP,fancybox=True,shadow=False,title='LEGEND')
            pyplot.show()

        if opts.beam:
            fig = pyplot.figure() 
            ax = fig.add_subplot(1,1,1)
            ax.plot(beam)
            #ax.set_yscale('log')    
            ax.set_title("BEAM")
            ax.yaxis.tick_left()
            pyplot.show()

        if len(listacorr)>0:
            print "\nPlotting "+str(len(listacorr))+" series of "+str(len(correlazioni_real[0]))+" samples\n"
            for i in range(len(listacorr)):
                pyplot.plot(correlazioni_real[i], label="ANT-"+listacorr[i].split("-")[0]+"_ANT-"+listacorr[i].split("-")[1])
            pyplot.legend(bbox_to_anchor=(1.05, 1), loc=1, borderaxespad=0., prop = fontP,fancybox=True,shadow=False,title='LEGEND')
            pyplot.show()


