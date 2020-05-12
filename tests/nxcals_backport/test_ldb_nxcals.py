import datetime

import pytest
import jpype


@pytest.mark.unit
class TestUnit:
    def test_timestamp(self, nxcals):
        import time

        now = time.time()
        ts_now = nxcals.toTimestamp(now)
        now2 = nxcals.fromTimestamp(ts_now, unixtime=True)
        dt_now2 = nxcals.fromTimestamp(ts_now, unixtime=False)
        assert now == now2
        assert (
            str(ts_now)[:25] == dt_now2.strftime("%Y-%m-%d %H:%M:%S.%f")[:25]
        )

        time_str = "2015-10-12 12:12:32.453255123"
        ta = nxcals.toTimestamp(time_str)
        assert ta.toLocaleString() == "Oct 12, 2015 12:12:32 PM"
        unix = nxcals.fromTimestamp(ta, unixtime=True)
        assert unix == 1444644752.4532552
        assert (
            time.strftime("%b %-d, %Y %-I:%M:%S %p", time.localtime(unix))
            == "Oct 12, 2015 12:12:32 PM"
        )

    @staticmethod
    def _search(nxcals, pattern):
        return nxcals.search(pattern)

    @pytest.mark.core
    def test_should_search(self, monkeypatch, nxcals):
        def mockreturn(pattern):
            _Variable = jpype.JPackage(
                "cern"
            ).nxcals.api.backport.domain.core.metadata.Variable

            var_list = []
            for i in [1, 2, 3]:
                var_list.append(
                    _Variable.builder()
                    .variableName(pattern.replace("%", str(i)))
                    .build()
                    .toString()
                )
            return var_list

        monkeypatch.setattr(nxcals, "search", mockreturn)
        variable_list = TestUnit._search(nxcals, "VARIABLE%")

        assert "VARIABLE1" in variable_list


@pytest.mark.integration
class TestIntegration:
    @pytest.mark.core
    @pytest.mark.parametrize(
        "pattern, variable_name, count", [("HX:BETA%", "HX:BETASTAR_IP1", 4)]
    )
    def test_search(self, nxcals, pattern, variable_name, count):
        variables = nxcals.search(pattern)
        assert variable_name in variables
        assert len(variables) == count

    class TestGet:
        @pytest.mark.core
        @pytest.mark.parametrize(
            "t1, t2, variable, count, ts, value",
            [
                (
                    "2015-05-13 12:00:00.000",
                    "2015-05-15 00:00:00.000",
                    "HX:FILLN",
                    6,
                    1431523684.764,
                    3715.0,
                )
            ],
        )
        def test_get_simple(self, nxcals, t1, t2, variable, count, ts, value):
            data = nxcals.get(variable, t1, t2)

            t, v = data[variable]
            assert len(t) == count
            assert len(v) == count

            assert t[0] == ts
            assert v[0] == value

        import datetime

        @pytest.mark.parametrize(
            "t1, t2, variable, dt",
            [
                (
                    "2015-05-13 12:00:00.000",
                    "2015-05-15 00:00:00.000",
                    "HX:FILLN",
                    datetime.datetime(2015, 5, 13, 15, 28, 4, 764000),
                )
            ],
        )
        def test_get_unixtime(self, nxcals, t1, t2, variable, dt):
            data = nxcals.get(variable, t1, t2, unixtime=False)
            t, v = data[variable]

            assert t[0] == dt

        @pytest.mark.parametrize(
            "t1, t2, variable, count",
            [
                (
                    "2015-05-13 12:00:00.000",
                    "2015-05-13 12:00:01.000",
                    "LHC.BQBBQ.CONTINUOUS_HS.B1:ACQ_DATA_H",
                    4096,
                )
            ],
        )
        def test_get_vectornumeric(self, nxcals, t1, t2, variable, count):
            data = nxcals.get(variable, t1, t2)

            t, v = data[variable]

            for vv in v:
                assert len(vv) == count

    @pytest.mark.parametrize(
        "pattern_or_list, start_time, end_time",
        [
            (
                "%:LUMI_TOT_INST",
                "2018-10-17 15:00:00.000",
                "2018-10-17 15:05:00.000",
            )
        ],
    )
    def test_get_aligned(self, nxcals, pattern_or_list, start_time, end_time):
        # TODO
        assert True

    @pytest.mark.parametrize(
        "pattern, variable, description",
        [
            (
                "%:LUMI_TOT_INST",
                "ATLAS:LUMI_TOT_INST",
                "ATLAS: Total instantaneous luminosity summed over all bunches",
            )
        ],
    )
    def test_getdescription(self, nxcals, pattern, variable, description):
        descriptions = nxcals.getDescription(pattern)

        assert descriptions[variable] == description

    class TestFundamentals:
        @pytest.mark.parametrize(
            "variable, t1, t2, fundamental, value",
            [
                (
                    "CPS.TGM:USER",
                    "2015-05-15 12:00:00.000",
                    "2015-05-15 12:01:00.000",
                    "CPS:%:SFTPRO%",
                    "SFTPRO2",
                )
            ],
        )
        def test_filter_by_fundamentals(
            self, nxcals, variable, t1, t2, fundamental, value
        ):
            t, v = nxcals.getVariable(
                variable, t1, t2, fundamental=fundamental
            )
            assert v[0] == value

        @pytest.mark.parametrize(
            "t1, t2, pattern, value",
            [
                (
                    "2018-10-17 15:00:00.000",
                    "2018-10-17 15:05:00.000",
                    "CPS:%:%",
                    "CPS:AD:AD",
                )
            ],
        )
        def test_get_fundamentals(self, nxcals, t1, t2, pattern, value):
            fundamentals = nxcals.getFundamentals(t1, t2, pattern)
            assert sorted(fundamentals)[0] == value

        @pytest.mark.parametrize(
            "t1, t2, pattern, value, length",
            [
                (
                    "2018-10-17 05:15:00.000",
                    "2018-10-17 05:16:00.000",
                    "CPS:%:%",
                    "CPS:EAST_NORTH:EAST2",
                    5,
                )
            ],
        )
        def test_search_fundamental(
            self, nxcals, t1, t2, pattern, value, length
        ):
            fundamentals = nxcals.searchFundamental(pattern, t1, t2)
            assert sorted(fundamentals)[0] == value
            assert len(fundamentals) == length

    class TestLHC:
        @pytest.mark.parametrize(
            "start_time, end_time, mode1, mode2, int_cnt, first_fill, int_start, int_end",
            [
                (
                    "2018-09-23 10:00:00.000",
                    "2018-09-26 00:00:00.000",
                    "SETUP",
                    "STABLE",
                    4,
                    7212,
                    "2018-09-23 16:15:03",
                    "2018-09-23 23:52:36",
                )
            ],
        )
        def test_get_intervals(
            self,
            nxcals,
            start_time,
            end_time,
            mode1,
            mode2,
            int_cnt,
            first_fill,
            int_start,
            int_end,
        ):
            intervals = nxcals.getIntervalsByLHCModes(
                nxcals.toTimestamp(start_time),
                nxcals.toTimestamp(end_time),
                mode1,
                mode2,
            )
            assert len(intervals) == int_cnt
            assert intervals[0][0] == first_fill
            assert (
                datetime.datetime.utcfromtimestamp(intervals[0][1]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                == int_start
            )
            assert (
                datetime.datetime.utcfromtimestamp(intervals[0][2]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                == int_end
            )

        @pytest.mark.parametrize(
            "fill_nr, fill_start_time, fill_last_mode, mode_start_time",
            [(7218, "2018-09-24 22:38:03", "RAMPDOWN", "2018-09-25 14:12:45")],
        )
        def test_get_fill_data(
            self,
            nxcals,
            fill_nr,
            fill_start_time,
            fill_last_mode,
            mode_start_time,
        ):
            fill_data = nxcals.getLHCFillData(fill_nr)

            last = len(fill_data["beamModes"]) - 1
            assert (
                datetime.datetime.utcfromtimestamp(
                    fill_data["startTime"]
                ).strftime("%Y-%m-%d %H:%M:%S")
                == fill_start_time
            )
            assert fill_data["beamModes"][last]["mode"] == fill_last_mode
            assert (
                datetime.datetime.utcfromtimestamp(
                    fill_data["beamModes"][last]["startTime"]
                ).strftime("%Y-%m-%d %H:%M:%S")
                == mode_start_time
            )

        @pytest.mark.parametrize(
            "start_time, end_time, beam_modes, fills_cnt, first_fill",
            [
                (
                    "2018-09-28 00:00:00.000",
                    "2018-10-02 00:00:00.000",
                    "STABLE",
                    5,
                    7234,
                )
            ],
        )
        def test_get_fill_by_time(
            self,
            nxcals,
            start_time,
            end_time,
            beam_modes,
            fills_cnt,
            first_fill,
        ):
            fills = nxcals.getLHCFillsByTime(start_time, end_time, beam_modes)
            assert len(fills) == fills_cnt
            assert fills[0]["fillNumber"] == first_fill

    def test_get_metadata(self, nxcals):
        # TODO
        assert True

    import numpy as np

    @pytest.mark.parametrize(
        "variable, t1, t2, scale_interval, scale_algorithm, scale_size, result",
        [
            (
                "MSC01.ZT8.107:COUNTS",
                "2015-05-15 12:00:00.000",
                "2015-05-15 15:00:00.000",
                "HOUR",
                "SUM",
                "1",
                np.array([1174144.0, 1172213.0, 1152831.0]),
            )
        ],
    )
    def test_getscaled(
        self,
        nxcals,
        variable,
        t1,
        t2,
        scale_interval,
        scale_algorithm,
        scale_size,
        result,
    ):
        data = nxcals.getScaled(
            variable,
            t1,
            t2,
            scaleInterval=scale_interval,
            scaleAlgorithm=scale_algorithm,
            scaleSize=scale_size,
        )

        t, v = data[variable]

        assert (v[:4] - result).sum() == 0

    @pytest.mark.parametrize(
        "variables , t1, t2, scale_interval, scale_algorithm, scale_size, result",
        [
            (
                ["IP.NSRCGEN:BIASDISCAQNI", "IP.NSRCGEN:BIASDISCAQNV"],
                "2018-12-10 00:10:05.000",
                "2018-12-10 00:10:45.000",
                "SECOND",
                "SUM",
                "10",
                np.array(
                    [
                        -7.630000114440918,
                        -12.130000114440918,
                        -15.59000015258789,
                    ]
                ),
            )
        ],
    )
    def test_getscaled_for_list(
        self,
        nxcals,
        variables,
        t1,
        t2,
        scale_interval,
        scale_algorithm,
        scale_size,
        result,
    ):
        data = nxcals.getScaled(
            variables,
            t1,
            t2,
            scaleInterval=scale_interval,
            scaleAlgorithm=scale_algorithm,
            scaleSize=scale_size,
        )

        t, v = data[variables[0]]
        assert self.is_close((v[1:4] - result).sum(), 0, 6)

    @staticmethod
    def is_close(float_a, float_b, prec):
        if round(float_a, prec) == round(float_b, prec):
            return True
        return False

    @pytest.mark.parametrize(
        "variable, t1, t2, min_timestamp, std_deviation",
        [
            (
                "LHC.BOFSU:EIGEN_FREQ_2_B1",
                "2016-03-01 00:00:00.000",
                "2016-04-03 00:00:00.000",
                1457962796.972,
                0.00401594,
            )
        ],
    )
    def test_getstats(
        self, nxcals, variable, t1, t2, min_timestamp, std_deviation
    ):
        stat = nxcals.getStats(variable, t1, t2)[variable]

        assert stat.MinTstamp == min_timestamp
        assert self.is_close(stat.StandardDeviationValue, std_deviation, 8)

    @pytest.mark.parametrize(
        "pattern, variable, unit",
        [("%:LUMI_TOT_INST", "ATLAS:LUMI_TOT_INST", "Hz/ub")],
    )
    def test_getunit(self, nxcals, pattern, variable, unit):
        units = nxcals.getUnit(pattern)
        assert units[variable] == unit

    class TestVariable:
        @pytest.mark.parametrize(
            "variable, t1, t2, tstamp_count, value_count, tstamp, value",
            [
                (
                    "HX:FILLN",
                    "2015-05-13 12:00:00.000",
                    "2015-05-15 00:00:00.000",
                    6,
                    6,
                    1431523684.764,
                    3715.0,
                )
            ],
        )
        def test_getvariable(
            self,
            nxcals,
            variable,
            t1,
            t2,
            tstamp_count,
            value_count,
            tstamp,
            value,
        ):
            t, v = nxcals.getVariable(variable, t1, t2)

            assert len(t) == tstamp_count
            assert len(v) == value_count

            assert t[0] == tstamp
            assert v[0] == value

        @pytest.mark.parametrize("pattern, var_cnt", [("%LUMI%INST", 10)])
        def test_get_variables_with_name_like_pattern(
            self, nxcals, pattern, var_cnt
        ):
            # Currently Java VariableSet object returned
            variables = nxcals.getVariableSet(pattern)
            assert len(variables) == var_cnt

        @pytest.mark.parametrize(
            "varlist", [(["ALICE:BUNCH_LUMI_INST", "ALICE:LUMI_TOT_INST"])]
        )
        def test_get_variables_with_name_in_list(self, nxcals, varlist):
            # Currently Java VariableSet object returned
            variables = nxcals.getVariableSet(varlist)
            assert len(variables) == 2

        @pytest.mark.parametrize(
            "variable, t1, t2, idx1, idx2, value",
            [
                (
                    "HIE-BCAM-T3M04:RAWMEAS#SEQ_ID",
                    "2018-03-26 00:00:00.000",
                    "2018-03-26 06:00:00.000",
                    0,
                    2,
                    "SEQ_T3M04_FRONT_03",
                )
            ],
        )
        def test_get_vectorstring(
            self, nxcals, variable, t1, t2, idx1, idx2, value
        ):
            t, v = nxcals.getVariable(variable, t1, t2)
            assert v[idx1][idx2] == value
