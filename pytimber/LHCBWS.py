try:
    import pandas as pd
    import numpy as np
    from scipy.optimize import curve_fit
except ImportError:
    print("No module found: pandas, numpy, matplotlib and scipy"
          "modules should be present to run pytimbertools")

import pytimber

from . import toolbox as tb

# from .dataquery import set_xaxis_date
# from .localdate import parsedate, dumpdate


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
    bunchSelection = []
    main_counter = 0
    for bsb in bunch_selection_binary:
        if bsb != 0:
            counter = 0
            nbr = bin(int(float(bsb)) & 0xffffffff)
            for bit in nbr[2:][::-1]:
                if bit == '1':
                    bunchSelection.append(main_counter + counter)
                counter += 1
        main_counter += 32
    return bunchSelection


def _get_timber_variables(beam, wire, io='all', plane='all'):
    """
    variable names for a given beam, wire and direction in/out

    Parameter:
    ----------
    beam: either 'B1' or 'B2'
    wire: either '1' or '2'
    io: either 'all', 'IN', 'OUT'
    plane: either 'all', 'H', 'V'
    """
    beam = beam.upper()
    assert(beam in ['B1', 'B2']), ("beam = {} "
                                   "must be either 'B1' or 'B2'").format(beam)
    if beam == 'B1':
        rl = 'R'
    elif beam == 'B2':
        rl = 'L'
    assert(wire in ['1', '2']), "wire = {} must be either 1 or 2".format(wire)
    assert(io in ['all', 'IN', 'OUT']), ("io = {} must be either "
                                         "'all', 'IN' or 'OUT'".format(wire))
    assert(plane in ['all', 'H', 'V']), ("plane = {} must be either "
                                         "'all', 'H' or 'V'".format(plane))

    var_template = [u'LHC.BWS.5{rl}4.{b}H{w}:NB_GATES',
                    u'LHC.BWS.5{rl}4.{b}V{w}:NB_GATES',
                    u'LHC.BWS.5{rl}4.{b}H{w}:BUNCH_SELECTION',
                    u'LHC.BWS.5{rl}4.{b}V{w}:BUNCH_SELECTION',
                    u'LHC.BWS.5{rl}4.{b}H.APP.IN:BETA',
                    u'LHC.BWS.5{rl}4.{b}V.APP.IN:BETA',
                    u'LHC.BWS.5{rl}4.{b}H.APP.OUT:BETA',
                    u'LHC.BWS.5{rl}4.{b}V.APP.OUT:BETA',
                    u'LHC.BWS.5{rl}4.{b}H.APP.IN:EMITTANCE_NORM',
                    u'LHC.BWS.5{rl}4.{b}V.APP.IN:EMITTANCE_NORM',
                    u'LHC.BWS.5{rl}4.{b}H.APP.OUT:EMITTANCE_NORM',
                    u'LHC.BWS.5{rl}4.{b}V.APP.OUT:EMITTANCE_NORM',
                    u'LHC.BWS.5{rl}4.{b}H{w}:PROF_POSITION_IN',
                    u'LHC.BWS.5{rl}4.{b}V{w}:PROF_POSITION_IN',
                    u'LHC.BWS.5{rl}4.{b}H{w}:PROF_POSITION_OUT',
                    u'LHC.BWS.5{rl}4.{b}V{w}:PROF_POSITION_OUT',
                    u'LHC.BWS.5{rl}4.{b}H{w}:PROF_DATA_IN',
                    u'LHC.BWS.5{rl}4.{b}V{w}:PROF_DATA_IN',
                    u'LHC.BWS.5{rl}4.{b}H{w}:PROF_DATA_OUT',
                    u'LHC.BWS.5{rl}4.{b}V{w}:PROF_DATA_OUT',
                    u'LHC.BWS.5{rl}4.{b}H{w}:GAIN',
                    u'LHC.BWS.5{rl}4.{b}V{w}:GAIN',
                    u'LHC.BOFSU:OFC_ENERGY']

    variables = [v.format(rl=rl.upper(),
                          b=beam.upper(),
                          w=wire) for v in var_template]
    if io != 'all' and io in ['IN', 'OUT']:
        not_io = list(set(['IN', 'OUT']) - set([io]))[0]
        variables = [v for v in variables if ('.' + not_io not in v and
                                              '_' + not_io not in v)]
    if plane != 'all' and plane in ['H', 'V']:
        not_plane = list(set(['H', 'V']) - set([plane]))[0]
        not_str = '{b}{p}'.format(b=beam, p=not_plane)
        variables = [v for v in variables if not_str not in v]
    return variables


def _get_timber_data(beam, t1, t2, convert_gate=False, db=None):
    """
    retrieve data from timber needed for
    BWS emittance calculation

    Parameters:
    ----------
    db    : timber database
    beam  : either 'B1' or 'B2'
    t1,t2 : start and end time of extracted data in unix time
    convert_gate: if True, converts the binary GATE to slots

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
    if db is None:
        db = pytimber.LoggingDB()
    # -- some checks
    if t2 < t1:
        raise ValueError('End time smaller than start time, t2 = ' +
                         '%s > %s = t1' % (t2, t1))
    name = '%LHC%BWS%' + beam.upper()
    # check for which wire we have data
    data = db.get(db.search(name + '%NB_GATES%'), t1, t2)
    var_names = []
    for plane in 'HV':
        nm = name + plane.upper()
        wire = ''
        try:
            if len(data[db.search(nm + '1%NB_GATES%')[0]][1]) != 0:
                wire += '1'
        except (KeyError, IndexError):
            pass
        try:
            if len(data[db.search(nm + '2%NB_GATES%')[0]][1]) != 0:
                wire += '2'
        except (KeyError, IndexError):
            pass
        if wire == '1' or wire == '2':
            pass
        elif wire == '':
            err_str = ("No data found for wire 1 or wire 2 as "
                       "db.search('{}') is empty!")
            err_str = err_str.format(name + "%NB_GATES%")
            raise ValueError(err_str)
        elif wire == '12':
            err_str = ("Both wires appear to be used! This class assumes that "
                       "only one wire is used! db.search('{}') = {}!")
            err_str = err_str.format(name + "%NB_GATES%",
                                     db.search(name + '%NB_GATES%'))
            raise ValueError(err_str)
        else:
            err_str = ("This completely failed! wire = {} and "
                       "db.search('{}') = {}!")
            err_str = err_str.format(wire,
                                     name + "%NB_GATES%",
                                     db.search(name + '%NB_GATES%'))
            raise ValueError(err_str)
    var_names = _get_timber_variables(beam, wire)
    data = db.get(var_names, t1, t2)
    # check that there is an energy value smaller than t1
    var_egev = 'LHC.BOFSU:OFC_ENERGY'
    degev = data[var_egev]
    t1_new = t1
    # make sure data is not empty
    while (degev[0].size == 0):
        if (np.abs(t1_new - t1) > 30 * 24 * 60 * 60):
            raise ValueError('Last logging time for LHC.BOFSU:OFC_ENERGY '
                             'exceeds 1 month! Check your data!!!')
            return
        t1_new = t1_new - 24 * 60 * 60
        degev = db.get([var_egev], t1_new, t2)[var_egev]
    # then check that first time stamp is smaller than t1
    while (degev[0][0] > t1):
        if (np.abs(t1_new - t1) > 30 * 24 * 60 * 60):
            raise ValueError('Last logging time for LHC.BOFSU:OFC_ENERGY '
                             'exceeds 1 month! Check your data!!!')
            return
        t1_new = t1_new - 24 * 60 * 60
        degev = db.get([var_egev], t1_new, t2)[var_egev]
    # update data
    data['LHC.BOFSU:OFC_ENERGY'] = degev
    if convert_gate:
        if beam == 'B1':
            rl = 'R'
        elif beam == 'B2':
            rl = 'L'
        bunch_vars = [u'LHC.BWS.5{rl}4.{b}H{w}:BUNCH_SELECTION',
                      u'LHC.BWS.5{rl}4.{b}V{w}:BUNCH_SELECTION']
        bunch_vars = [k.format(rl=rl, b=beam, w=wire) for k in bunch_vars]
        for b_v in bunch_vars:
            data[b_v] = list(data[b_v])
            val = data[b_v][1]
            # run the binary to bunch conversion
            data[b_v][1] = np.array([extract_bunch_selection(vv) for
                                    vv in val])
            data[b_v] = tuple(data[b_v])
    return data


def _timber_to_dict(beam, plane, direction, data, db):
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
    [dict: dictionary with structure
      {time: [slot, pos, amp, amp_norm, p_gauss, pcov_gauss]},

    mulitIndex DataFrame contaning the 1D data,
    the indexing of the DataFrame is:
               gain, egev, beta, emit, emit_gauss, emit_gauss_err
    time slot
      1   0
          1
      2   0
          1
    ]
    """
    keys_dic = ['gate', 'bunch', 'beta', 'emit',
                'pos', 'amp', 'gain']
    # dictionary of time,value
    tt, vv = {}, {}
    # make sure to have upper letters
    name = '%LHC%BWS%' + beam.upper() + plane.upper()
    # check which wire is used by checking the gates
    try:
        if db.search(name + '1%NB_GATES%')[0] in data.keys():
            wire = '1'
    except IndexError:
        pass
    try:
        if db.search(name + '2%NB_GATES%')[0] in data.keys():
            wire = '2'
    except IndexError:
        pass
    var_names = _get_timber_variables(beam, wire, io=direction, plane=plane)
    for kt, kd in zip(var_names, keys_dic):
        tt[kd] = data[kt][0]
        vv[kd] = data[kt][1]
    df_ws = []
    dbws_nd = {}
    for i, t in enumerate(tt['pos']):
        pos = vv['pos'][i]  # position
        ngate = vv['gate'][i]
        gain = vv['gain'][i]
        amp = vv['amp'][i].reshape(int(ngate), len(pos))
        slots = vv['bunch'][i]
        # beta and eps time stamps are different but have the same ordering
        # all of the timestamps of the %APP% variables have the same timings
        tbe = tt['beta'][i]
        beta = vv['beta'][i]
        emit = vv['emit'][i]

#    print 'MF',pos,ngate,gain,amp,slots,tbe,beta,emit
        # trouble with getting the energy
        igev = np.where(t - data['LHC.BOFSU:OFC_ENERGY'][0] >= 0.)[0][-1]
        egev = data['LHC.BOFSU:OFC_ENERGY'][1][igev]
        if t not in dbws_nd.keys():
            dbws_nd[t] = []
        for idx, sl in zip(np.arange(ngate), slots):
            idx = int(idx)
            idx_max = np.argmax(np.abs(amp[idx]))
            # flip in case profile is mirrored on x-axis
            if amp[idx][idx_max] < 0:
                amp[idx] = -amp[idx]
            # put smallest value to 0
            amp[idx] = amp[idx] - np.min(amp[idx])
            dx = np.abs(pos[1:] - pos[0:-1])
            int_dist = (dx * amp[idx][:-1]).sum()
            # case where amplitude = 0
            if int_dist == 0:
                amp_norm = amp[idx]
                sigma_gauss = 0
                sigma_gauss_err = 0
                emit_gauss = 0
                emit_gauss_err = 0
                p = np.zeros(4)
                pcov = np.zeros((4, 4))
            else:
                amp_norm = amp[idx] / int_dist
                p, pcov = curve_fit(f=tb.gauss_pdf,
                                    xdata=pos,
                                    ydata=amp_norm,
                                    p0=[0, 1, 0, 1000])
                sigma_gauss = p[3]
                sigma_gauss_err = np.sqrt(pcov[3, 3])
                emit_gauss = tb.emitnorm(sigma_gauss**2 / beta, egev) * 1.e-6
                emit_gauss_err = tb.emitnorm(2 * sigma_gauss *
                                    sigma_gauss_err / beta, egev) * 1.e-6
            row_nd = (sl, pos, amp[idx], amp_norm, p, pcov)
            row_1d = (t, sl, tbe, gain, egev,
                      beta, emit[idx],
                      emit_gauss,
                      emit_gauss_err)
            df_ws.append(row_1d)
            dbws_nd[t].append(row_nd)

    cols_1d = ['time', 'slots', 'time_app', 'gain', 'egev', 'beta', 'emit',
               'emit_gauss', 'emit_gauss_err']
    bws_1d = pd.DataFrame(data=df_ws, columns=cols_1d).set_index(['time',
                                                                 'slots'])
    # the goal here is to output a nice pd.DataFrame of the 1D data
    # and a horrible dictionnary --> array for the nD data
    for k in dbws_nd.keys():
        dbws_nd[k] = np.array(dbws_nd[k], dtype=[('slot', float),
                                           ('pos', np.ndarray),
                                           ('amp', np.ndarray),
                                           ('amp_norm', np.ndarray),
                                           ('p_gauss', np.ndarray),
                                           ('pcov_gauss', np.ndarray)])
    return dbws_nd, bws_1d


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
    """

    def __init__(self, db=None, timber_vars=None, beam=None, data=None,
                 t_start=None, t_end=None):
        self.db = db
        self.timber_vars = timber_vars
        self.beam = beam
        self.data = data
        self.t_start = t_start
        self.t_end = t_end

    @classmethod
    def fromdb(cls, t1, t2, beam='B1', db=None, verbose=False):
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
              [{time: [slot, pos, amp, amp_norm, p_gauss, pcov_gauss]},
               mulitIndex DataFrame contaning the 1D data,
               the indexing of the dataframe should be:
                          gain, egev, beta, emit, emit_gauss, emit_gauss_err
               time slot
                 1   0
                     1
                 2   0
                     1
        ]
        """
        if beam not in ['B1', 'B2']:
            raise ValueError("beam = %s must be either 'B1' or 'B2'" % beam)
        # if no database is given create dummy database to extract data
        if db is None:
            db = pytimber.LoggingDB()
            if verbose:
                print('... no database given, creating default database '
                      'pytimber.LoggingDB()')
        # get data from timber
        if verbose:
            print('... extracting data from timber')
        timber_data = _get_timber_data(beam=beam, t1=t1, t2=t2,
                                       convert_gate=True, db=db)
        timber_vars = timber_data.keys()
        # generate dictionary
        if verbose:
            print('... generating dictionary')
        data_1d = {}
        data_nd = {}
        for plane in 'HV':
            data_1d[plane] = {}
            data_nd[plane] = {}
            for io in 'IN', 'OUT':
                data = _timber_to_dict(beam=beam,
                                       plane=plane,
                                       direction=io,
                                       data=timber_data,
                                       db=db)
                data_nd[plane][io] = data[0]
                data_1d[plane][io] = data[1]

        return cls(db=db, timber_vars=timber_vars, data=[data_1d, data_nd],
                   t_start=t1, t_end=t2, beam=beam)

    def get_timber_data(self, t1, t2, convert_gate=False):
        """
        return timber data for BWS. See LHCBWS._get_timber_data(...)
        for further documentation.
        """
        return _get_timber_data(beam=self.beam, t1=t1, t2=t2, db=self.db,
                                convert_gate=False)

    def update_beta_energy(self, t1=None, t2=None, beth=None, betv=None,
                           energy=None, verbose=False):
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
        if t1 is None:
            t1 = self.t_start
        if t2 is None:
            t2 = self.t_end

        def energy_func(x):
            energy_old = x['egev']
            b_old = tb.betarel(energy_old)
            g_old = tb.gammarel(energy_old)
            b = tb.betarel(energy)
            g = tb.gammarel(energy)
            emit_gauss = x['emit_gauss'] * (b * g) / (b_old * g_old)
            emit_gauss_err = x['emit_gauss_err'] * (b * g) / (b_old * g_old)
            return pd.Series([emit_gauss, emit_gauss_err])

        def beta_func(x):
            beta_old = x['beta']
            emit_gauss = x['emit_gauss'] * (beta_old) / (beta)
            emit_gauss_err = x['emit_gauss_err'] * (beta_old) / (beta)
            return pd.Series([emit_gauss, emit_gauss_err])

        for plane, beta in zip('HV', [beth, betv]):
            for io in 'IN', 'OUT':
                data = self.data[0][plane][io].reset_index()
                data_filt = data.loc[np.logical_and(data['time'] >= t1,
                                                data['time'] <= t2)].copy()
                if energy is not None:
                    data_filt[['emit_gauss',
                         'emit_gauss_err']] = data_filt.apply(energy_func,
                                                              axis=1)
                    data_filt['egev'] = energy
                if beta is not None:
                    data_filt[['emit_gauss',
                               'emit_gauss_err']] = data_filt.apply(beta_func,
                                                                    axis=1)
                    data_filt['beta'] = beta
                data.loc[np.logical_and(data['time'] >= t1,
                                        data['time'] <= t2)] = data_filt
                self.data[0][plane][io] = data.set_index(['time', 'slots'])
