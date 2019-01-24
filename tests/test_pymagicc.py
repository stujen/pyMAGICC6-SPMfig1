import os
from unittest.mock import MagicMock


import pandas as pd
import numpy as np
import pytest


from pymagicc import _magiccpath, read_scen_file, rcp26, rcp45, rcp60, rcp85, run
from pymagicc.io import MAGICCData


RCP26_SCEN_FILE = os.path.join(_magiccpath, "RCP26.SCEN")
RCP85_SCEN_FILE = os.path.join(_magiccpath, "RCP85.SCEN")
WORLD_ONLY = read_scen_file(
    os.path.join(os.path.dirname(__file__), "./test_data/WORLD_ONLY.SCEN")
)


def test_read_scen_file():
    MAGICCData.read = MagicMock()
    result = read_scen_file(RCP26_SCEN_FILE)

    assert isinstance(result, MAGICCData)
    MAGICCData.read.assert_called_with(RCP26_SCEN_FILE)


def do_basic_run_checks(results):
    assert (
        results.metadata["magicc-version"]
        == "6.8.01 BETA, 7th July 2012 - live.magicc.org"
    )
    assert (
        results.metadata["parameters"]["allcfgs"]["file_emissionscenario"]
        == "SCENARIO.SCEN"
    )


magicc7_not_included_msg = (
    "A MAGICC7 binary is not yet included with Pymagicc and hence regression tests "
    "are not of any use."
)


@pytest.mark.slow
def test_run_rcp26(package):
    if package.version == 7:
        pytest.skip(magicc7_not_included_msg)
    results = run(rcp26, magicc_version=package.version)

    result_temp = results.df[
        (results.df.variable == "Surface Temperature")
        & (results.df.time == 2100)
        & (results.df.region == "World")
    ].value.values
    np.testing.assert_allclose(result_temp, 1.563254, rtol=1e-5)
    do_basic_run_checks(results)


@pytest.mark.slow
def test_run_rcp45(package):
    if package.version == 7:
        pytest.skip(magicc7_not_included_msg)
    results = run(rcp45, magicc_version=package.version)

    result_temp = results.df[
        (results.df.variable == "Surface Temperature")
        & (results.df.time == 2100)
        & (results.df.region == "World")
    ].value.values
    np.testing.assert_allclose(result_temp, 2.497057, rtol=1e-5)
    do_basic_run_checks(results)


@pytest.mark.slow
def test_run_rcp60(package):
    if package.version == 7:
        pytest.skip(magicc7_not_included_msg)
    results = run(rcp60, magicc_version=package.version)

    result_temp = results.df[
        (results.df.variable == "Surface Temperature")
        & (results.df.time == 2100)
        & (results.df.region == "World")
    ].value.values
    np.testing.assert_allclose(result_temp, 3.102484, rtol=1e-5)
    do_basic_run_checks(results)


@pytest.mark.slow
def test_run_rcp85(package):
    if package.version == 7:
        pytest.skip(magicc7_not_included_msg)
    results = run(rcp85, magicc_version=package.version)

    result_temp = results.df[
        (results.df.variable == "Surface Temperature")
        & (results.df.time == 2100)
        & (results.df.region == "World")
    ].value.values
    np.testing.assert_allclose(result_temp, 4.676012, rtol=1e-5)
    do_basic_run_checks(results)


@pytest.mark.slow
def test_parameters():
    results = run(rcp26, out_parameters=True, core_climatesensitivity=1.5)
    assert results.metadata["parameters"]["allcfgs"]["core_climatesensitivity"] == 1.5
    # Test removal of newlines in PARAMETERS.out
    assert "H\nFC134a" not in results.metadata["parameters"]["allcfgs"]["fgas_names"]


@pytest.mark.slow
def test_default_config():
    results = run(rcp26, out_parameters=True)
    assert results.metadata["parameters"]["allcfgs"]["core_climatesensitivity"] == 3
    assert results.metadata["parameters"]["years"]["startyear"] == 1765


@pytest.mark.slow
def test_set_years():
    results = run(rcp26, out_parameters=True, startyear=1900, endyear=2000)
    assert results.metadata["parameters"]["years"]["startyear"] == 1900
    assert results.metadata["parameters"]["years"]["endyear"] == 2000
    assert results.df.time.min() == 1900
    assert results.df.time.max() == 2000


@pytest.mark.xfail(
    reason="Not sure how best to fail reading CARBONCYCLE.OUT at the moment"
)
@pytest.mark.slow
def test_out_carboncycle():
    out = run(rcp26, out_carboncycle=1)
    assert "CARBONCYCLE" in out.keys()
