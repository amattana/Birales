#!/usr/bin/python
"""
Output LST, Julian date, and Sun position at the provided location and time.
Input times can be julian dates, or UTC times in 'year/month/day hour:minute:second' format.
Outputs a list of sources and transit times at this location and day, given a user provided catalogue and selection criteria.
"""

import sys, optparse, ephem
import operator, numpy as n

o = optparse.OptionParser()
o.set_usage('calib_source.py [options] datetime1 datetime2 ...')
o.set_description(__doc__)
o.add_option('--lat', dest='lat', default=44.523733, type='float',
    help='Latitude (N) in degrees, Default: 44.523733 (Medicina)')
o.add_option('--lon', dest='lon', default=11.645929, type='float',
    help='Longitude (E) in degrees, Default: 11.645929 (Medicina)')
o.add_option('-f','--minflux', dest='minflux', default=50.0, type='float',
    help='Minimum flux. Default=50')
o.add_option('--mindec', dest='mindec', default=-90, type='float',
    help='Minimum declination. Default=-90')
o.add_option('--maxdec', dest='maxdec', default=90, type='float',
    help='Maximum declination. Default=90')
o.add_option('-s', '--sort_key', dest='sort_key', type='string', default='transit',
        help='Key by which to sort sources. Choices: transit, flux, name, ra, dec, ha. Default: transit')
o.add_option('-d', '--descending', dest='descending', action='store_true', default=False,
        help='Use this flag to sort sources in descending order')
o.add_option('-c', '--cat', dest='cat', default='/home/lessju/Code/medicina/poxy/scripts/analysis/VIII_1A_3cr-120303b.csv', type='string',
    help='Catalogue to load. Default is 3CR at /home/lessju/Code/medicina/poxy/scripts/analysis/VIII_1A_3cr-120303b.csv')
o.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
    help='Be verbose (mainly about reading the catalogue file).')
o.add_option('-r', '--radiosource', dest='radiosource', default='', type='string',
    help='The Radiosource to query. If not given show all')
opts, args = o.parse_args(sys.argv[1:])

def juldate2ephem(num):
    """Convert Julian date to ephem date, measured from noon, Dec. 31, 1899."""
    return ephem.date(num - 2415020.)

def ephem2juldate(num):
    """Convert ephem date (measured from noon, Dec. 31, 1899) to Julian date."""
    return float(num + 2415020.)

def get_common_name(name):
    common_name = {'3C144':'tau',
                   '3C461':'casa',
                   '3C405':'cyg',
                   '3C274':'virgo'}
    if name in common_name.keys():
        return common_name[name]
    else:
        return ''

sun=ephem.Sun()
obs=ephem.Observer()
obs.long=opts.lon*(ephem.pi/180.)
obs.lat=opts.lat*(ephem.pi/180.)
obs.epoch=2000.0

catfile = opts.cat
if opts.cat == '':
    print "Please specify a catalogue with the -c switch"
    exit()
#print "Opening catalogue \'%s\'"%catfile
cat = open(catfile,'r')

#Read the catalogue file, ignoring commented lines
catstr = ''
#print "Reading catalogue \'%s\'"%catfile
for line in cat.readlines():
    if line[0] != '#':
        catstr = catstr + line

catlist = catstr.split('\n')[2:] #skip title and unit lines
n_entries = len(catlist)
epoch = 1950

body_list = []
if opts.verbose:
    print '######################################################################################################'
for rn,row in enumerate(catlist):
    if row=='':
        break
    if opts.verbose:
        print 'Parsing object %d of %d:'%(rn+1,n_entries),
    cells = row.split(',')
    name = '3C'+ cells[0]
    #print row,cells
    ra = cells[1].replace(' ',':')
    dec = cells[2].replace(' ',':')
    flux = n.log10(float(cells[3])) #log flux, so we can store in the magnitude field, which has a relatively small range
    if opts.verbose:
        print ' %s, RA:%s, DEC:%s, FLUX:%.2f'%(name,ra,dec,10**flux)
    ephemline = '%s,f,%s,%s,%s,%d'%(name,ra,dec,flux,epoch)
    body = ephem.readdb(ephemline)
    body_list.append(body)
if opts.verbose:
    print '######################################################################################################'

if len(args) == 0: args = [str(ephem.julian_date())]
for date in args:
    #print '##########################################################################################################################'
    if '/' in date:
        jd = ephem.julian_date(date)
    else:
        jd = float(date)

    obs.date=juldate2ephem(jd)

    sun.compute(obs)
    lst = obs.sidereal_time()
    #print 'LST:', lst,
    ra=obs.sidereal_time()
    #print '(',(ra.real/(ephem.pi))*180.,')',
    #print '     Julian Date:', jd,
    #print '     Day:', obs.date
    #print 'Sun is at (RA, DEC): (%s,%s)' %(str(sun.ra), str(sun.dec))

    common_name = {'3C144':'tau',
                   '3C461':'casa',
                   '3C405':'cyg',
                   '3C274':'virgo'}

    for body in body_list:
        body.compute(obs)
        if body.name in common_name.keys():
            obs.date=juldate2ephem(jd)
            next_transit = obs.next_transit(body)
            time_to_transit = next_transit-juldate2ephem(jd)
            ha = lst - body.ra
            #unwrap
            if ha > n.pi:
                ha = ha-2*n.pi
            elif ha < -n.pi:
                ha = ha + 2*n.pi
            
            if (opts.radiosource == get_common_name(body.name)) or (opts.radiosource==''):
                print "%-7s %+8s : RA: %11s  DEC: %11s  FLUX: %8s  TRANSIT (UTC): %-20s (%.3f)    HA: %12s"%(body.name,get_common_name(body.name),body.ra,body.dec,'%.2f'%(10**body.mag),next_transit,ephem.julian_date(next_transit),ephem.hours(ha))

