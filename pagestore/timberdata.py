"""
Wrapper around the  CERN logging database command line tool

Usage:
  open:   Parse and return the output of a query from a file name
  load:   Parse and return the output of a query from a file object
"""

import os
import time
import gzip
import numpy as np

from .localdate import parsedate, parsedate_myl



def load(fh,sep=',',t1=None,t2=None,debug=False,nmax=1e99,types=(float,float)):
  """Parse the output of the CERN logging database command line tool

  Usage:
    fh:    file handler
    sep:   separator ',' or '\\t'
    t1,t2: time interval read
    nmax:  maximum number of records per variable

  Returns:
    A dictionary for which for each variable found data is stored in a tuple
    of timestamps list and record list. Data is accesible by the variable name
    and a numeric index.
  """
  if type(t1) is str:
    t1=parsedate(t1)
  if type(t2) is str:
    t2=parsedate(t2)
  data={}
  dataon=False
  header=True
  for l in fh:
    if l.startswith('VARIABLE'):
      vname=l.split()[1]
      count=0
      if debug is True:
        print('Found var %s' % vname)
      if vname in data:
        t,v=data[vname]
      else:
        t,v=[],[]
        data[vname]=[t,v]
      dataon=False
      header=False
    elif l.startswith('Timestamp'):
      dataon=True
      tformat='string'
      if 'UNIX Format' in l:
        tformat='unix'
      elif 'LOCAL_TIME' in l:
        tformat='local'
      elif 'UTC_TIME' in l:
        tformat='utc'
    elif l=='\n':
      dataon=False
    elif dataon:
      ll=l.strip().split(sep)
      if tformat=='unix':
        trec=float(ll[0])/1000.
      elif tformat=='utc':
        trec=parsedate_myl(ll[0]+' UTC')
      else:
        trec=parsedate_myl(ll[0])
      if (t1 is None or trec>=t1) and (t2 is None or trec<=t2) and count<nmax:
        vrec=ll[1:]
        t.append(trec)
        v.append(vrec)
        count+=1
    elif header:
      if debug is True:
        print(l)
      log.append(l)
  if types is not None:
    ttype,vtype=types
    data=combine_data(data,vtype=vtype,ttype=ttype)
  return data

def combine_data(data,vtype=float,ttype=float):
  """Combine and change data type"""
  for k in data.keys():
    t,v=data[k]
    outv=[]
    outt=[]
    for tt,vv in zip(t,v):
        try:
          vvv=np.array(vv,dtype=vtype)
          outv.append(vvv)
          outt.append(tt)
        except ValueError:
          print("Warning %s at %s not converted"%(repr(vv),tt))
          pass
    t=np.array(outt,dtype=ttype)
    v=np.array(outv)
    if v.shape[-1]==1:
      v=v.reshape(v.shape[0])
    data[k]=[t,v]
  return data

def open(fn,sep=None,t1=None,t2=None,nmax=1e99,debug=False,
         types=(float,float)):
  """Load output of the CERN measurement database query from a filename

  Usage:  open("test.tsv")
    fn: filename
    sep: separator type

  Separator is inferred from the file extension as well
  """
  if sep is None:
    if fn.endswith('tsv') or fn.endswith('tsv.gz'):
      sep='\t'
    else:
      sep=','
  if fn.endswith('.gz'):
    fh=gzip.open(fn)
  else:
    fh=file(fn)
  data=load(fh,sep=sep,debug=debug,t1=t1,t2=t2,nmax=nmax,types=types)
  fh.close()
  return data


def openfnames(fnames,sep=None,t1=None,t2=None,nmax=1e99,debug=False):
  """Open a set of filenames"""
  mask=fnames[0]
  if sep is None:
    if mask.endswith('tsv') or mask.endswith('tsv.gz'):
      sep='\t'
    else:
      sep=','
  data=load(_icat(fnames),sep=sep,debug=debug,t1=t1,t2=t2,nmax=nmax)
  return data

def _icat(fnames):
  for fn in fnames:
    if fn.endswith('.gz'):
      for l in gzip.open(fn):
        yield l
    else:
      for l in file(fn):
        yield l


def pprint(data):
  """Pretty print data, last dimension is from the first record"""
  print("CERN DB data:")
  for k in data.keys():
    t,v=data[k]
    recl=set()
    for ii,vv in enumerate(v):
      recl.add(len(vv))
    recl=' or '.join([str(i) for i in recl])
    print("  ['%s'][1] => v[%d][%s]" %( k,len(t),recl))


def merge_out(fnames):
  data_final={}
  for vname in data_final.keys():
    data_final[vname]=([],[])
  for fn in fnames:
    data=load(fn)
    for vname in data.keys():
      t,v=data[vname]
      nt=data_final[vname][0].extend(t)
      nv=data_final[vname][1].extend(v)
    data_final['log'].extend(data['log'])
  return data_final




