import os, glob, time
import time

import jpype

import numpy as np

"""
http://abwww.cern.ch/ap/dist/accsoft/cals/accsoft-cals-extr-client/PRO/build/dist/accsoft-cals-extr-client-nodep.jar
"""

_moddir=os.path.dirname(__file__)
_jar=os.path.join(_moddir,'accsoft-cals-extr-client-nodep.jar')

if not jpype.isJVMStarted():
  libjvm=jpype.getDefaultJVMPath()
  jpype.startJVM(libjvm,'-Djava.class.path=%s'%_jar)
else:
  print "Warning jpype started"


#defs
cern=jpype.JPackage('cern')
org =jpype.JPackage('org')
java =jpype.JPackage('java')
ServiceBuilder=cern.accsoft.cals.extr.client.service.ServiceBuilder
DataLocationPreferences=cern.accsoft.cals.extr.domain.core.datasource.DataLocationPreferences
VariableDataType=cern.accsoft.cals.extr.domain.core.constants.VariableDataType
Timestamp=java.sql.Timestamp

null=org.apache.log4j.varia.NullAppender()
org.apache.log4j.BasicConfigurator.configure(null);



def toTimeStamp(t):
    if type(t) is str:
        return Timestamp.valueOf(t)
    else:
        sec=int(t)
        nanos=int((t-sec)*1e9)
        #print sec*1000
        tt=Timestamp(long(sec*1000))
        tt.setNanos(nanos)
        return tt

source_dict={'mdb': DataLocationPreferences.MDB_PRO,
        'ldb': DataLocationPreferences.LDB_PRO,
        'all': DataLocationPreferences.MDB_AND_LDB_PRO}

def toStringList(myArray):
  myList = java.util.ArrayList()
  for s in myArray:
     myList.add(s)
  return myList

class LoggingDB(object):
    def __init__(self,appid='LHC_MD_ABP_ANALYSIS',clientid='BEAM_PHYSICS',source='mdb'):
        loc=source_dict[source]
        self._builder=ServiceBuilder.getInstance(appid,clientid,loc)
        self._md=self._builder.createMetaService()
        self._ts=self._builder.createTimeseriesService()
        self.tree=Hierarchy('root',None,None,self._md)
    def search(self,pattern):
      types=VariableDataType.ALL
      vvv=self._md.getVariablesOfDataTypeWithNameLikePattern(pattern,types)
      return vvv.toString()[1:-1].split(', ')
    def get(self,pattern,t1,t2):
        ts1=toTimeStamp(t1)
        ts2=toTimeStamp(t2)
        types=VariableDataType.ALL
        vvv=self._md.getVariablesOfDataTypeWithNameLikePattern(pattern,types)
        out={}
        for v in range(vvv.getVariableCount()):
           jvar=vvv.getVariable(v)
           res=self._ts.getDataInTimeWindow(jvar,ts1,ts2)
           data=[]
           datatype=res.getVariableDataType().toString()
           for ntt in range(res.size()):
               tt=res.get(ntt)
               ts=tt.getStamp()
               ts=ts.fastTime/1000.+ts.getNanos()/1e9
               if datatype=='VECTORNUMERIC':
                  val=np.array(tt.getDoubleValues())
               elif datatype=='NUMERIC':
                  val=tt.getDoubleValue()
               else:
                  val=tt
               data.append((ts,val))
           out[jvar.toString()]=zip(*data)
        return out
   # def __dir__(self):
   #     return []


def clean_name(s):
    if s[0].isdigit():
        s='_'+s
    out=[]
    for ss in s:
        if ss in ' _;><':
            out.append('_')
        else:
            out.append(ss)
    return ''.join(out)


class Hierarchy(object):
    def __init__(self,name,obj,src,varsrc):
        self.name=name
        self.obj=obj
        self.varsrc=varsrc
        if src is not None:
          self.src=src
    def _get_childs(self):
        if self.obj is None:
            objs=self.src.getHierachies(1)
        else:
            objs=self.src.getChildHierarchies(self.obj)
        return dict([(clean_name(hh.hierarchyName),hh) for hh in objs])
    def __getattr__(self,k):
        if k=='src':
            self.src=self.varsrc.getAllHierarchies()
            return self.src
        elif k=='_dict':
            self._dict=self._get_childs()
            return self._dict
        else:
            return Hierarchy(k,self._dict[k],self.src,self.varsrc)
    def __dir__(self):
        return sorted(self._dict.keys())
    def __repr__(self):
        if self.obj is None:
          return "<Top Hierarchy>"
        else:
          name=self.obj.getHierarchyName()
          desc=self.obj.getDescription()
          return "<%s: %s>"%(name,desc)
    def get_vars(self):
        if self.obj is not None:
          vvv=self.varsrc.getVariablesOfDataTypeAttachedToHierarchy(self.obj,VariableDataType.ALL)
          return vvv.toString()[1:-1].split(', ')
        else:
          return []

