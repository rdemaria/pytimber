import os, glob, time, datetime
import jpype
import numpy as np

"""
http://abwww.cern.ch/ap/dist/accsoft/cals/accsoft-cals-extr-client/PRO/build/dist/accsoft-cals-extr-client-nodep.jar
"""

try:
    # Try to get a lit of .jars from cmmnbuild_dep_manager.
    import cmmnbuild_dep_manager
    mgr = cmmnbuild_dep_manager.Manager()
    jarlist = mgr.jars()

    # Allows to use a local log4j.properties file
    jarlist.append(os.path.abspath("./"))

    if os.name == "nt":
        # We are running on Windows, Java expects a ";" between
        # classpaths.
        _jar = ";".join(jarlist)
    else:
        # ":" works for linux and maybe also some other systems?
        _jar = ":".join(jarlist)
except ImportError:
    # Could not import cmmnbuild_dep_manager -- it is probably not
    # installed. Fall back to using the locally bundled .jar file.
    _moddir=os.path.dirname(__file__)
    _jar=os.path.join(_moddir,'jars/accsoft-cals-extr-client-nodep.jar')

if not jpype.isJVMStarted():
    libjvm=jpype.getDefaultJVMPath()
    jpype.startJVM(libjvm,'-Djava.class.path=%s'%_jar)
else:
    print("Warning jpype started")


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
    elif type(t) is datetime.datetime:
        return Timestamp.valueOf( t.strftime("%Y-%m-%d %H:%M:%S") )
    else:  #Hopefully it's an int or double or something ;)
        sec=int(t)
        nanos=int((t-sec)*1e9)
        print( sec*1000 )
        tt=Timestamp(long(sec*1000))
        #tt.setNanos(nanos)
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
        """
            Search for parameter names.
            Wildcard is `%`.
        """
        types=VariableDataType.ALL
        vvv=self._md.getVariablesOfDataTypeWithNameLikePattern(pattern,types)
        return vvv.toString()[1:-1].split(', ')
    def get(self,pattern,t1,t2=None):
        """
         Queries the logging database with `pattern`.

         Returns data between t1 and t2
         If t2 is `None`, the last available data point before t1 is returned
         (search-range is one year)

         t1 and t2 can be python `datetime` objects or strings with this format:
         `2015-10-12 18:12:32.453255123`

         Returns:
         ---------
         `datetime` timestamp(s), data
        """
        ts1=toTimeStamp(t1)
        types=VariableDataType.ALL
        vvv=self._md.getVariablesOfDataTypeWithNameLikePattern(pattern,types)
        out={}
        for v in vvv:
            jvar=vvv.getVariable(v)
            if t2 is None:
                res=[self._ts.getLastDataPriorToTimestampWithinDefaultInterval(jvar,ts1)]
                datatype=res[0].getVariableDataType().toString()
            else:
                ts2=toTimeStamp(t2)
                res=self._ts.getDataInTimeWindow(jvar,ts1,ts2)
                datatype=res.getVariableDataType().toString()
            datas=[]
            tss=[]
            for tt in res:
                ts=tt.getStamp()
                ts=ts.fastTime/1000.+ts.getNanos()/1e9
                if datatype=='VECTORNUMERIC':
                   val=np.array(tt.getDoubleValues())
                elif datatype=='NUMERIC':
                   val=tt.getDoubleValue()
                else:
                   val=tt
                ts2 = datetime.datetime.fromtimestamp(ts)
                datas.append( val )
                tss.append( ts2 )
                #data.append((ts2,val))
            # We try to unpack the data as much as possible
            if len(datas) == 1:
                out[v]=( ts2, val )
            else:
                out[v]=( tss, datas )
        if len(out) == 1:
            return out[v]
        else:
            return out

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

