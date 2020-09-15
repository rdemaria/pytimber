import logging
import os
from datetime import datetime

import numpy as np
import pytest

import pytimber

ts1 = "2018-05-01 00:00:00.000"
ts2 = "2018-05-02 00:00:00.000"
ts3 = '2018-06-01 00:00:00.000'
ts1dt = datetime.strptime(ts1, '%Y-%m-%d %H:%M:%S.%f')
ts2dt = datetime.strptime(ts2, '%Y-%m-%d %H:%M:%S.%f')
ts3dt = datetime.strptime(ts3, '%Y-%m-%d %H:%M:%S.%f')

var_name = ['TD68.BTVD.683458.B1/Image#imageSet', 'SPS.BWS.51995.H_ROT.APP.IN:EMIT_AV']

NXCALS_COL_NAMES = {'nxcals_entity_id', 'nxcals_timestamp', 'nxcals_value', 'nxcals_variable_name'}

HAS_KERBEROS = 'CI' not in os.environ.keys()


class TestSparkExtensions:
    @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
    def setup_class(self):
        self.nxcals = pytimber.NXCals(loglevel=logging.INFO)

    @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
    def test_spark2numpy(self):
        spark_dataset = self.get_spark_dataset(var_name[0], ts1, ts2)
        name2numpy = self.nxcals.spark2numpy(spark_dataset)
        assert NXCALS_COL_NAMES == set(name2numpy.keys())
        assert var_name[0] == name2numpy['nxcals_variable_name'][0]
        self._assert_value_correct(name2numpy['nxcals_value'])

    @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
    def test_spark2pandas_subarrays_with_same_length(self):
        spark_dataset = self.get_spark_dataset(var_name[0], ts1, ts2)
        pdf = self.nxcals.spark2pandas(spark_dataset)
        assert NXCALS_COL_NAMES == set(pdf.columns)
        assert var_name[0] == pdf['nxcals_variable_name'][0]
        self._assert_value_correct(pdf['nxcals_value'])
        entity_id = pdf['nxcals_entity_id'][0]
        assert entity_id > 0
        assert int == type(entity_id)
        assert pdf.index[0] >= ts1dt
        assert pdf.index[-1] <= ts2dt

    @pytest.mark.skipif(not HAS_KERBEROS, reason="kerberos authentication not available on gitlabCI")
    def test_spark2pandas_subarrays_with_different_length(self):
        spark_dataset = self.get_spark_dataset(var_name[0], ts1, ts3)
        pdf = self.nxcals.spark2pandas(spark_dataset)
        self._assert_value_correct(pdf['nxcals_value'])

    def get_spark_dataset(self, var, t1, t2):
        return self.nxcals.DataQuery.byVariables().system("CMW").startTime(t1).endTime(t2).variable(var).buildDataset()

    def _assert_value_correct(self, arr_of_arrs):
        assert arr_of_arrs.ndim == 1
        long_value = arr_of_arrs[0][0]
        assert long_value > 0
        assert np.int64 == long_value.dtype
