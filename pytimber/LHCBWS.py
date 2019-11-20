try:
    import pandas as pd
    import numpy as np
    from scipy.optimize import curve_fit
except ImportError:
    print(
        "No module found: pandas, numpy, matplotlib and scipy"
        "modules should be present to run pytimbertools"
    )

from . import pytimber

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
            nbr = bin(int(float(bsb)) & 0xFFFFFFFF)
            for bit in nbr[2:][::-1]:
                if bit == "1":
                    bunchSelection.append(main_counter + counter)
                counter += 1
        main_counter += 32
    return bunchSelection


def _get_timber_variables(beam, wire, io="all", plane="all"):
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
    assert beam in ["B1", "B2"], ("beam = {} " "must be either 'B1' or 'B2'").format(
        beam
    )
    if beam == "B1":
        rl = "R"
    elif beam == "B2":
        rl = "L"
    assert wire in ["1", "2"], "wire = {} must be either 1 or 2".format(wire)
    assert io in ["all", "IN", "OUT"], (
        "io = {} must be either " "'all', 'IN' or 'OUT'"
    ).format(wire)
    assert plane in ["all", "H", "V"], (
        "plane = {} must be either " "'all', 'H' or 'V'"
    ).format(plane)

    var_template = [
        u"LHC.BWS.5{rl}4.{b}H{w}:NB_GATES",
        u"LHC.BWS.5{rl}4.{b}V{w}:NB_GATES",
        u"LHC.BWS.5{rl}4.{b}H{w}:BUNCH_SELECTION",
        u"LHC.BWS.5{rl}4.{b}V{w}:BUNCH_SELECTION",
        u"LHC.BWS.5{rl}4.{b}H.APP.IN:BETA",
        u"LHC.BWS.5{rl}4.{b}V.APP.IN:BETA",
        u"LHC.BWS.5{rl}4.{b}H.APP.OUT:BETA",
        u"LHC.BWS.5{rl}4.{b}V.APP.OUT:BETA",
        u"LHC.BWS.5{rl}4.{b}H.APP.IN:EMITTANCE_NORM",
        u"LHC.BWS.5{rl}4.{b}V.APP.IN:EMITTANCE_NORM",
        u"LHC.BWS.5{rl}4.{b}H.APP.OUT:EMITTANCE_NORM",
        u"LHC.BWS.5{rl}4.{b}V.APP.OUT:EMITTANCE_NORM",
        u"LHC.BWS.5{rl}4.{b}H{w}:PROF_POSITION_IN",
        u"LHC.BWS.5{rl}4.{b}V{w}:PROF_POSITION_IN",
        u"LHC.BWS.5{rl}4.{b}H{w}:PROF_POSITION_OUT",
        u"LHC.BWS.5{rl}4.{b}V{w}:PROF_POSITION_OUT",
        u"LHC.BWS.5{rl}4.{b}H{w}:PROF_DATA_IN",
        u"LHC.BWS.5{rl}4.{b}V{w}:PROF_DATA_IN",
        u"LHC.BWS.5{rl}4.{b}H{w}:PROF_DATA_OUT",
        u"LHC.BWS.5{rl}4.{b}V{w}:PROF_DATA_OUT",
        u"LHC.BWS.5{rl}4.{b}H{w}:GAIN",
        u"LHC.BWS.5{rl}4.{b}V{w}:GAIN",
        u"LHC.BOFSU:OFC_ENERGY",
    ]

    variables = [v.format(rl=rl.upper(), b=beam.upper(), w=wire) for v in var_template]
    if io != "all" and io in ["IN", "OUT"]:
        not_io = list(set(["IN", "OUT"]) - set([io]))[0]
        variables = [
            v for v in variables if ("." + not_io not in v and "_" + not_io not in v)
        ]
    if plane != "all" and plane in ["H", "V"]:
        not_plane = list(set(["H", "V"]) - set([plane]))[0]
        not_str = "{b}{p}".format(b=beam, p=not_plane)
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
        raise ValueError(
            ("End time smaller than start time, t2 = " "{} > {} = t1").format(t2, t1)
        )
    name = "%LHC%BWS%" + beam.upper()
    # check for which wire we have data
    data = db.get(db.search(name + "%NB_GATES%"), t1, t2)
    var_names = []
    for plane in "HV":
        nm = name + plane.upper()
        wire = ""
        try:
            if len(data[db.search(nm + "1%NB_GATES%")[0]][1]) != 0:
                wire += "1"
        except (KeyError, IndexError):
            pass
        try:
            if len(data[db.search(nm + "2%NB_GATES%")[0]][1]) != 0:
                wire += "2"
        except (KeyError, IndexError):
            pass
        if wire == "1" or wire == "2":
            pass
        elif wire == "":
            err_str = (
                "No data found for wire 1 or wire 2 as " "db.search('{}') is empty!"
            )
            err_str = err_str.format(name + "%NB_GATES%")
            raise ValueError(err_str)
        elif wire == "12":
            err_str = (
                "Both wires appear to be used! This class assumes that "
                "only one wire is used! db.search('{}') = {}!"
            )
            err_str = err_str.format(
                name + "%NB_GATES%", db.search(name + "%NB_GATES%")
            )
            raise ValueError(err_str)
        else:
            err_str = "This completely failed! wire = {} and " "db.search('{}') = {}!"
            err_str = err_str.format(
                wire, name + "%NB_GATES%", db.search(name + "%NB_GATES%")
            )
            raise ValueError(err_str)
    var_names = _get_timber_variables(beam, wire)
    data = db.get(var_names, t1, t2)
    # check that there is an energy value smaller than t1
    var_egev = "LHC.BOFSU:OFC_ENERGY"
    degev = data[var_egev]
    t1_new = t1
    # make sure data is not empty
    while degev[0].size == 0:
        if np.abs(t1_new - t1) > 30 * 24 * 60 * 60:
            raise ValueError(
                "Last logging time for LHC.BOFSU:OFC_ENERGY "
                "exceeds 1 month! Check your data!!!"
            )
            return
        t1_new = t1_new - 24 * 60 * 60
        degev = db.get([var_egev], t1_new, t2)[var_egev]
    # then check that first time stamp is smaller than t1
    while degev[0][0] > t1:
        if np.abs(t1_new - t1) > 30 * 24 * 60 * 60:
            raise ValueError(
                "Last logging time for LHC.BOFSU:OFC_ENERGY "
                "exceeds 1 month! Check your data!!!"
            )
            return
        t1_new = t1_new - 24 * 60 * 60
        degev = db.get([var_egev], t1_new, t2)[var_egev]
    # update data
    data["LHC.BOFSU:OFC_ENERGY"] = degev
    if convert_gate:
        if beam == "B1":
            rl = "R"
        elif beam == "B2":
            rl = "L"
        bunch_vars = [
            u"LHC.BWS.5{rl}4.{b}H{w}:BUNCH_SELECTION",
            u"LHC.BWS.5{rl}4.{b}V{w}:BUNCH_SELECTION",
        ]
        bunch_vars = [k.format(rl=rl, b=beam, w=wire) for k in bunch_vars]
        for b_v in bunch_vars:
            data[b_v] = list(data[b_v])
            val = data[b_v][1]
            # run the binary to bunch conversion
            data[b_v][1] = np.array([extract_bunch_selection(vv) for vv in val])
            data[b_v] = tuple(data[b_v])
    return data


def _timber_to_dict(beam, plane, direction, data, db):
    """
    converts timber data to dictionary of the slots number
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
    mulitIndex DataFrame contaning the 1D data
        the indexing of the DataFrame is:
               gain, egev, beta, emit
    time slots
      1   0
          1
      2   0
          1

    dict: dictionary with structure
      {time: [slot, pos, amp]},
    """
    keys_dic = ["gate", "bunch", "beta", "emit", "pos", "amp", "gain"]
    # dictionary of time,value
    tt, vv = {}, {}
    # make sure to have upper letters
    name = "%LHC%BWS%" + beam.upper() + plane.upper()
    # check which wire is used by checking the gates
    try:
        if db.search(name + "1%NB_GATES%")[0] in data.keys():
            wire = "1"
    except IndexError:
        pass
    try:
        if db.search(name + "2%NB_GATES%")[0] in data.keys():
            wire = "2"
    except IndexError:
        pass
    var_names = _get_timber_variables(beam, wire, io=direction, plane=plane)
    for kt, kd in zip(var_names, keys_dic):
        tt[kd] = data[kt][0]
        vv[kd] = data[kt][1]
    df_ws = []
    dbws_nd = {}
    for i, t in enumerate(tt["pos"]):
        pos = vv["pos"][i]  # position
        ngate = vv["gate"][i]
        gain = vv["gain"][i]
        amp = vv["amp"][i].reshape(int(ngate), len(pos))
        slots = vv["bunch"][i]
        # beta and eps time stamps are different but have the same ordering
        # all of the timestamps of the %APP% variables have the same timings
        tbe = tt["beta"][i]
        beta = vv["beta"][i]
        emit = vv["emit"][i]

        #    print 'MF',pos,ngate,gain,amp,slots,tbe,beta,emit
        # trouble with getting the energy
        igev = np.where(t - data["LHC.BOFSU:OFC_ENERGY"][0] >= 0.0)[0][-1]
        egev = data["LHC.BOFSU:OFC_ENERGY"][1][igev]
        if t not in dbws_nd.keys():
            dbws_nd[t] = []
        for idx, sl in zip(np.arange(ngate), slots):
            idx = int(idx)
            row_nd = (sl, pos, amp[idx])
            row_1d = (t, sl, tbe, gain, egev, beta, emit[idx])
            df_ws.append(row_1d)
            dbws_nd[t].append(row_nd)

    cols_1d = ["time", "slots", "time_app", "gain", "egev", "beta", "emit"]
    bws_1d = pd.DataFrame(data=df_ws, columns=cols_1d).set_index(["time", "slots"])
    # the goal here is to output a nice pd.DataFrame of the 1D data
    # and a horrible dictionnary --> array for the nD data
    for k in dbws_nd.keys():
        dbws_nd[k] = np.array(
            dbws_nd[k],
            dtype=[("slots", float), ("pos", np.ndarray), ("amp", np.ndarray)],
        )
    return bws_1d, dbws_nd


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
    data    : contains two dictionaries both indexed with the plane
               ('H' or 'V') and the direction ('IN' or 'OUT'). The first
               dict contains a MultiIndex DataFrame containing :
                          gain, egev, beta, emit
               time slots
                 1   0
                     1
                 2   0
                     1
                The second dict contains a dict['time'] --> structured array
                {time: [slot, pos, amp]}

    data_fit : contains two dictionaries both indexed with the plane
               ('H' or 'V') and the direction ('IN' or 'OUT'). The first
               dict contains a MultiIndex DataFrame containing :
                         emit_gauss, emit_gauss_err
               time slots
                 1   0
                     1
                 2   0
                     1
                The second dict contains a dict['time'] --> structured array
                {time:  [slot, amp_norm, p_gauss, pcov_gauss]},

    Methods:
    --------
    get_timber_data : returns raw data from pytimber
    fromdb : create BWS instance using the given pytimber database
    """

    def __init__(
        self,
        db=None,
        timber_vars=None,
        beam=None,
        data=None,
        t_start=None,
        t_end=None,
        data_fit=None,
    ):
        self.db = db
        self.timber_vars = timber_vars
        self.beam = beam
        self.data = data
        self.data_fit = data_fit
        self.t_start = t_start
        self.t_end = t_end

    @classmethod
    def fromdb(cls, t1, t2, beam="B1", db=None, verbose=False):
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
               profiles and other relevant parameters stored in self.data
               and self.data_fit.

               self.data: contains two dictionaries both indexed with the plane
               ('H' or 'V') and the direction ('IN' or 'OUT').
               The first dict contains a MultiIndex DataFrame containing :
                          gain, egev, beta, emit
               time slots
                 1   0
                     1
                 2   0
                     1
                The second dict contains a dict['time'] --> structured array
                {time: [slot, pos, amp]}

                self.data_fit: contains two dictionaries both indexed with the
                plane ('H' or 'V') and the direction ('IN' or 'OUT').
                The first dict contains a MultiIndex DataFrame containing :
                             emit_gauss, emit_gauss_err

                time, slots
                  1    0
                       1
                  2    0
                       1

                The second element contains a dict['time'] --> structured array
                {time: [slot, amp_norm, p_gauss, pcov_gauss]}


        """
        if beam not in ["B1", "B2"]:
            err_str = "beam = {} must be either 'B1' or 'B2'".format(beam)
            raise ValueError(err_str)
        # if no database is given create dummy database to extract data
        if db is None:
            db = pytimber.LoggingDB()
            if verbose:
                print(
                    "... no database given, creating default database "
                    "pytimber.LoggingDB()"
                )
        # get data from timber
        if verbose:
            print("... extracting data from timber")
        timber_data = _get_timber_data(
            beam=beam, t1=t1, t2=t2, convert_gate=True, db=db
        )
        timber_vars = timber_data.keys()
        # generate dictionary
        if verbose:
            print("... converting data")
        data_1d = {}
        data_nd = {}
        for plane in "HV":
            data_1d[plane] = {}
            data_nd[plane] = {}
            for io in "IN", "OUT":
                data = _timber_to_dict(
                    beam=beam, plane=plane, direction=io, data=timber_data, db=db
                )
                data_nd[plane][io] = data[1]
                data_1d[plane][io] = data[0]

        return cls(
            db=db,
            timber_vars=timber_vars,
            data=[data_1d, data_nd],
            t_start=t1,
            t_end=t2,
            beam=beam,
        )

    def get_timber_data(self, t1, t2, convert_gate=False):
        """
        return timber data for BWS. See LHCBWS._get_timber_data(...)
        for further documentation.
        """
        return _get_timber_data(
            beam=self.beam, t1=t1, t2=t2, db=self.db, convert_gate=False
        )

    def update_beta_energy(self, t1=None, t2=None, beth=None, betv=None, energy=None):
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
        assert self.data_fit is not None, (
            "No fitted data found, " "run fit_gaussian first"
        )
        if t1 is None:
            t1 = self.t_start
        if t2 is None:
            t2 = self.t_end

        def energy_func(x):
            energy_old = x["egev"]
            b_old = tb.betarel(energy_old)
            g_old = tb.gammarel(energy_old)
            b = tb.betarel(energy)
            g = tb.gammarel(energy)
            emit_gauss = x["emit_gauss"] * (b * g) / (b_old * g_old)
            emit_gauss_err = x["emit_gauss_err"] * (b * g) / (b_old * g_old)
            return pd.Series([emit_gauss, emit_gauss_err])

        def beta_func(x):
            beta_old = x["beta"]
            emit_gauss = x["emit_gauss"] * (beta_old) / (beta)
            emit_gauss_err = x["emit_gauss_err"] * (beta_old) / (beta)
            return pd.Series([emit_gauss, emit_gauss_err])

        for plane, beta in zip("HV", [beth, betv]):
            for io in "IN", "OUT":
                data = self.data[0][plane][io].reset_index()
                data_fit = self.data_fit[0][plane][io].reset_index()
                mask = np.logical_and(data_fit["time"] >= t1, data_fit["time"] <= t2)
                data_fit_filt = data_fit.loc[mask].copy()
                data_filt = data.loc[mask].copy()
                if energy is not None:
                    data_fit_filt[
                        ["emit_gauss", "emit_gauss_err"]
                    ] = data_fit_filt.apply(energy_func, axis=1)
                    data_filt["egev"] = energy
                if beta is not None:
                    data_fit_filt[["emit_gauss", "emit_gauss_err"]] = data_filt.apply(
                        beta_func, axis=1
                    )
                    data_filt["beta"] = beta

                data.loc[mask] = data_filt
                data_fit.loc[mask] = data_fit_filt
                self.data[0][plane][io] = data.set_index(["time", "slots"])
                self.data_fit[0][plane][io] = data_fit.set_index(["time", "slots"])

    def fit_gaussian(self):
        """
        Fits gaussian to the previously fetched data

        Returns:
        --------
        data_fit_df: MulitIndex DataFrame containing the fitted 'emit_gauss'
            and the 'emit_gauss_err'
                         emit_gauss, emit_gauss_err

            time, slots

            1   0
            1
            2   0
            1

        data_fit_dic: a dict['time'] --> structured array
            contains the fit params
            {time: [slot, amp_norm, p_gauss, pcov_gauss]}
        """
        assert self.data is not None, "No data, run from_db first"
        data_fit_df = {}
        data_fit_dic = {}
        for plane in ["H", "V"]:
            data_fit_df[plane] = {}
            data_fit_dic[plane] = {}
            for direction in ["IN", "OUT"]:
                data_df = self.data[0][plane][direction]
                data_dic = self.data[1][plane][direction]
                df_fit, dic_fit = self._fit_gaussian(data_df, data_dic)
                data_fit_df[plane][direction] = df_fit
                data_fit_dic[plane][direction] = dic_fit
        self.data_fit = [data_fit_df, data_fit_dic]
        return data_fit_df, data_fit_dic

    def _fit_gaussian(self, data_df, data_nd):
        """
        Fits gaussian to the the provided data

        Returns:
        --------
        data_fit_df: MulitIndex DataFrame containing the fitted 'emit_gauss'
            and the 'emit_gauss_err'
                         emit_gauss, emit_gauss_err

            time, slots

            1   0
            1
            2   0
            1

        data_fit_dic: a dict['time'] --> structured array
            contains the fit params
            {time: [slot, amp_norm, p_gauss, pcov_gauss]}
        """
        df_fit = []
        dic_fit = {}
        for t, arrays in data_nd.items():
            if t not in dic_fit.keys():
                dic_fit[t] = []
            for idx, sl in enumerate(arrays["slots"]):
                amp = arrays["amp"][idx]
                pos = arrays["pos"][idx]
                beta = data_df.loc[(t, sl)]["beta"]
                egev = data_df.loc[(t, sl)]["egev"]
                idx_max = np.argmax(np.abs(amp))
                # flip in case profile is mirrored on x-axis
                if amp[idx_max] < 0:
                    amp = -amp
                # put smallest value to 0
                amp = amp - np.min(amp)
                dx = np.abs(np.diff(pos))
                int_dist = (dx * amp[:-1]).sum()
                # case where amplitude = 0
                if int_dist == 0:
                    amp_norm = amp
                    sigma_gauss = 0
                    sigma_gauss_err = 0
                    emit_gauss = 0
                    emit_gauss_err = 0
                    p = np.zeros(4)
                    pcov = np.zeros((4, 4))
                else:
                    amp_norm = amp / int_dist
                    p, pcov = curve_fit(
                        f=tb.gauss_pdf, xdata=pos, ydata=amp_norm, p0=[0, 1, 0, 1000]
                    )
                    sigma_gauss = p[3]
                    sigma_gauss_err = np.sqrt(pcov[3, 3])
                    emit_gauss = tb.emitnorm(sigma_gauss ** 2 / beta, egev) * 1.0e-6
                    emit_gauss_err = (
                        tb.emitnorm(2 * sigma_gauss * sigma_gauss_err / beta, egev)
                        * 1.0e-6
                    )

                row_nd = (sl, amp_norm, p, pcov)
                row_1d = (t, sl, emit_gauss, emit_gauss_err)
                df_fit.append(row_1d)
                dic_fit[t].append(row_nd)

        cols = ["time", "slots", "emit_gauss", "emit_gauss_err"]
        df_fit = pd.DataFrame(df_fit, columns=cols)
        df_fit = df_fit.set_index(["time", "slots"])
        ftype = [
            ("slots", float),
            ("amp_norm", np.ndarray),
            ("p_gauss", np.ndarray),
            ("pcov_gauss", np.ndarray),
        ]
        for k in dic_fit.keys():
            dic_fit[k] = np.array(dic_fit[k], dtype=ftype)
        return df_fit, dic_fit
