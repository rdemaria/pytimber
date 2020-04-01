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
                    .build().toString()
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

    def test_get_aligned(self, nxcals):
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

        def test_get_fundamentals(self, nxcals):
            # TODO
            assert True

        def test_search_fundamental(self, nxcals):
            # TODO
            assert True

    class TestLHC:
        def test_get_intervals(self, nxcals):
            # TODO
            assert True

        def test_get_fill_data(self, nxcals):
            # TODO
            assert True

        def test_get_fill_by_time(self, nxcals):
            # TODO
            assert True

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

        def test_getvariables(self, nxcals):
            # TODO
            assert True

        def test_getvariableslist(self, nxcals):
            # TODO
            assert True

        @pytest.mark.parametrize(
            "variable, t1, t2, idx1, idx2, value",
            [
                (
                    "LHC.BOFSU:BPM_NAMES_H",
                    "2016-03-28 00:00:00.000",
                    "2016-03-28 23:59:59.999",
                    0,
                    123,
                    "BPM.16L3.B1",
                )
            ],
        )
        def test_get_vectorstring(
            self, nxcals, variable, t1, t2, idx1, idx2, value
        ):
            t, v = nxcals.getVariable(variable, t1, t2)
            assert v[idx1][idx2] == value
