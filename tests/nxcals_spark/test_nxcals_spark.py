import os
from datetime import datetime

import numpy as np
import pytest


@pytest.mark.integration
class TestIntegration:

    @pytest.mark.core
    @pytest.mark.parametrize(
        "pattern_or_list, t1, t2, system, expected1, given, expected2",
        [
            (
                "%:LUMI_TOT_INST",
                "2015-05-13 12:00:00.000", "2015-05-15 00:00:00.000",
                "CMW",
                ['ATLAS:LUMI_TOT_INST', 'CMS:LUMI_TOT_INST', 'LHCB:LUMI_TOT_INST'],
                'ATLAS:LUMI_TOT_INST',
                (1925, ),
            )
        ],
    )
    def test_searchByVariables(self, nxcals, pattern_or_list, t1, t2, system, expected1, given, expected2):
        result = nxcals.searchByVariables(pattern_or_list, t1, t2, system)
        assert sorted(list(result.keys())) == expected1
        assert result[given][0].shape == expected2

    class TestSparkExtensions:

        ts1 = "2018-05-01 00:00:00.000"
        ts2 = "2018-05-02 00:00:00.000"
        ts3 = '2018-06-01 00:00:00.000'
        ts1dt = datetime.strptime(ts1, '%Y-%m-%d %H:%M:%S.%f')
        ts2dt = datetime.strptime(ts2, '%Y-%m-%d %H:%M:%S.%f')
        ts3dt = datetime.strptime(ts3, '%Y-%m-%d %H:%M:%S.%f')

        var_name = ['TD68.BTVD.683458.B1/Image#imageSet', 'SPS.BWS.51995.H_ROT.APP.IN:EMIT_AV']

        NXCALS_COL_NAMES = {'nxcals_entity_id', 'nxcals_timestamp', 'nxcals_value', 'nxcals_variable_name'}

        HAS_KERBEROS = 'CI' not in os.environ.keys()

        @pytest.mark.core
        @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
        def test_spark2numpy(self, nxcals):
            spark_dataset = self.get_spark_dataset(nxcals, self.var_name[0], self.ts1, self.ts2)
            name2numpy = nxcals.spark2numpy(spark_dataset)
            assert self.NXCALS_COL_NAMES == set(name2numpy.keys())
            assert self.var_name[0] == name2numpy['nxcals_variable_name'][0]
            self._assert_value_correct(name2numpy['nxcals_value'])

        @pytest.mark.core
        @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
        def test_spark2pandas_subarrays_with_same_length(self, nxcals):
            spark_dataset = self.get_spark_dataset(nxcals, self.var_name[0], self.ts1, self.ts2)
            pdf = nxcals.spark2pandas(spark_dataset)
            assert self.NXCALS_COL_NAMES == set(pdf.columns)
            assert self.var_name[0] == pdf['nxcals_variable_name'][0]
            self._assert_value_correct(pdf['nxcals_value'])
            entity_id = pdf['nxcals_entity_id'][0]
            assert entity_id > 0
            assert int == type(entity_id)
            assert pdf.index[0] >= self.ts1dt
            assert pdf.index[-1] <= self.ts2dt

        @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
        def test_spark2pandas_subarrays_with_different_length(self, nxcals):
            spark_dataset = self.get_spark_dataset(nxcals, self.var_name[0], self.ts1, self.ts3)
            pdf = nxcals.spark2pandas(spark_dataset)
            self._assert_value_correct(pdf['nxcals_value'])

        def get_spark_dataset(self, nxcals, var, t1, t2):
            return nxcals.DataQuery.byVariables().system("CMW").startTime(t1).endTime(t2).variable(var).buildDataset()

        def _assert_value_correct(self, arr_of_arrs):
            assert arr_of_arrs.ndim == 1
            long_value = arr_of_arrs[0][0]
            assert long_value > 0
            assert np.int64 == long_value.dtype