import time,pytz
import re
from dateutil.tz import gettz,tzlocal
from datetime import datetime

myzones={'bnl' : 'America/New_York',
       'cern': 'Europe/Zurich',
       'fnal': 'America/Chicago',
       'lbl' : 'America/Los_Angeles',
       'Z'   : 'UTC'}

myfmt={'myf': '%Y-%m-%d--%H-%M-%S--%z',
       'myh': '%Y-%m-%d %H:%M:%S %z',
       'myl': '%Y-%m-%d %H:%M:%S.SSS',
       'rfc': '%a, %d %b %Y %H:%M:%S %z',
       'epoch' :'%s',
       'iso' : '%Y%m%dT%H%M%S%z',
       'cernlogdb' : '%Y%m%d%H%M%SCET',
       }

# predefined time zones
utc = pytz.timezone('UTC')

def parsedate_myl(s,zone='cern'):
  """Read a string in the '2010-06-10 00:00:00.123' format and return
  the unix time for the time zone *zone*."""
  stime='00:00:00'
  ssec=0
  parts=s.split(' ')
  sdate=parts[0]
  if len(parts)>1:
    stime=parts[1]
  stimes=stime.split('.')
  if len(stimes)==2:
    stime=stimes[0]
    ssec=int(float('0.'+stimes[1])*1e6)
  try:
    stz=gettz(myzones.get(zone,zone))
  # catch case if stz is not defined
  except TypeError:
    stz=gettz(myzones.get('cern','cern'))
  dt_stz = datetime.strptime('%s %s'%(sdate,stime),'%Y-%m-%d %H:%M:%S')
  dt_stz = dt_stz.replace(tzinfo=stz)
  # mktime is only valid for localtime -> convert to local timezone
  ltz = gettz()
  dt_local = dt_stz.astimezone(ltz)
  epoch=time.mktime(dt_local.timetuple())+ssec*1.e-6
  return epoch

def parsedate(t,zone='cern'):
  try:
    if type(t) is complex:
      t=time.time()-t.imag
    float(t)
    return t
  except ValueError:
    return parsedate_myl(t,zone='cern')

def dumpdate(t=None,fmt='%Y-%m-%d %H:%M:%S.SSS',zone='cern'):
  """
  converts unix time [float] to time in time zone *zone* [string].

  Paramters:
  ----------
  t : unix time [s], if t = None the time now is used
  fmt : = format string for output
  zone : time zone, either predefined (bnl,cern,fnal,lbl and z for 
         utc time) or datetime timezones (e.g. 'Europe/Zurich' for 
         cern).
         If zone = None local time is used
  """
  if t is None:
    t=time.time()
  ti = int(t)
  tf = t-ti
  if zone is None:
    s = time.strftime(fmt,time.localtime(t))
  else:
    utc_dt = datetime.utcfromtimestamp(t)
    utc_dt = utc_dt.replace(tzinfo = utc)
    tz = pytz.timezone(myzones.get(zone,zone))
    tz_dt = utc_dt.astimezone(tz)
    s = tz_dt.strftime(fmt)
  if 'SSS' in s:
    s=s.replace('SSS','%03d'%(tf*1000))
  return s

def dumpdateutc(t=None,fmt='%Y-%m-%d %H:%M:%S.SSS'):
  """
  converts unix time [float] to utc time [string]
  Parameters:
  -----------
  t : unix time [s], if t = None the time now is used
  fmt : = format string for output
  """
  if t is None:
    t=time.time()
  ti=int(t)
  tf=t-ti
  utc_dt = datetime.utcfromtimestamp(t)
  s=utc_dt.strftime(fmt)
  if 'SSS' in s:
    s=s.replace('SSS','%03d'%(tf*1000))
  return s


#from objdebug import ObjDebug as object

class SearchName(object):
  def search(self,regexp):
    r=re.compile(regexp,re.IGNORECASE)
    res=[ l for l in self.get_names() if r.search(l) is not None]
    return res
  __floordiv__=search
  def _parsenames(self,names):
    if not hasattr(names,'__iter__'):
      out=[]
      for name in names.split(','):
        if name.startswith('/'):
          res=self.search(name[1:])
          print("Using the following names:")
          for name in res:
            print(name)
          out.extend(res)
        else:
          out.append(name)
      names=out
    return names

