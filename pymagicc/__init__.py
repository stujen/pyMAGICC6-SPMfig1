# Copyright (c) 2017 pymagicc authors:
#   Robert Gieseke <robert.gieseke@pik-potsdam.de>
# Free software under GNU Affero General Public License v3, see LICENSE
#
# The compiled MAGICC binary (http://www.magicc.org/download6) by Tom Wigley,
# Sarah Raper, and Malte Meinshausen included in this package is licensed under
# a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported
# License (https://creativecommons.org/licenses/by-nc-sa/3.0/)


import logging
import os
import subprocess


from ._version import get_versions
from .config import config as _config
from .core import MAGICC6, MAGICC7  # noqa
from .io import MAGICCData


__version__ = get_versions()["version"]
del get_versions

# Path used for data files loading.
_magiccpath = MAGICC6().original_dir

if not _config["is_windows"]:
    wine_installed = (
        subprocess.call(
            "type wine", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        == 0
    )
    if not wine_installed:
        logging.warning("Wine is not installed")


def read_scen_file(filepath):
    """
    Read a MAGICC .SCEN file.

    Parameters
    ----------
    filepath : str
        Filepath of the .SCEN file to read

    Returns
    -------
    :obj:`pymagicc.io.MAGICCData`
        ``MAGICCData`` object containing the data and metadata.
    """
    mdata = MAGICCData()
    mdata.read(filepath)

    return mdata


rcp26 = read_scen_file(os.path.join(_magiccpath, "RCP26.SCEN"))
rcp45 = read_scen_file(os.path.join(_magiccpath, "RCP45.SCEN"))
rcp60 = read_scen_file(os.path.join(_magiccpath, "RCP60.SCEN"))
rcp85 = read_scen_file(os.path.join(_magiccpath, "RCP85.SCEN"))

scenarios = {"RCP26": rcp26, "RCP45": rcp45, "RCP60": rcp60, "RCP85": rcp85}


def run(scenario, magicc_version=6, **kwargs):
    """
    Run a MAGICC scenario and return output data and (optionally) config parameters.

    As a reminder, putting ``out_parameters=1`` will cause MAGICC to write out its
    parameters into ``out/PARAMETERS.OUT`` and they will then be read into
    ``output.metadata["parameters"]`` where ``output`` is the returned object.

    Parameters
    ----------
    scenario : :obj:`pymagicc.io.MAGICCData`
        Scenario to run

    magicc_version : int
        MAGICC version to use for the run

    **kwargs
        Parameters overwriting default parameters

    Raises
    ------
    ValueError
        If the magicc_version is not available

    Returns
    -------
    output : :obj:`pymagicc.io.MAGICCData`
        Output of the run with the data in the ``df`` attribute and parameters and
        other metadata in the ``metadata attribute``
    """
    if magicc_version == 6:
        magicc_cls = MAGICC6
    elif magicc_version == 7:
        magicc_cls = MAGICC7
    else:
        raise ValueError("MAGICC version {} is not available".format(magicc_version))

    with magicc_cls() as magicc:
        results = magicc.run(scenario=scenario, **kwargs)

    return results
