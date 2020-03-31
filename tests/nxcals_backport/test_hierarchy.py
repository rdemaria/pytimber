import pytest
import functools


@pytest.mark.unit
class TestUnit:

    @staticmethod
    def _get_v(nxcals):
        return nxcals.tree.get_vars()

    def test_should_get_variable_list(self, monkeypatch, nxcals):
        def mockreturn():
            return ["AAA", "BBB", "CCC"]

        monkeypatch.setattr(nxcals.tree, "get_vars", mockreturn)
        variable_list = TestUnit._get_v(nxcals)

        assert len(variable_list) == 3


@pytest.mark.integration
class TestIntegration:

    @staticmethod
    def _rgetattr(obj, attribute, *args):
        def _getattr(o, attr):
            return getattr(o, attr, *args)

        return functools.reduce(_getattr, [obj] + attribute.split('.'))

    @pytest.mark.core
    @pytest.mark.parametrize("path, node", [("LHC", "Beam_Instrumentation"),
                                            ('LHC.ALICE', 'Temperatures')])
    def test_hierarchy(self, nxcals, path, node):
        assert hasattr(TestIntegration._rgetattr(nxcals.tree, path), node)

    @pytest.mark.core
    @pytest.mark.parametrize("path, element, count", [("LHC.ALICE.Temperatures", 'ALICE.BEAMPIPE.SENSOR00:TEMP', 14),
                                                      ('SPS.Kickers.Injection.Magnets', 'MKP.11931:TEMPERATURE.1', 11)])
    def test_get_vars(self, nxcals, path, element, count):
        variables = TestIntegration._rgetattr(nxcals.tree, path).get_vars()
        assert element in variables
        assert len(variables) == count
