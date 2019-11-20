from . import pytimber

try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as pl
    from scipy.optimize import curve_fit
except ImportError:
    print(
        (
            "No module found: pandas, numpy, matplotlib and scipy modules "
            "should be present to run pytimbertools"
        )
    )

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
    bsrt_data: DataFrame of [time, gate, sigh, sigv, lsfh_time,
        lsfv_time, beth_time, betv_time, energy_time,
        lsfh, lsfv, beth, betv, energy]
    """
    # -- some checks
    if t2 < t1:
        raise ValueError(
            "End time smaller than start time, t2 = " + "%s > %s = t1" % (t2, t1)
        )

    if beam.upper() == "B1":
        fit_sig_h_var = "LHC.BSRT.5R4.B1:FIT_SIGMA_H"
        fit_sig_v_var = "LHC.BSRT.5R4.B1:FIT_SIGMA_V"
        gate_delay_var = "LHC.BSRT.5R4.B1:GATE_DELAY"
        lsf_h_var = "LHC.BSRT.5R4.B1:LSF_H"
        lsf_v_var = "LHC.BSRT.5R4.B1:LSF_V"
        beta_h_var = "LHC.BSRT.5R4.B1:BETA_H"
        beta_v_var = "LHC.BSRT.5R4.B1:BETA_V"
    elif beam.upper() == "B2":
        fit_sig_h_var = "LHC.BSRT.5L4.B2:FIT_SIGMA_H"
        fit_sig_v_var = "LHC.BSRT.5L4.B2:FIT_SIGMA_V"
        gate_delay_var = "LHC.BSRT.5L4.B2:GATE_DELAY"
        lsf_h_var = "LHC.BSRT.5L4.B2:LSF_H"
        lsf_v_var = "LHC.BSRT.5L4.B2:LSF_V"
        beta_h_var = "LHC.BSRT.5L4.B2:BETA_H"
        beta_v_var = "LHC.BSRT.5L4.B2:BETA_V"
    else:
        raise ValueError("beam = {} must be either 'B1' or 'B2'")
    energy_var = u"LHC.BOFSU:OFC_ENERGY"

    bsrt_sig_var = [fit_sig_h_var, fit_sig_v_var, gate_delay_var]
    # extract the data from timber
    bsrt_sig = db.get(bsrt_sig_var, t1, t2)
    # check that all timestamps are the same for bsrt_sig_var
    for k in bsrt_sig_var:
        if np.any(bsrt_sig[bsrt_sig_var[0]][0] != bsrt_sig[k][0]):
            error_str = (
                "Time stamps for %s and %s differ!" % (bsrt_sig_var[0], bsrt_sig_var[k])
                + "The data can not be combined"
            )
            raise ValueError(error_str)
            return
    bsrt_lsf_var = [lsf_h_var, lsf_v_var, beta_h_var, beta_v_var, energy_var]
    t1_lsf = t1
    bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
    # only logged rarely, loop until array is not empty, print warning
    # if time window exceeds one month
    # check that time stamp of lsf,beta,energy is before first sigma
    # timestamp
    for var in bsrt_lsf_var:
        while bsrt_lsf[var][0].size == 0:
            if np.abs(t1_lsf - t1) > 30 * 24 * 60 * 60:
                error_str = (
                    "Last logging time for "
                    + ", %s" * 5
                    + " exceeds 1 month!"
                    + " Check your data!!!"
                ) % tuple(bsrt_lsf_var)
                raise ValueError(error_str)
                return
            else:
                t1_lsf = t1_lsf - 24 * 60 * 60
                bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
        while bsrt_lsf[var][0][0] > bsrt_sig[bsrt_sig_var[0]][0][0]:
            if np.abs(t1_lsf - t1) > 30 * 24 * 60 * 60:
                error_str = (
                    "Last logging time for "
                    + ", %s" * 5
                    + " exceeds 1 month!"
                    + " Check your data!!!"
                ) % tuple(bsrt_lsf_var)
                raise ValueError(error_str)
                return
            else:
                t1_lsf = t1_lsf - 24 * 60 * 60
                bsrt_lsf = db.get(bsrt_lsf_var, t1_lsf, t2)
    # -- create list containing all the data (bsrt_list), then save
    # data in DataFrame bsrt_data
    # take timestamp from GATE_DELAY (same as for other variables)
    bsrt_list = []
    var = zip(
        bsrt_sig[gate_delay_var][0],
        bsrt_sig[gate_delay_var][1],
        bsrt_sig[fit_sig_h_var][1],
        bsrt_sig[fit_sig_v_var][1],
    )
    # find closest timestamp with t_lsf<t
    for t, gate, sigh, sigv in var:
        lsf_time = {}
        lsf_value = {}
        for k in bsrt_lsf_var:
            idx = np.where(t - bsrt_lsf[k][0] >= 0.0)[0][-1]
            lsf_time[k] = bsrt_lsf[k][0][idx]
            lsf_value[k] = bsrt_lsf[k][1][idx]
        for i in range(len(gate)):
            bsrt_list.append(
                tuple(
                    [t, gate[i], sigh[i], sigv[i]]
                    + [lsf_time[k] for k in bsrt_lsf_var]
                    + [lsf_value[k] for k in bsrt_lsf_var]
                )
            )
    cols = [
        "time",
        "slots",
        "sigh",
        "sigv",
        "lsfh_time",
        "lsfv_time",
        "beth_time",
        "betv_time",
        "energy_time",
        "lsfh",
        "lsfv",
        "beth",
        "betv",
        "energy",
    ]
    # time could be converted to pd.Datetime
    bsrt_data = pd.DataFrame(data=bsrt_list, columns=cols)
    return bsrt_data


def _timber_to_emit(bsrt_array):
    """
    returns DataFrame with emittance etc. as used in BSRT.fromdb

    Parameters:
    -----------
    bsrt_array : data extracted from timber with _get_timber_data
    and structured array format

    Returns:
    --------
    bsrt_array: MultiIndex DataFrame of:
                sigh sigv lsfh lsfv beth betv emith emitv energy
    slots time
    """

    t_unit_change = parsedate("2018-01-01 00:00:00")
    mask = bsrt_array["time"] < t_unit_change
    bsrt_prior = bsrt_array[mask]
    bsrt_post = bsrt_array[~mask]

    unit_rescale = 1
    bsrt_prior["emith"] = (
        bsrt_prior["sigh"] ** 2 - (bsrt_prior["lsfh"] / unit_rescale) ** 2
    ) / bsrt_prior["beth"]
    bsrt_prior["emitv"] = (
        bsrt_prior["sigv"] ** 2 - (bsrt_prior["lsfv"] / unit_rescale) ** 2
    ) / bsrt_prior["betv"]
    unit_rescale = 1000
    bsrt_post["emith"] = (
        bsrt_post["sigh"] ** 2 - (bsrt_post["lsfh"] / unit_rescale) ** 2
    ) / bsrt_post["beth"]
    bsrt_post["emitv"] = (
        bsrt_post["sigv"] ** 2 - (bsrt_post["lsfv"] / unit_rescale) ** 2
    ) / bsrt_post["betv"]
    bsrt_array = pd.concat([bsrt_prior, bsrt_post], axis=0)
    keep_cols = [
        "sigh",
        "sigv",
        "lsfh",
        "lsfv",
        "beth",
        "betv",
        "emith",
        "emitv",
        "energy",
    ]
    bsrt_array = bsrt_array.groupby(["slots", "time"])[keep_cols].mean()

    def func(x):
        return emitnorm(x[0], x[1])

    bsrt_array["emith"] = bsrt_array[["emith", "energy"]].apply(func, axis=1)
    bsrt_array["emitv"] = bsrt_array[["emitv", "energy"]].apply(func, axis=1)
    return bsrt_array


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
    beam : 'B1' for beam 1 or 'B2' for beam2
    t_start, t_end : start/end time of extracted data
    emit : MultiIndex DataFrame of:
                sigh sigv lsfh lsfv beth betv emith emitv energy
    slots time
    emit_fit : MultiIndex DataFrame of:
                ah sigah tauh sigtauh av sigav tauv sigtauv
    slots t1 t2

    Methods:
    --------
    get_timber_data : returns raw data from pytimber
    fromdb : create BSRT instance using the given pytimber database
    fit : make fit of BSRT emittance between timestamps t1,t2.
          Values are added to *emit_fit*.
    get_fit : extract fit data for specific slot and times
    """

    timber_vars = {}
    timber_vars["B1"] = [
        u"LHC.BSRT.5R4.B1:FIT_SIGMA_H",
        u"LHC.BSRT.5R4.B1:FIT_SIGMA_V",
        u"LHC.BSRT.5R4.B1:GATE_DELAY",
        u"LHC.BSRT.5R4.B1:LSF_H",
        u"LHC.BSRT.5R4.B1:LSF_V",
        u"LHC.BSRT.5R4.B1:BETA_H",
        u"LHC.BSRT.5R4.B1:BETA_V",
        "LHC.BOFSU:OFC_ENERGY",
    ]
    timber_vars["B2"] = [
        u"LHC.BSRT.5L4.B2:FIT_SIGMA_H",
        u"LHC.BSRT.5L4.B2:FIT_SIGMA_V",
        u"LHC.BSRT.5L4.B2:GATE_DELAY",
        u"LHC.BSRT.5L4.B2:LSF_H",
        u"LHC.BSRT.5L4.B2:LSF_V",
        u"LHC.BSRT.5L4.B2:BETA_H",
        u"LHC.BSRT.5L4.B2:BETA_V",
        "LHC.BOFSU:OFC_ENERGY",
    ]

    def __init__(
        self, db=None, beam=None, emit=None, emit_fit=None, t_start=None, t_end=None
    ):
        self.db = db
        self.beam = beam
        self.emit = emit
        self.emit_fit = emit_fit
        self.t_start = t_start
        self.t_end = t_end

    @classmethod
    def fromdb(cls, t1, t2, beam="B1", db=None, verbose=False):
        """
        retrieve data using timber and calculate normalized emittances
        from extracted values.
        Note: all values in self.emit_fit are deleted

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
        class: BSRT class instance with DataFrame of normalized emittances
               stored in self.emit as a MultiIndex DataFrame:
                   sigh sigv lsfh lsfv beth betv emith emitv energy
        slots time
        """
        if beam not in ["B1", "B2"]:
            raise ValueError("beam={} must be 'B1' or 'B2'".format(beam))
        # if no database is given create dummy database to extract data
        if db is None:
            db = pytimber.LoggingDB()
            if verbose:
                print(
                    "... no database given, creating default database "
                    + "pytimber.LoggingDB()"
                )
        if verbose:
            print("... extracting data from timber")
        # -- get timber data
        bsrt_array = _get_timber_data(beam=beam, t1=t1, t2=t2, db=db)
        # -- calculate emittances, store them in
        #    dictionary self.emit = emit
        if verbose:
            print("... calculating emittance for non-empty slots")
        emit = _timber_to_emit(bsrt_array)
        return cls(db=db, emit=emit, emit_fit=None, t_start=t1, t_end=t2, beam=beam)

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
        bsrt_data: MultiIndex DataFrame
                    sigh sigv lsfh lsfv beth betv emith emitv energy
        slots time

        """
        return _get_timber_data(beam=beam, t1=t1, t2=t2, db=db)

    def update_beta_lsf_energy(
        self,
        t1,
        t2,
        beth=None,
        betv=None,
        lsfh=None,
        lsfv=None,
        energy=None,
        verbose=False,
    ):
        """
        update beta and lsf factor within t1 and t2.

        Parameters:
        ----------
        t1,t2: start/end time in unix time [s]
        betah,betav: hor./vert. beta function [m]
        lsfh, lsfv: hor./vert. lsf factor [mm]
        energy: beam energy [GeV]
        """
        bsrt_array = _get_timber_data(
            beam=self.beam, t1=self.t_start, t2=self.t_end, db=self.db
        )
        # only change values between t1 and t2
        mask = np.logical_and(bsrt_array["time"] >= t1, bsrt_array["time"] <= t2)
        for k, v in zip(
            ["beth", "betv", "lsfh", "lsfv", "energy"], [beth, betv, lsfh, lsfv, energy]
        ):
            if verbose:
                print(k, "old=", bsrt_array[k][mask], "new=", v)
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
        fitdata: the relevant row of self.emit_fit for the requested (slot, t1,
            t2)
        """
        # -- set times
        t1, t2 = self._set_times(t1, t2, verbose)
        # -- check if values exist
        try:
            # values exist
            return self.emit_fit.loc[(slot, t1, t2)]
        except AttributeError:
            # values don't exist -> try to fit
            self.fit(t1=t1, t2=t2)
            try:
                return self.emit_fit.loc[(slot, t1, t2)]
            except IndexError:
                print(
                    "ERROR: Fit failed for slot %s " % slot
                    + " and time "
                    + "interval (t1,t2) = (%s,%s)" % (t1, t2)
                )

    def fit(self, t1=None, t2=None, force=False, verbose=False):
        """
        fit the emittance between *t1* and *t2* with an exponential
        function:
          a*exp((t-t1)/tau)
        with a=initial value [um] and tau=growth time [s]
        and store values in self.emit_fit. If t1=t2=None use full data
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
              self.emit_fit, where self.emit_fit is a MultiIndex DataFrame
                        ah sigah tauh sigtauh av sigav tauv sigtauv
            slots t1 t2

        """
        # -- set times
        t1, t2 = self._set_times(t1, t2, verbose)
        # -- some basic checks
        # check that the data has been extracted
        if self.emit is None:
            raise Exception(
                """First extract the emittance data using \
BSRT.fromdb(beam,EGeV,t_start,t_end,db) with t_start < t1 < t2 \
< t_end."""
            )

        cols = [
            "t1",
            "t2",
            "ah",
            "sigah",
            "tauh",
            "sigtauh",
            "av",
            "sigav",
            "tauv",
            "sigtauv",
        ]

        def fit_slot(group):
            slot = group.index.get_level_values(0)[0]
            # don't fit if already done earlier
            if (
                self.emit_fit is not None
                and force is False
                and slot in self.emit_fit.index.get_level_values(0)
            ):
                if t1 in self.emit_fit.index.get_level_values(1):
                    if t2 in self.emit_fit.index.get_level_values(2):
                        return

            time = group.index.get_level_values(1)
            mask = np.logical_and(time >= t1, time <= t2)

            group = group.loc[mask, :]
            time = time[mask]

            time = time - time[0]
            # give a guess for the initial paramters
            # assume eps(t1)=a*exp(t1/tau)
            #        eps(t2)=a*exp(t2/tau)
            fit_data = []
            for plane in ["h", "v"]:
                emit_key = "emit{}".format(plane)
                t2_fit = time[-1] - time[0]
                epst2_fit = group[emit_key].iloc[-1]
                epst1_fit = group[emit_key].iloc[0]
                if epst2_fit < 0:
                    err_str = (
                        "Invalid value of BSRT emittance " "(eps < 0) for time " "t2={}"
                    ).format(parsedate(time[-1]))
                    raise ValueError(err_str)
                if epst1_fit < 0:
                    err_str = (
                        "Invalid value of BSRT emittance " "(eps < 0) for time " "t1={}"
                    ).format(parsedate(time[0]))
                    raise ValueError(err_str)
                # initial values for fit parameters
                a_init = epst1_fit
                tau_init = t2_fit / (np.log(epst2_fit) - np.log(epst1_fit))
                if verbose:
                    print("... fitting emittance {} for slot".format(plane))
                popt, pcov = curve_fit(
                    exp_fit, time, group[emit_key], p0=[a_init, tau_init]
                )
                psig = [np.sqrt(pcov[i, i]) for i in range(len(popt))]
                fit_data += [popt[0], psig[0], popt[1], psig[1]]

            return pd.Series([t1, t2] + fit_data, index=cols)

        out = self.emit.groupby(level=0).apply(fit_slot)
        if not out.empty:
            out = out.reset_index().set_index(["slots", "t1", "t2"])
            self.emit_fit = pd.concat([self.emit_fit, out], axis=0)

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
            slots = list(np.unique(self.emit.index.get_level_values(0)))
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
                print("... using start time {}".format(dumpdate(t1)))
        if t2 is None:
            t2 = self.t_end
            if verbose:
                print("... using end time {}".format(dumpdate(t2)))
        # check timestamp
        if t1 < self.t_start:
            raise ValueError(
                "Start time t1 = "
                + "%s < %s" % (t1, self.t_start)
                + " lies outside of data range!"
            )
        if t2 > self.t_end:
            err_str = ("End time t2 = {} > {} " "lies outside of data range!").format(
                t1, self.t_end
            )
            raise ValueError(err_str)
        if t2 < t1:
            err_str = ("End time smaller than start time, t2 = " "{} > {} = t1").format(
                t2, t1
            )
            raise ValueError(err_str)
        return t1, t2

    def plot(
        self,
        plane="h",
        t1=None,
        t2=None,
        slots=None,
        avg=10,
        fit=True,
        color=None,
        label=None,
        verbose=False,
        err_bar=False,
    ):
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
                    "lime",
                    "indigo",
                    "cyan",
                    "pink",
                    "orange",
                    "m",
                    "g",
                    "r",
                    "b",
                ]
            if color is None:
                c = colors.pop()
            else:
                c = color
            mask = np.logical_and(
                self.emit.loc[slot].index >= t1, self.emit.loc[slot].index <= t2
            )
            eps = self.emit.loc[slot][mask]
            # raw data
            if avg is None:
                pl.plot(
                    eps.index, eps["emit{}".format(plane)], ".", color=c, label=label
                )
            # averaged data
            else:
                if len(eps) < avg:
                    if verbose:
                        warn_str = (
                            "slot {} number of measurements: {} < "
                            "requested moving avg: {}"
                        )
                        print(warn_str.format(slot, len(eps), avg))
                        warn_str = "averaging over {} measurements"
                        print(warn_str.format(len(eps)))
                    window = len(eps)
                else:
                    window = avg
                epsavg = {}  # use a dictionary instead of a structured array
                for k in ["time", "emit{}".format(plane)]:
                    epsavg[k] = movingaverage(eps.reset_index()[k], window)
                pl.plot(
                    epsavg["time"],
                    epsavg["emit{}".format(plane)],
                    ".",
                    color=c,
                    label=label,
                )
        # plot fit with a black dashed line
        if fit:
            self.plot_fit(
                plane=plane,
                t1=t1,
                t2=t2,
                slots=slots,
                linestyle="--",
                color="k",
                verbose=verbose,
            )
        else:
            set_xaxis_date()
        pl.ylabel(r"$\epsilon_{N,%s} \ [\mu\mathrm{ m}]$" % plane.upper())
        pl.grid(b=True)
        if label is not None:
            pl.legend(loc="best", fontsize=12)
        return self

    def plot_fit(
        self,
        plane="h",
        t1=None,
        t2=None,
        slots=None,
        color=None,
        linestyle=None,
        label=None,
        verbose=False,
    ):
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
                    "lime",
                    "indigo",
                    "cyan",
                    "pink",
                    "orange",
                    "m",
                    "g",
                    "r",
                    "b",
                ]
            if color is None:
                c = colors.pop()
            else:
                c = color
            if linestyle is None:
                ls = "-"
            else:
                ls = linestyle
            mask = np.logical_and(
                self.emit.loc[slot].index >= t1, self.emit.loc[slot].index <= t2
            )
            ts = self.emit.loc[slot][mask].index
            fitparam = self.get_fit(slot=slot, t1=t1, t2=t2)
            pl.plot(
                ts,
                exp_fit(ts - ts[0], fitparam["a%s" % plane], fitparam["tau%s" % plane]),
                linestyle=ls,
                color=c,
                label=label,
            )
        set_xaxis_date()
        pl.ylabel(r"$\epsilon_{N,%s} \ [\mu m]$" % plane)
        pl.grid(b=True)
        return self
