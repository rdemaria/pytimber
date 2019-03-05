import os

try:
    import numpy as np
    import matplotlib.pyplot as pl
    from scipy.optimize import curve_fit
except ImportError:
    print("""No module found: numpy, matplotlib and scipy modules should
    be present to run pytimbertools""")

import pytimber
from .toolbox import emitnorm, exp_fit, movingaverage

from .dataquery import set_xaxis_date
from .localdate import parsedate, dumpdate


def _get_timber_data(beam, t1, t2, db=None):
    """
    retrieve data from timber needed for
    BSRT emittance calculation

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
               lsf* = calibration factors
               bet* = beta functions at position of BSRT
               *_time = time stamps for rarely logged
                        variables, explicitly timber variables
                        %LHC%BSRT%LSF_%, %LHC%BSRT%BETA% and
                        LHC.BOFSU:OFC_ENERGY
    """
    # -- some checks
    if t2 < t1:
        raise ValueError('End time smaller than start time, t2 = ' +
                         '%s > %s = t1' % (t2, t1))
    # --- get data
    # timber variable names are stored in *_var variables
    # bsrt_sig and bsrt_lsf = BSRT data from timber
    # -- data extraction beam sizes + gates:
    #    FIT_SIGMA_H,FIT_SIGMA_V,GATE_DELAY
    # save timber variable names
    [fit_sig_h_var, fit_sig_v_var] = db.search('%LHC%BSRT%' + beam.upper() +
                                               '%FIT_SIGMA_%')
    [gate_delay_var] = db.search('%LHC%BSRT%' + beam.upper() +
                                 '%GATE_DELAY%')
    bsrt_sig_var = [fit_sig_h_var, fit_sig_v_var, gate_delay_var]
    # extract the data from timber
    bsrt_sig = db.get(bsrt_sig_var, t1, t2)
    # check that all timestamps are the same for bsrt_sig_var
    for k in bsrt_sig_var:
        if np.any(bsrt_sig[bsrt_sig_var[0]][0] != bsrt_sig[k][0]):
            error_str = ('Time stamps for %s and %s differ!'
                         % (bsrt_sig_var[0], bsrt_sig_var[k]) +
                         'The data can not be combined')
            raise ValueError(error_str)
            return
    # -- BSRT callibration factors and beam energy:
    #    LSF_H,LSF_V,BETA_H,BETA_V,ENERGY
    [lsf_h_var, lsf_v_var] = db.search('%LHC%BSRT%' + beam.upper() +
                                       '%LSF_%')
    [beta_h_var, beta_v_var] = db.search('%LHC%BSRT%' + beam.upper() +
                                         '%BETA%')
    energy_var = u'LHC.BOFSU:OFC_ENERGY'
    bsrt_lsf_var = [lsf_h_var, lsf_v_var, beta_h_var, beta_v_var,
                    energy_var]
    t1_lsf = t1
    bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
    # only logged rarely, loop until array is not empty, print warning
    # if time window exceeds one month
    # check that time stamp of lsf,beta,energy is before first sigma
    # timestamp
    for var in bsrt_lsf_var:
        while (bsrt_lsf[var][0].size == 0):
            if (np.abs(t1_lsf - t1) > 30 * 24 * 60 * 60):
                error_str = ('Last logging time for ' + ', %s' * 5 +
                             ' exceeds 1 month!' +
                             ' Check your data!!!') % tuple(bsrt_lsf_var)
                raise ValueError(error_str)
                return
            else:
                t1_lsf = t1_lsf - 24 * 60 * 60
                bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
        while (bsrt_lsf[var][0][0] > bsrt_sig[bsrt_sig_var[0]][0][0]):
            if (np.abs(t1_lsf - t1) > 30 * 24 * 60 * 60):
                error_str = ('Last logging time for ' + ', %s' * 5 +
                             ' exceeds 1 month!' +
                             ' Check your data!!!') % tuple(bsrt_lsf_var)
                raise ValueError(error_str)
                return
            else:
                t1_lsf = t1_lsf - 24 * 60 * 60
                bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
    # -- create list containing all the data (bsrt_list), then save
    # data in structured array bsrt_data
    # take timestamp from GATE_DELAY (same as for other variables)
    bsrt_list = []
    var = zip(bsrt_sig[gate_delay_var][0], bsrt_sig[gate_delay_var][1],
              bsrt_sig[fit_sig_h_var][1], bsrt_sig[fit_sig_v_var][1])
    # find closest timestamp with t_lsf<t
    for t, gate, sigh, sigv in var:
        lsf_time = {}
        lsf_value = {}
        for k in bsrt_lsf_var:
            idx = np.where(t - bsrt_lsf[k][0] >= 0.)[0][-1]
            lsf_time[k] = bsrt_lsf[k][0][idx]
            lsf_value[k] = bsrt_lsf[k][1][idx]
        for i in range(len(gate)):
            bsrt_list.append(tuple([t, gate[i], sigh[i], sigv[i]] +
                                   [lsf_time[k] for k in bsrt_lsf_var] +
                                   [lsf_value[k] for k in bsrt_lsf_var]))
    ftype = [('time', float),
             ('gate', float),
             ('sigh', float),
             ('sigv', float),
             ('lsfh_time', float),
             ('lsfv_time', float),
             ('beth_time', float),
             ('betv_time', float),
             ('energy_time', float),
             ('lsfh', float),
             ('lsfv', float),
             ('beth', float),
             ('betv', float),
             ('energy', float)]
    bsrt_data = np.array(bsrt_list, dtype=ftype)
    return bsrt_data


def _timber_to_emit(bsrt_array):
    """
    returns dictionary with emittance etc. as used in BSRT.fromdb

    Parameters:
    -----------
    bsrt_array : data extracted from timber with _get_timber_data

    Returns:
    --------
    emit_dict: dictionary with emittances
              {slot: [time [s],emith [um],emitv[um],sigh[mm],sigv[mm],
              lsfh [mm], lsfv[mm], beth[mm], betv[mm],energy[GeV]]}
    """
    # create dictionary indexed with slot number
    emit_dict = {}

    t_unit_change = parsedate('2018-01-01 00:00:00')

    # loop over slots
    for j in set(bsrt_array['gate']):
        # data for slot j
        bsrt_slot = bsrt_array[bsrt_array['gate'] == j]
        bsrt_emit = []
        # loop over all timestamps for slot j
        for tt in set(bsrt_slot['time']):
            # data for slot j and timestamp tt
            bsrt_aux = bsrt_slot[bsrt_slot['time'] == tt]
            # gives back several values per timestamp -> take the mean value
            # energy [GeV]
            energy_aux = np.mean(bsrt_aux['energy'])
            sigh = bsrt_aux['sigh']
            lsfh = bsrt_aux['lsfh']
            beth = bsrt_aux['beth']
            sigv = bsrt_aux['sigv']
            lsfv = bsrt_aux['lsfv']
            betv = bsrt_aux['betv']
            # geometric emittance
            if tt > t_unit_change:
                # print('lsf/1000')
                # added /1000, Claudia's suggestion probably
                # because emit values in um and lsf in mm
                emith_aux = np.mean((sigh**2 - (lsfh / 1000.0)**2) / beth)
                emitv_aux = np.mean((sigv**2 - (lsfv / 1000.0)**2) / betv)
            else:
                # print('lsf')
                emith_aux = np.mean((sigh**2 - lsfh**2) / beth)
                emitv_aux = np.mean((sigv**2 - lsfv**2) / betv)
            sigh, lsfh, beth = np.mean([sigh, lsfh, beth], axis=1)
            sigv, lsfv, betv = np.mean([sigv, lsfv, betv], axis=1)
            # normalized emittance
            emith = emitnorm(emith_aux, energy_aux)
            emitv = emitnorm(emitv_aux, energy_aux)
            bsrt_emit.append((tt, emith, emitv, sigh, sigv, lsfh, lsfv,
                              beth, betv, energy_aux))
        # sort after the time
        emit_dict[j] = np.sort(np.array(bsrt_emit,
                                        dtype=[('time', float),
                                               ('emith', float),
                                               ('emitv', float),
                                               ('sigh', float),
                                               ('sigv', float),
                                               ('lsfh', float),
                                               ('lsfv', float),
                                               ('beth', float),
                                               ('betv', float),
                                               ('energy', float)]), axis=0)
    return emit_dict


class BSRT(object):
    """
    class to analyze BSRT data
    Example:
    --------
    To extract the data from timber:

      t1=pytimber.parsedate("2016-08-24 00:58:00.000")
      t2=pytimber.parsedate("2016-08-24 00:59:00.000")
      bsrt=pytimber.BSRT.fromdb(t1,t2,beam='B1')

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
    fromdb : create BSRT instance using the given pytimber database
    fit : make fit of BSRT emittance between timestamps t1,t2.
          Values are added to *emitfit*.
    get_fit : extract fit data for specific slot and times
    """
    timber_vars = {}
    timber_vars['B1'] = [u'LHC.BSRT.5R4.B1:FIT_SIGMA_H',
                         u'LHC.BSRT.5R4.B1:FIT_SIGMA_V',
                         u'LHC.BSRT.5R4.B1:GATE_DELAY',
                         u'LHC.BSRT.5R4.B1:LSF_H',
                         u'LHC.BSRT.5R4.B1:LSF_V',
                         u'LHC.BSRT.5R4.B1:BETA_H',
                         u'LHC.BSRT.5R4.B1:BETA_V',
                         'LHC.BOFSU:OFC_ENERGY']
    timber_vars['B2'] = [u'LHC.BSRT.5L4.B2:FIT_SIGMA_H',
                         u'LHC.BSRT.5L4.B2:FIT_SIGMA_V',
                         u'LHC.BSRT.5L4.B2:GATE_DELAY',
                         u'LHC.BSRT.5L4.B2:LSF_H',
                         u'LHC.BSRT.5L4.B2:LSF_V',
                         u'LHC.BSRT.5L4.B2:BETA_H',
                         u'LHC.BSRT.5L4.B2:BETA_V',
                         'LHC.BOFSU:OFC_ENERGY']

    def __init__(self, db=None, beam=None, emit=None, emitfit=None,
                 t_start=None, t_end=None):
        self.db = db
        self.beam = beam
        self.emit = emit
        self.emitfit = emitfit
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
            bsrt=pytimber.BSRT.fromdb(t1,t2,beam='B1')

        Parameters:
        -----------
        db : pytimber or pagestore database
        beam : either 'B1' or 'B2'
        t1,t2 : start and end time of extracted data
               in unix time
        verbose: verbose mode, default verbose = False

        Returns:
        -------
        class: BSRT class instance with dictionary of normalized emittances
               stored in self.emit. self.emit is sorted after slot number
              {slot: [time [s],emith [um],emitv[um],sigh[mm],sigv[mm],
                      lsfh [mm], lsfv[mm], beth[mm], betv[mm],energy[GeV]]}
        """
        if beam not in ['B1', 'B2']:
            raise ValueError("beam = %s must be either 'B1' or 'B2'" % beam)
        # if no database is given create dummy database to extract data
        if db is None:
            db = pytimber.LoggingDB()
            if verbose:
                print('... no database given, creating default database ' +
                      'pytimber.LoggingDB()')
        if verbose:
            print('... extracting data from timber')
        if verbose:
            print('... calculating emittance for non-empty slots')
        # -- get timber data
        bsrt_array = _get_timber_data(beam=beam, t1=t1, t2=t2, db=db)
        # -- calculate emittances, store them in
        #    dictionary self.emit = emit
        emit_dict = _timber_to_emit(bsrt_array)
        return cls(db=db, emit=emit_dict, emitfit=None,
                   t_start=t1, t_end=t2, beam=beam)

    def get_timber_data(self, beam, t1, t2, db=None):
        """
        retrieve data from timber needed for
        BSRT emittance calculation

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
                   lsf* = calibration factors
                   bet* = beta functions at position of BSRT
                   *_time = time stamps for rarely logged
                            variables, explicitly timber variables
                            %LHC%BSRT%LSF_%, %LHC%BSRT%BETA% and
                            LHC.BOFSU:OFC_ENERGY
        """
        return _get_timber_data(beam=beam, t1=t1, t2=t2, db=db)

    def update_beta_lsf_energy(self, t1, t2, beth=None, betv=None,
                               lsfh=None, lsfv=None, energy=None,
                               verbose=False):
        """
        update beta and lsf factor within t1 and t2.

        Parameters:
        ----------
        t1,t2: start/end time in unix time [s]
        betah,betav: hor./vert. beta function [m]
        lsfh, lsfv: hor./vert. lsf factor [mm]
        energy: beam energy [GeV]
        """
        bsrt_array = _get_timber_data(beam=self.beam,
                                      t1=self.t_start, t2=self.t_end,
                                      db=self.db)
        # only change values between t1 and t2
        mask = np.logical_and(
            bsrt_array['time'] >= t1,
            bsrt_array['time'] <= t2)
        for k, v in zip(['beth', 'betv', 'lsfh', 'lsfv', 'energy'], [
                        beth, betv, lsfh, lsfv, energy]):
            if verbose:
                print(k, 'old=', bsrt_array[k][mask], 'new=', v)
            if v is None:
                continue
            bsrt_array[k][mask] = v
        # -- calculate emittances, store them in
        #    dictionary self.emit = emit
        self.emit = _timber_to_emit(bsrt_array)

    def get_fit(self, slot, t1=None, t2=None, verbose=False):
        """
        Function to access fit values for slot *slot* between t1 and t2.

        Parameters:
        ----------
        slot : slot number
        t1 : start time of fit in unix time, if None start of datarange is
             used
        t2 : end time of fit in unix time, if None end of datarange is used
        verbose: verbose mode, default verbose = False

        Returns:
        --------
        fitdata: returns structured array with fitdata for slot *slot* and
                 time interval (t1,t2) with:
                   a*      = amplitude ah,av [um]
                   siga*   = error of fit parameter ah,av [um]
                   tau*    = growth time tauh,tauv [s]
                   sigtau* = error of growth time tauh,tauv [s]
        """
        # -- set times
        t1, t2 = self._set_times(t1, t2, verbose)
        # -- check if values exist
        try:
            # values exist
            return self.emitfit[slot][(t1, t2)]
        except (KeyError, IndexError, TypeError):
            # values don't exist -> try to fit
            self.fit(t1=t1, t2=t2)
            try:
                return self.emitfit[slot][(t1, t2)]
            except IndexError:
                print('ERROR: Fit failed for slot %s ' % slot + ' and time ' +
                      'interval (t1,t2) = (%s,%s)' % (t1, t2))

    def fit(self, t1=None, t2=None, force=False, verbose=False):
        """
        fit the emittance between *t1* and *t2* with an exponential
        function:
          a*exp((t-t1)/tau)
        with a=initial value [um] and tau=growth time [s]
        and store values in self.emitfit. If t1=t2=None use full data
        range. Note that the fit is done with the unaveraged raw data.

        Parameters:
        ----------
        t1 : start time in unix time
        t2 : end time in unix time
        force : if force=True force recalculation of values
        verbose: verbose mode, default verbose = False

        Returns:
        --------
        self: returns class object with updated fit parameters in
              self.emitfit, where self.emitfit has the following structure:
                 self.emitfit = {slot: {(t1,t2): fitdata} }
              with fitdata being a structured array with:
                a*      = amplitude ah,av [um]
                siga*   = error of fit parameter ah,av [um]
                tau*    = growth time tauh,tauv [s]
                sigtau* = error of growth time tauh,tauv [s]
        """
        # -- set times
        t1, t2 = self._set_times(t1, t2, verbose)
        # -- some basic checks
        # check that the data has been extracted
        if self.emit is None:
            raise Exception("""First extract the emittance data using \
BSRT.fromdb(beam,EGeV,t_start,t_end,db) with t_start < t1 < t2 \
< t_end.""")
            return
        # initialize self.emitfit if needed
        if self.emitfit is None:
            if verbose:
                print('... no previous fits found')
            force = True
            # initialize dictionary
            self.emitfit = {}
            for slot in self.emit.keys():
                self.emitfit[slot] = {}
        # -- start fitting
        # loop over all slots
        for slot in self.emit.keys():
            # case 1: fit data available + force = False
            try:
                if ((force is False) and
                    (self.emitfit[slot][(t1, t2)].size > 0)):
                    if verbose:
                        error_str = ('...fit data already exists for slot' +
                                     ' %s' % (slot) +
                                     ' and force = False -> skip fit')
                        print(error_str)
                    continue
            except KeyError:  # just continue and redo the fit
                if verbose:
                    print('... no fit data found for slot %s' % (slot))
                pass
            # case 2: fit data not available or force = True
            try:
                if verbose:
                    print('... extracting emittances for slot %s ' % (slot) +
                          'from %s to %s' % (dumpdate(t1), dumpdate(t2)))
                mask = ((self.emit[slot]['time'] >= t1) &
                        (self.emit[slot]['time'] <= t2))
                data = self.emit[slot][mask]
                # subtract initial time to make fitting easier
                data['time'] = data['time'] - data['time'][0]
                # give a guess for the initial paramters
                # assume eps(t1)=a*exp(t1/tau)
                #        eps(t2)=a*exp(t2/tau)
                fit_data = []
                for plane in ['h', 'v']:
                    t2_fit = data['time'][-1] - data['time'][0]
                    epst2_fit = data['emit%s' % plane][-1]
                    epst1_fit = data['emit%s' % plane][0]
                    if epst2_fit < 0:
                        raise ValueError("""Invalid value of BSRT emittance \
(eps < 0) for time t2=%s'%pytimber.parsedate(data['time'][-1])""")
                        return
                    if epst1_fit < 0:
                        raise ValueError("""Invalid value of BSRT emittance \
(eps < 0) for time t1=%s'%pytimber.parsedate(data['time'][0])""")
                        return
                    # initial values for fit parameters
                    a_init = epst1_fit
                    tau_init = t2_fit / (np.log(epst2_fit) - np.log(epst1_fit))
                    if verbose:
                        print(
                            '... fitting emittance %s for slot %s ' %
                            (plane, slot))
                    popt, pcov = curve_fit(exp_fit, data['time'],
                                           data['emit%s' % plane],
                                           p0=[a_init, tau_init])
                    psig = [np.sqrt(pcov[i, i]) for i in range(len(popt))]
                    fit_data += [popt[0], psig[0], popt[1], psig[1]]
                ftype = [('ah', float), ('sigah', float), ('tauh', float),
                         ('sigtauh', float), ('av', float), ('sigav', float),
                         ('tauv', float), ('sigtauv', float)]
                self.emitfit[slot][(t1, t2)] = np.array([tuple(fit_data)],
                                                        dtype=ftype)
            except IndexError:
                print(('ERROR: no data found for slot %s! ') % (slot) +
                      'Check the data in timber using BSRT.get_timber_data()!')
        return self

    def get_slots(self):
        """
        return list of non-empty slots
        """
        return list(self.emit.keys())

    def _set_slots(self, slots):
        """
        set slot numbers, handles the case of slots = None and only one
        slot.
        """
        if slots is None:
            slots = list(self.emit.keys())
        try:
            len(slots)
        except TypeError:
            slots = [slots]
        return np.sort(slots, axis=None)

    def _set_times(self, t1, t2, verbose):
        """
        set start/end time, handles the case of t1 = None and/or t2 = None.
        For t1,t2 = None choose full data range.
        """
        if t1 is None:
            t1 = self.t_start
            if verbose:
                print('... using start time %s' % (dumpdate(t1)))
        if t2 is None:
            t2 = self.t_end
            if verbose:
                print('... using end time %s' % (dumpdate(t2)))
        # check timestamp
        if t1 < self.t_start:
            raise ValueError('Start time t1 = ' +
                             '%s < %s' % (t1, self.t_start) +
                             ' lies outside of data range!')
        if t2 > self.t_end:
            raise ValueError('End time t2 = ' + '%s > %s' % (t1, self.t_end) +
                             ' lies outside of data range!')
        if t2 < t1:
            raise ValueError('End time smaller than start time, t2 = ' +
                             '%s > %s = t1' % (t2, t1))
        return t1, t2

    def plot(self, plane='h', t1=None, t2=None, slots=None, avg=10, fit=True,
             color=None, label=None, verbose=False):
        """plot BSRT data and fit. The unaveraged raw data is used for the
        fit.

        Parameters:
        -----------
        t1,t2 : time interval, if t1 = t2 = None full time range is used
        slots : slot number or list of slot numbers, e.g. slot = [100,200].
                If slots = None, all slots are plotted
        avg: moving average over *avg* data points, if avg = None, the raw
             data is plotted
        fit: fit curve from exponential fit on raw data (not averaged)
        color,linestyle : set fixed color and linestyle
        label : plot label
        verbose: verbose mode, default verbose = False
        """
        # set slots
        slots = self._set_slots(slots)
        # set time
        t1, t2 = self._set_times(t1, t2, verbose)
        # plot data
        colors = []
        for slot in slots:
            if len(colors) == 0:
                colors = [
                    'lime',
                    'indigo',
                    'cyan',
                    'pink',
                    'orange',
                    'm',
                    'g',
                    'r',
                    'b']
            if color is None:
                c = colors.pop()
            else:
                c = color
            mask = ((self.emit[slot]['time'] >= t1) &
                    (self.emit[slot]['time'] <= t2))
            eps = self.emit[slot][mask]
            # raw data
            if avg is None:
                pl.plot(eps['time'], eps['emit%s' %
                                         plane], '.', color=c, label=label)
            # averaged data
            else:
                epsavg = {}  # use a dictionary instead of a structured array
                for k in eps.dtype.fields:
                    epsavg[k] = movingaverage(eps[k], avg)
                pl.plot(epsavg['time'], epsavg['emit%s' % plane], '.',
                        color=c, label=label)
        # plot fit with a black dashed line
        if fit:
            self.plot_fit(plane=plane, t1=t1, t2=t2, slots=slots,
                          linestyle='--', color='k', verbose=verbose)
        else:
            set_xaxis_date()
        pl.ylabel(r'$\epsilon_{N,%s} \ [\mu\mathrm{ m}]$' % plane.upper())
        pl.grid(b=True)
        if label is not None:
            pl.legend(loc='best', fontsize=12)
        return self

    def plot_fit(self, plane='h', t1=None, t2=None, slots=None, color=None,
                 linestyle=None, label=None, verbose=False):
        """
        plot only fit of BSRT data. The raw data is not displayed.

        Parameters:
        -----------
        t1,t2 : time interval, if t1 = t2 = None full time range is used
        slots : slot number or list of slot numbers, e.g. slot = [100,200].
                If None, all slots are plotted
        color,linestyle : set fixed color and linestyle
        label : plot label
        verbose: verbose mode, default verbose = False
        """
        # set slots
        slots = self._set_slots(slots)
        # set time
        t1, t2 = self._set_times(t1, t2, verbose)
        colors = []
        for slot in slots:
            if len(colors) == 0:
                colors = [
                    'lime',
                    'indigo',
                    'cyan',
                    'pink',
                    'orange',
                    'm',
                    'g',
                    'r',
                    'b']
            if color is None:
                c = colors.pop()
            else:
                c = color
            if linestyle is None:
                ls = '-'
            else:
                ls = linestyle
            mask = ((self.emit[slot]['time'] >= t1) &
                    (self.emit[slot]['time'] <= t2))
            ts = self.emit[slot][mask]['time']
            fitparam = self.get_fit(slot=slot, t1=t1, t2=t2)
            pl.plot(ts,
                    exp_fit(ts - ts[0], fitparam['a%s' % plane],
                            fitparam['tau%s' % plane]),
                    linestyle=ls,
                    color=c,
                    label=label)
        set_xaxis_date()
        pl.ylabel(r'$\epsilon_{N,%s} \ [\mu m]$' % plane)
        pl.grid(b=True)
        return self
