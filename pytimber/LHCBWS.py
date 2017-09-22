import os
from IPython.core.debugger import Tracer;

try:
  import numpy as np
  import matplotlib.pyplot as pl
  from scipy.optimize import curve_fit
except ImportError:
  print("""No module found: numpy, matplotlib and scipy modules should 
    be present to run pytimbertools""")

import pytimber
import pytimber.toolbox as tb

from .dataquery import set_xaxis_date
from .localdate import parsedate,dumpdate

def extract_bunch_selection(bunch_selection_binary):
  """
  The bunch selection is stored in binary format. This
  function reads the binary file and returns
  an array with the selected bunches
  
  Parameters:
  -----------
  bunch_selection_binary: Binary data from 
    LHC.BWS.5[LR]4.B[12]H[12]:BUNCH_SELECTION

  Returns:
  --------
  numpy array of selected bunches, e.g. [0,20,80]
  """
  bunchSelection=[]
  main_counter=0
  for bsb in bunch_selection_binary:
    if bsb!=0:
      counter=0
      nbr=bin(int(float(bsb))&0xffffffff)
      for bit in nbr[2:][::-1]:
        if bit=='1':
            bunchSelection.append(main_counter+counter)
        counter+=1
    main_counter+=32
  return bunchSelection
def _bws_timber_variables():
  """
  returns dictionary with hardcoded timber variables.

  Parameter:
  ----------
  var: list of variable names (string)
  """
  timber_variables = {}
  timber_variables['B1'] = [u'LHC.BWS.5R4.B1H2:NB_GATES',
    u'LHC.BWS.5R4.B1V2:NB_GATES',u'LHC.BWS.5R4.B1H2:BUNCH_SELECTION',
    u'LHC.BWS.5R4.B1V2:BUNCH_SELECTION',u'LHC.BWS.5R4.B1H.APP.IN:BETA',
    u'LHC.BWS.5R4.B1H.APP.OUT:BETA',u'LHC.BWS.5R4.B1V.APP.IN:BETA',
    u'LHC.BWS.5R4.B1V.APP.OUT:BETA',
    u'LHC.BWS.5R4.B1H.APP.IN:EMITTANCE_NORM',
    u'LHC.BWS.5R4.B1H.APP.OUT:EMITTANCE_NORM',
    u'LHC.BWS.5R4.B1V.APP.IN:EMITTANCE_NORM',
    u'LHC.BWS.5R4.B1V.APP.OUT:EMITTANCE_NORM',
    u'LHC.BWS.5R4.B1H2:PROF_POSITION_IN',
    u'LHC.BWS.5R4.B1H2:PROF_POSITION_OUT',
    u'LHC.BWS.5R4.B1V2:PROF_POSITION_IN',
    u'LHC.BWS.5R4.B1V2:PROF_POSITION_OUT',
    u'LHC.BWS.5R4.B1H2:PROF_DATA_IN',
    u'LHC.BWS.5R4.B1H2:PROF_DATA_OUT',
    u'LHC.BWS.5R4.B1V2:PROF_DATA_IN',
    u'LHC.BWS.5R4.B1V2:PROF_DATA_OUT',
    u'LHC.BWS.5R4.B1H2:GAIN',u'LHC.BWS.5R4.B1V2:GAIN',
    u'LHC.BOFSU:OFC_ENERGY']
  timber_variables['B2']=[u'LHC.BWS.5L4.B2H1:NB_GATES',
    u'LHC.BWS.5L4.B2V2:NB_GATES',u'LHC.BWS.5L4.B2H1:BUNCH_SELECTION',
    u'LHC.BWS.5L4.B2V2:BUNCH_SELECTION',u'LHC.BWS.5L4.B2H.APP.IN:BETA',
    u'LHC.BWS.5L4.B2H.APP.OUT:BETA',u'LHC.BWS.5L4.B2V.APP.IN:BETA',
    u'LHC.BWS.5L4.B2V.APP.OUT:BETA',
    u'LHC.BWS.5L4.B2H.APP.IN:EMITTANCE_NORM',
    u'LHC.BWS.5L4.B2H.APP.OUT:EMITTANCE_NORM',
    u'LHC.BWS.5L4.B2V.APP.IN:EMITTANCE_NORM',
    u'LHC.BWS.5L4.B2V.APP.OUT:EMITTANCE_NORM',
    u'LHC.BWS.5L4.B2H1:PROF_POSITION_IN',
    u'LHC.BWS.5L4.B2H1:PROF_POSITION_OUT',
    u'LHC.BWS.5L4.B2V2:PROF_POSITION_IN',
    u'LHC.BWS.5L4.B2V2:PROF_POSITION_OUT',
    u'LHC.BWS.5L4.B2H1:PROF_DATA_IN',
    u'LHC.BWS.5L4.B2H1:PROF_DATA_OUT',
    u'LHC.BWS.5L4.B2V2:PROF_DATA_IN',
    u'LHC.BWS.5L4.B2V2:PROF_DATA_OUT',
    u'LHC.BWS.5L4.B2H1:GAIN',u'LHC.BWS.5L4.B2V2:GAIN',
    u'LHC.BOFSU:OFC_ENERGY']
  return timber_variables
def _get_timber_data(beam,t1,t2,db=None):
  """
  retrieve data from timber needed for
  BWS emittance calculation
  
  Parameters:
  ----------
  db    : timber database
  beam  : either 'B1' or 'B2'
  t1,t2 : start and end time of extracted data in unix time
  
  Returns:
  -------
  bsrt_data: structured array with
             time = timestamp
             gate = gate delay
             sig* = beam size
             bet* = beta functions at position of BSRT
             *_time = time stamps for rarely logged 
                      variables, explicitly timber variables
                      %LHC%BSRT%LSF_%, %LHC%BSRT%BETA% and
                      LHC.BOFSU:OFC_ENERGY
  """
  # -- some checks
  if t2 < t1:
    raise ValueError('End time smaller than start time, t2 = ' +
    '%s > %s = t1'%(t2,t1))
  name = '%LHC%BWS%'+beam.upper()
  # check for which wire we have data
  data = db.get(db.search(name+'%NB_GATES%'),t1,t2)
  var_names = []
  for plane in 'HV':
    nm = name+plane.upper()
    wire = ''
    try:
      if len(data[db.search(nm+'1%NB_GATES%')[0]][1]) !=0:
        wire += '1'
    except (KeyError,IndexError): pass
    try:
      if len(data[db.search(nm+'2%NB_GATES%')[0]][1]) !=0:
        wire += '2'
    except (KeyError,IndexError): pass
    if wire =='1' or wire == '2': pass
    elif wire == '':
      raise ValueError("No data found for wire 1 or wire 2 as "+
      "db.search('%s') is empty!"%(name+"%NB_GATES%"))
    elif wire == '12':
      raise ValueError("Both wires appear to be used! This class "+
      " assumes that only one wire is used!" +
      "db.search('%s') = %s!"%(name+"%NB_GATES%",
      db.search(name+'%NB_GATES%')))
    else:
      raise ValueError("This completely failed! wire = %s "%wire +
      "and db.search('%s') = %s!"%(name+"%NB_GATES%",
      db.search(name+'%NB_GATES%')))
    # extract variable names for wires from database
    for var in ['NB_GATES','GAIN','BUNCH_SELECTION','PROF_POSITION_',
               'PROF_DATA_']:
      nm = name+plane.upper()+wire
      var_names.extend(db.search(nm+'%'+var+'%'))
  for var in ['BETA','EMITTANCE_NORM']:
    var_names.extend(db.search(name+'%'+var+'%'))
  var_names.extend(['LHC.BOFSU:OFC_ENERGY'])
  # check that variable names haven't changed
  var_check = _bws_timber_variables() # hardcoded names
  flag_check = True
  for var in var_names:
    if var not in var_check[beam.upper()]:
      print('WARNING: variable name %s changed!'%var)
      flag_check = False
  if flag_check is False:
    print('Hardcoded variable names are: %s'%var_check)
  # get data
  data = db.get(var_names,t1,t2) 
  # check that there is an energy value smaller than t1
  var_egev = 'LHC.BOFSU:OFC_ENERGY'
  degev = data[var_egev]
  t1_new = t1
  # make sure data is not empty
  while (degev[0].size  == 0):
    if (np.abs(t1_new-t1) > 30*24*60*60):                               
      raise ValueError('Last logging time for LHC.BOFSU:OFC_ENERGY' +   
                       ' exceeds 1 month! Check your data!!!')          
      return                                                            
    t1_new = t1_new-24*60*60
    degev = db.get([var_egev],t1_new,t2)[var_egev]
  # then check that first time stamp is smaller than t1
  while (degev[0][0] > t1):
    if (np.abs(t1_new-t1) > 30*24*60*60):
      raise ValueError('Last logging time for LHC.BOFSU:OFC_ENERGY' + 
                       ' exceeds 1 month! Check your data!!!')
      return
    t1_new = t1_new-24*60*60
    degev = db.get([var_egev],t1_new,t2)[var_egev]
  # update data
  data['LHC.BOFSU:OFC_ENERGY'] = degev
  return data
def _timber_to_dict(beam,plane,direction,data,db):
  """
  converts timber data to dictionary of the slot number
  as keys, explicitly:

  Parameters:
  -----------
  beam: 'B1' or 'B2'
  plane: plane to be extracted
  direction: 'IN' or 'OUT'
  data: timber data as extracted with _get_timber_data()
  db: timber database

  Returns:
  --------
  dict: dictionary with structure
    {slot: [time[s], time_app[s], emith[um], emitv[um]]}
  where 
  """
  keys_timber = ['NB_GATES','BUNCH_SELECTION','BETA','EMITTANCE_NORM',
                 'PROF_POSITION','PROF_DATA','GAIN']
  keys_dic    = ['gate','bunch','beta','emit',
                 'pos','amp','gain']
  # dictionary of time,value
  tt,vv ={},{}
  name = '%LHC%BWS%'+beam.upper()+plane.upper() # make sure to have upper letters
  # check which wire is used by checking the gates
  try:
    if db.search(name+'1%NB_GATES%')[0] in data.keys(): wire = '1'
  except IndexError: pass
  try:
    if db.search(name+'2%NB_GATES%')[0] in data.keys(): wire = '2'
  except IndexError: pass
  for kt,kd in zip(keys_timber,keys_dic):
  # db.search() gives correctly back which wire is used. Use it to
  # assign the data to tt,vv etc.
    if kd in ['gate','bunch','gain']:
      var_str = name+wire+'%'+kt+'%'
    elif kd in ['beta','emit']:
      var_str = name+'%'+direction+'%'+kt+'%'
    else:
      var_str = name+wire+'%'+kt+'%'+direction+'%'
    var_name = db.search(var_str) 
    # check that this really only returns one variable name
    if len(var_name) !=1:
      raise ValueError("Only one variable name should be returned "+
        "here!\n db.search('"+var_str+"')=%s"%(var_name))
    tt[kd],vv[kd] = data[var_name[0]] 
    # convert binary format to float values
    if kd == 'bunch':
      vv[kd] = np.array([extract_bunch_selection(vv[kd][i]) 
                  for i in xrange(len(vv[kd]))])
  dbws={}
  for t in tt['pos']:
    pos = vv['pos'][tt['pos'] == t][0] # position                             
    ngate = vv['gate'][tt['gate'] == t]
    gain  = vv['gain'][tt['gain'] == t]
    amp = (vv['amp'][tt['amp'] == t][0]).reshape(int(ngate),len(pos))
    slots = vv['bunch'][tt['bunch'] == t].flatten()
    # beta and eps time stamps are different but have the same ordering
    tbe  = tt['beta'][tt['pos'] ==t]
    beta = vv['beta'][tt['beta'] == tbe]
    emit = vv['emit'][tt['emit'] == tbe].flatten()
#    print 'MF',pos,ngate,gain,amp,slots,tbe,beta,emit
    # trouble with getting the energy
    igev = np.where(t-data['LHC.BOFSU:OFC_ENERGY'][0]>=0.)[0][-1]
    egev = data['LHC.BOFSU:OFC_ENERGY'][1][igev]
    for idx,sl in zip(xrange(ngate),slots):
      if sl not in dbws.keys():
        dbws[sl]=[]
      idx_max = np.argmax(np.abs(amp[idx]))
      # flip in case profile is mirrored on x-axis
      if amp[idx][idx_max]<0:
        amp[idx]=-amp[idx]
      # put smallest value to 0
      amp[idx] = amp[idx]-np.min(amp[idx])
      dx = np.abs(pos[1:]-pos[0:-1])
      int_dist = (dx*amp[idx][:-1]).sum()
      # case where amplitude =0
      if int_dist == 0:
        amp_norm = amp[idx]
        sigma_gauss,sigma_gauss_err,emit_gauss,emit_gauss_err=0,0,0,0
        p = np.zeros(4)
        pcov = np.zeros((4,4))
      else:
        amp_norm = amp[idx]/int_dist
        p,pcov = curve_fit(f=tb.gauss_pdf,xdata=pos,ydata=amp_norm,
                           p0=[0,1,0,1000])
        sigma_gauss = p[3]
        sigma_gauss_err = np.sqrt(pcov[3,3])
        emit_gauss = tb.emitnorm(sigma_gauss**2/beta,egev)*1.e-6
        emit_gauss_err = tb.emitnorm(2*sigma_gauss*sigma_gauss_err/
                                     beta,egev)*1.e-6
      Tracer()()
      dbws[sl].append((t,tbe,gain,egev,pos,amp[idx],amp_norm,beta,emit[idx],
                       emit_gauss,emit_gauss_err,p,pcov))
  for k in dbws.keys():
    dbws[k]=np.array(dbws[k],dtype=[('time',float),
               ('time_app',float),('gain',float),('egev',float),('pos',np.ndarray),
               ('amp',np.ndarray),('amp_norm',np.ndarray),
               ('beta',float),('emit',float),
               ('emit_gauss',float),('emit_gauss_err',float),
               ('p_gauss',np.ndarray),('pcov_gauss',np.ndarray)])
  return dbws


class BWS(object):
  """
  class to analyze BSRT data
  Example:
  --------
  To extract the data from timber:

    t1=pytimber.parsedate("2016-08-24 00:58:00.000")
    t2=pytimber.parsedate("2016-08-24 00:59:00.000")
    bws=pytimber.BWS.fromdb(t1,t2,beam='B1')

  Attributes:
  -----------
  timber_vars : timber variables needed to calculate
                    normalized emittance
  beam             : 'B1' for beam 1 or 'B2' for beam2
  t_start, t_end   : start/end time of extracted data
  emit    : dictionary of normalized emittances
            {slot: [time[s], emith[um], emitv[um]]}
  emitfit : dictionary of fit of normalized emittances
            between times t1 and t2
            {slot: [t1[s], t2[s], emith [um],emitv[um]]}

  Methods:
  --------
  get_timber_data : returns raw data from pytimber
  fromdb : create BWS instance using the given pytimber database
  fit_gauss : make a Gaussian fit of BWS profiles
  get_fit : extract fit data for specific slot and times
  """
  def __init__(self,db=None,timber_vars=None,beam=None,data=None,
               t_start=None,t_end=None):
    self.db = db
    self.timber_vars = timber_vars
    self.beam = beam
    self.data = data
    self.t_start = t_start
    self.t_end = t_end
  @classmethod
  def fromdb(cls,t1,t2,beam='B1',db=None,verbose=False):
    """
    retrieve data using timber and calculate normalized emittances 
    from extracted values.
    Note: all values in self.emitfit are deleted

    Example:
    --------
      To extract the data from timber:

        t1=pytimber.parsedate("2016-08-24 00:58:00.000")
        t2=pytimber.parsedate("2016-08-24 00:59:00.000")
        bws=pytimber.BWS.fromdb(t1,t2,beam='B1')

    Parameters:
    -----------
    db : pytimber or pagestore database
    beam : either 'B1' or 'B2'
    t1,t2 : start and end time of extracted data
            in unix time
    verbose: verbose mode, default verbose = False

    Returns:
    -------
    class: BWS class instance with dictionary of normalized emittances,
           profiles and other relevant parameters stored in self.emit.
           self.emit is sorted after slot number. 'in' and 'out' refer
           to the measurement of the wire moving inwards and outwards
           respectively.
          {slot: [time [s],emith [um],emitv[um],sigh[mm],sigv[mm],
                  lsfh [mm], lsfv[mm], beth[mm], betv[mm],energy[GeV]]}
    """
    if beam not in ['B1','B2']:
      raise ValueError("beam = %s must be either 'B1' or 'B2'"%beam)
    # if no database is given create dummy database to extract data
    if db is None:
      db = pytimber.LoggingDB()
      if verbose:
        print('... no database given, creating default database ' +
        'pytimber.LoggingDB()')
    # get data from timber
    if verbose:
      print('... extracting data from timber')
    timber_data = _get_timber_data(beam=beam,t1=t1,t2=t2,db=db)
    timber_vars = timber_data.keys()
    # generate dictionary
    data = {}
    for plane in 'HV':
      data[plane]={}
      for io in 'IN','OUT':
         data[plane][io] = _timber_to_dict(beam=beam,plane=plane,
                             direction=io,data=timber_data,db=db)
    return cls(db=db,timber_vars=timber_vars,data=data,t_start=t1,
               t_end=t2,beam=beam)
  def get_timber_data(self,t1,t2,db=None):
    """
    return timber data for BWS. See LHCBWS._get_timber_data(...)
    for further documentation.
    """
    return _get_timber_data(beam=self.beam,t1=t1,t2=t2,db=db)
  def update_beta_energy(self,t1=None,t2=None,beth=None,betv=None,
                         energy=None,verbose=False):
    """
    update beta and energy for emit_gauss and emit_gauss_err
    within t1 and t2. emit = emittance as stored in timber is not
    changed.

    Parameters:
    ----------
    t1,t2: start/end time in unix time [s]
    betah,betav: hor./vert. beta function [m]
    energy: beam energy [GeV]
    """
    if t1 is None: t1 = self.t_start
    if t2 is None: t2 = self.t_end
    for plane,beta in zip('HV',[beth,betv]):
      for io in 'IN','OUT':
        for sl in self.data[plane][io].keys():
          data = self.data[plane][io][sl]
          time = data['time']
          mask = np.logical_and(time>=t1,time<=t2)
          if energy is not None:
            energy_old = data['egev'][mask]
            data['egev'][mask] = energy
            # get rel beta,gamma
            b_old,g_old = tb.betarel(energy_old),tb.gammarel(energy_old) 
            b,g         = tb.betarel(energy),tb.gammarel(energy)
            for k in 'emit_gauss','emit_gauss_err':
              data[k][mask] = (data[k][mask]*(b*g)/(b_old*g_old))
          if beta is not None:
            beta_old = data['beta'][mask]
            data['beta'][mask] = beta
            for k in 'emit_gauss','emit_gauss_err':
              data[k][mask] = (data[k][mask]*(beta_old)/(beta))
          self.data[plane][io][sl] = data
