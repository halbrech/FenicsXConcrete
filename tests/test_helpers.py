import pytest
from pint import UnitRegistry

from fenicsxconcrete.helper import Parameters

ureg = UnitRegistry()


def test_parameters() -> None:
    parameters = Parameters()
    parameters["length"] = 42.0 * ureg.cm

    # Check if units are converted correctly
    assert parameters["length"].units == ureg.meter

    parameters_2 = Parameters()
    parameters_2["temperature"] = 2.0 * ureg.kelvin

    parameters_combined = parameters + parameters_2
    keys = parameters_combined.keys()
    assert "length" in keys and "temperature" in keys
    assert (
        parameters_combined["length"] == parameters["length"]
        and parameters_combined["temperature"] == parameters_2["temperature"]
    )


def test_parameter_dic_functions() -> None:
    parameters = Parameters()
    # testing if adding None to dictionary works
    new = parameters + None
    assert new is parameters


def test_parameter_dic_update() -> None:
    parameters = Parameters()

    # testing that update still requires a pint object
    p_wo_pint = {"length": 0.006}
    with pytest.raises(AssertionError):
        parameters.update(p_wo_pint)

    # testing that conversion to base units works with update
    length = 6000
    p_with_pint = {"length": length * ureg("mm")}
    parameters.update(p_with_pint)

    assert parameters["length"].magnitude == length / 1000
