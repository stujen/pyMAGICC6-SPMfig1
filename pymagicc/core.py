import shutil
import subprocess
from os import listdir, makedirs
from os.path import basename, dirname, exists, join, isfile, abspath
from tempfile import mkdtemp

import numpy as np
import f90nml

from .config import config
from .utils import get_date_time_string
from .io import MAGICCData, NoReaderWriterError, read_cfg_file
from .definitions import (
    convert_magicc6_to_magicc7_variables,
    convert_magicc7_to_openscm_variables,
)

IS_WINDOWS = config["is_windows"]


def _copy_files(source, target):
    """
    Copy all the files in source directory to target.

    Ignores subdirectories.
    """
    source_files = listdir(source)
    if not exists(target):
        makedirs(target)
    for filename in source_files:
        full_filename = join(source, filename)
        if isfile(full_filename):
            shutil.copy(full_filename, target)


def _clean_value(v):
    if isinstance(v, str):
        return v.strip()
    elif isinstance(v, list):
        if isinstance(v[0], str):
            return [i.replace("\0", "").strip().replace("\n", "") for i in v]
    return v


class MAGICCBase(object):
    """
    Provides access to the MAGICC binary and configuration.

    To enable multiple MAGICC 'setups' to be configured independently,
    the MAGICC directory containing the input files, configuration
    and binary is copied to a new folder. The configuration in this
    MAGICC copy can then be edited without impacting other instances or your
    original MAGICC distribution.

    A ``MAGICC`` instance first has to be setup by calling
    ``create_copy``. If many model runs are being performed this step only has
    to be performed once. The ``run`` method can then be called many times
    without re-copying the files each time. Between each call to ``run``, the
    configuration files can be updated to perform runs with different
    configurations.

    Parameters
    ----------
    root_dir : str
        If ``root_dir`` is supplied, an existing MAGICC 'setup' is
        used.
    """

    version = None
    _scen_file_name = "SCENARIO.SCEN"

    def __init__(self, root_dir=None):
        self.root_dir = root_dir
        self.config = None
        self.executable = self.get_executable()

        if root_dir is not None:
            self.is_temp = False
        else:
            # Create a temp directory
            self.is_temp = True

    def __enter__(self):
        if self.is_temp and self.run_dir is None:
            self.create_copy()
        return self

    def __exit__(self, *args, **kwargs):
        self.remove_temp_copy()

    def create_copy(self):
        """
        Initialises a temporary directory structure and copy of MAGICC
        configuration files and binary.
        """
        if self.executable is None or not isfile(self.executable):
            raise FileNotFoundError(
                "Could not find MAGICC{} executable: {}".format(
                    self.version, self.executable
                )
            )
        if self.is_temp:
            assert (
                self.root_dir is None
            ), "A temp copy for this instance has already been created"
            self.root_dir = mkdtemp(prefix="pymagicc-")

        if exists(self.run_dir):
            raise Exception("A copy of MAGICC has already been created.")
        if not exists(self.root_dir):
            makedirs(self.root_dir)

        exec_dir = basename(self.original_dir)

        # Copy a subset of folders from the MAGICC `original_dir`
        # Also copy anything which is in the root of the MAGICC distribution
        # Assumes that the MAGICC binary is in a folder one level below the root
        # of the MAGICC distribution. i.e. /run/magicc.exe or /bin/magicc
        dirs_to_copy = [".", "bin", "run"]
        # Check that the executable is in a valid sub directory
        assert exec_dir in dirs_to_copy, "binary must be in bin/ or run/ directory"

        for d in dirs_to_copy:
            source_dir = abspath(join(self.original_dir, "..", d))
            if exists(source_dir):
                _copy_files(source_dir, join(self.root_dir, d))

        # Create an empty out dir
        # MAGICC assumes that the 'out' directory already exists
        makedirs(join(self.root_dir, "out"))

        # Create basic configuration files so magicc can run
        self.set_years()
        self.set_config()

    @property
    def binary_name(self):
        return basename(self.executable)

    @property
    def original_dir(self):
        return dirname(self.executable)

    @property
    def run_dir(self):
        if self.root_dir is None:
            return None
        return join(self.root_dir, "run")

    @property
    def out_dir(self):
        if self.root_dir is None:
            return None
        return join(self.root_dir, "out")

    def run(self, scenario=None, only=None, **kwargs):
        """
        Run MAGICC and parse the output.

        As a reminder, putting ``out_parameters=1`` will cause MAGICC to write out its
        parameters into ``out/PARAMETERS.OUT`` and they will then be read into
        ``output.metadata["parameters"]`` where ``output`` is the returned object.

        Parameters
        ----------
        scenario : :obj:`pymagicc.io.MAGICCData`
            Scenario to run. If None MAGICC will simply run with whatever config has
            already been set.

        only : list of str
            If not None, only extract variables in this list.

        Returns
        -------
        :obj:`pymagicc.io.MAGICCData`
            MAGICCData object containing that data in its ``df`` attribute and
            metadata and parameters (depending on the value of ``include_parameters``)
            in its ``metadata`` attribute.
        """
        if not exists(self.root_dir):
            raise FileNotFoundError(self.root_dir)

        if self.executable is None:
            raise ValueError(
                "MAGICC executable not found, try setting an environment variable `MAGICC_EXECUTABLE_{}=/path/to/binary`".format(
                    self.version
                )
            )

        if scenario is not None:
            kwargs = self.set_emission_scenario_setup(scenario, kwargs)

        yr_config = {}
        if "startyear" in kwargs:
            yr_config["startyear"] = kwargs.pop("startyear")
        if "endyear" in kwargs:
            yr_config["endyear"] = kwargs.pop("endyear")
        if yr_config:
            self.set_years(**yr_config)

        # should be able to do some other nice metadata stuff re how magicc was run
        # etc. here
        kwargs.setdefault("rundate", get_date_time_string())

        self.update_config(**kwargs)

        self.check_config()

        exec_dir = basename(self.original_dir)
        command = [join(self.root_dir, exec_dir, self.binary_name)]

        if not IS_WINDOWS and self.binary_name.endswith(".exe"):  # pragma: no cover
            command.insert(0, "wine")

        # On Windows shell=True is required.
        subprocess.check_call(command, cwd=self.run_dir, shell=IS_WINDOWS)

        outfiles = [f for f in listdir(self.out_dir) if f != "PARAMETERS.OUT"]

        mdata = MAGICCData()
        try:
            run_paras = self.read_parameters()
            self.config = run_paras
            mdata.metadata["parameters"] = run_paras
        except FileNotFoundError:
            pass

        for filepath in outfiles:
            try:
                reader = mdata.determine_tool(filepath, "reader")(filepath)
                openscm_var = convert_magicc7_to_openscm_variables(
                    convert_magicc6_to_magicc7_variables(
                        reader._get_variable_from_filepath()
                    )
                )
                if only is None or openscm_var in only:
                    mdata.append(join(self.out_dir, filepath))
            except NoReaderWriterError:
                continue

        return mdata

    def check_config(self):
        """Check that our MAGICC ``.CFG`` files are set to safely work with PYMAGICC

        For further detail about why this is required, please see :ref:`MAGICC flags`.

        Raises
        ------
        ValueError
            If we are not certain that the config written by PYMAGICC will overwrite
            all other config i.e. that there will be no unexpected behaviour. A
            ValueError will also be raised if the user tries to use more than one
            scenario file.
        """
        cfg_error_msg = (
            "PYMAGICC is not the only tuning model that will be used by "
            "`MAGCFG_USER.CFG`: your run is likely to fail/do odd things"
        )
        emisscen_error_msg = (
            "You have more than one `FILE_EMISSCEN_X` flag set. Using more than "
            "one emissions scenario is hard to debug and unnecessary with "
            "Pymagicc's dataframe scenario input. Please combine all your "
            "scenarios into one dataframe with Pymagicc and pandas, then feed "
            "this single Dataframe into Pymagicc's run API."
        )

        nml_to_check = "nml_allcfgs"
        usr_cfg = read_cfg_file(join(self.run_dir, "MAGCFG_USER.CFG"))
        for k in usr_cfg[nml_to_check]:
            if k.startswith("file_tuningmodel"):
                first_tuningmodel = k in ["file_tuningmodel", "file_tuningmodel_1"]
                if first_tuningmodel:
                    if usr_cfg[nml_to_check][k] != "PYMAGICC":
                        raise ValueError(cfg_error_msg)
                elif usr_cfg[nml_to_check][k] not in ["USER", ""]:
                    raise ValueError(cfg_error_msg)

            elif k.startswith("file_emisscen_"):
                if usr_cfg[nml_to_check][k] not in ["NONE", ""]:
                    raise ValueError(emisscen_error_msg)

    def write(self, mdata, name):
        """Write an input file to disk

        Parameters
        ----------
        mdata : :obj:`pymagicc.io.MAGICCData`
            A MAGICCData instance with the data to write

        name : str
            The name of the file to write. The file will be written to the MAGICC
            instance's run directory i.e. ``self.run_dir``
        """
        mdata.write(join(self.run_dir, name), self.version)

    def read_parameters(self):
        """
        Read a parameters.out file

        Returns
        -------
        dict
            A dictionary containing all the configuration used by MAGICC
        """
        param_fname = join(self.out_dir, "PARAMETERS.OUT")

        if not exists(param_fname):
            raise FileNotFoundError("No PARAMETERS.OUT found")

        with open(param_fname) as nml_file:
            parameters = dict(f90nml.read(nml_file))
            for group in ["nml_years", "nml_allcfgs", "nml_outputcfgs"]:
                parameters[group] = dict(parameters[group])
                for k, v in parameters[group].items():
                    parameters[group][k] = _clean_value(v)
                parameters[group.replace("nml_", "")] = parameters.pop(group)
            self.config = parameters
        return parameters

    def remove_temp_copy(self):
        """
        Removes a temporary copy of the MAGICC version shipped with Pymagicc.
        """
        if self.is_temp and self.root_dir is not None:
            shutil.rmtree(self.root_dir)
            self.root_dir = None

    def set_config(
        self, filename="MAGTUNE_PYMAGICC.CFG", top_level_key="nml_allcfgs", **kwargs
    ):
        """
        Create a configuration file for MAGICC.

        Writes a fortran namelist in run_dir.

        Parameters
        ----------
        filename : str
            Name of configuration file to write

        top_level_key : str
            Name of namelist to be written in the
            configuration file

        kwargs
            Other parameters to pass to the configuration file. No
            validation on the parameters is performed.

        Returns
        -------
        dict
            The contents of the namelist which was written to file
        """
        kwargs = self._format_config(kwargs)

        fname = join(self.run_dir, filename)
        conf = {top_level_key: kwargs}
        f90nml.write(conf, fname, force=True)

        return conf

    def update_config(
        self, filename="MAGTUNE_PYMAGICC.CFG", top_level_key="nml_allcfgs", **kwargs
    ):
        """Updates a configuration file for MAGICC

        Updates the contents of a fortran namelist in the run directory,
        creating a new namelist if none exists.

        Parameters
        ----------
        filename : str
            Name of configuration file to write

        top_level_key : str
            Name of namelist to be written in the
            configuration file

        kwargs
            Other parameters to pass to the configuration file. No
            validation on the parameters is performed.

        Returns
        -------
        dict
            The contents of the namelist which was written to file
        """
        kwargs = self._format_config(kwargs)
        fname = join(self.run_dir, filename)

        if exists(fname):
            conf = f90nml.read(fname)
        else:
            conf = {top_level_key: {}}

        conf[top_level_key].update(kwargs)
        f90nml.write(conf, fname, force=True)

        return conf

    def _format_config(self, config_dict):
        config_dict = self._fix_any_backwards_emissions_scen_key_in_config(config_dict)
        config_dict = self._convert_out_config_flags_to_integers(config_dict)

        return config_dict

    def _convert_out_config_flags_to_integers(self, config_dict):
        for key, value in config_dict.items():
            if key.startswith("out") and key != "out_ascii_binary":
                config_dict[key] = 1 if value else 0

        return config_dict

    def _fix_any_backwards_emissions_scen_key_in_config(self, config_dict):
        magicc6_emissions_scen_key = "file_emissionscenario"
        magicc7_emissions_scen_key = "file_emisscen"

        if (self.version == 6) and (magicc7_emissions_scen_key in config_dict):
            config_dict[magicc6_emissions_scen_key] = config_dict[
                magicc7_emissions_scen_key
            ]
            config_dict.pop(magicc7_emissions_scen_key)
        if (self.version == 7) and (magicc6_emissions_scen_key in config_dict):
            config_dict[magicc7_emissions_scen_key] = config_dict[
                magicc6_emissions_scen_key
            ]
            config_dict.pop(magicc6_emissions_scen_key)

        return config_dict

    def set_years(self, startyear=1765, endyear=2100):
        """
        Set the start and end dates of the simulations.

        Parameters
        ----------
        startyear : int
            Start year of the simulation

        endyear : int
            End year of the simulation

        Returns
        -------
        dict
            The contents of the namelist
        """
        # TODO: test altering stepsperyear, I think 1, 2 and 24 should all work
        return self.set_config(
            "MAGCFG_NMLYEARS.CFG",
            "nml_years",
            endyear=endyear,
            startyear=startyear,
            stepsperyear=12,
        )

    def set_output_variables(self, write_ascii=True, write_binary=False, **kwargs):
        """Set the output configuration, minimising output as much as possible

        There are a number of configuration parameters which control which variables
        are written to file and in which format. Limiting the variables that are
        written to file can greatly speed up the running of MAGICC. By default,
        calling this function without specifying any variables will disable all output
        by setting all of MAGICC's ``out_xx`` flags to ``0``.

        This convenience function should not be confused with ``set_config`` or
        ``update_config`` which allow the user to set/update the configuration flags
        directly, without the more convenient syntax and default behaviour provided by
        this function.

        Parameters
        ----------
        write_ascii : bool
            If true, MAGICC is configured to write output files as human readable ascii files.

        write_binary : bool
            If true, MAGICC is configured to write binary output files. These files are much faster
            to process and write, but are not human readable.

        **kwargs:
            List of variables to write out. A list of possible options are as follows. This
            may not be a complete list.

            'emissions',
            'gwpemissions',
            'sum_gwpemissions',
            'concentrations',
            'carboncycle',
            'forcing',
            'surfaceforcing',
            'permafrost',
            'temperature',
            'sealevel',
            'parameters',
            'misc',
            'lifetimes',
            'timeseriesmix',
            'rcpdata',
            'summaryidx',
            'inverseemis',
            'tempoceanlayers',
            'oceanarea',
            'heatuptake',
            'warnings',
            'precipinput',
            'aogcmtuning',
            'ccycletuning',
            'observationaltuning',
            'keydata_1',
            'keydata_2'
        """

        assert (
            write_ascii or write_binary
        ), "write_binary and/or write_ascii must be configured"
        if write_binary and write_ascii:
            ascii_binary = "BOTH"
        elif write_ascii:
            ascii_binary = "ASCII"
        else:
            ascii_binary = "BINARY"

        # defaults
        outconfig = {
            "out_emissions": 0,
            "out_gwpemissions": 0,
            "out_sum_gwpemissions": 0,
            "out_concentrations": 0,
            "out_carboncycle": 0,
            "out_forcing": 0,
            "out_surfaceforcing": 0,
            "out_permafrost": 0,
            "out_temperature": 0,
            "out_sealevel": 0,
            "out_parameters": 0,
            "out_misc": 0,
            "out_timeseriesmix": 0,
            "out_rcpdata": 0,
            "out_summaryidx": 0,
            "out_inverseemis": 0,
            "out_tempoceanlayers": 0,
            "out_heatuptake": 0,
            "out_ascii_binary": ascii_binary,
            "out_warnings": 0,
            "out_precipinput": 0,
            "out_aogcmtuning": 0,
            "out_ccycletuning": 0,
            "out_observationaltuning": 0,
            "out_keydata_1": 0,
            "out_keydata_2": 0,
        }
        if self.version == 7:
            outconfig["out_oceanarea"] = 0
            outconfig["out_lifetimes"] = 0

        for kw in kwargs:
            val = 1 if kwargs[kw] else 0  # convert values to 0/1 instead of booleans
            outconfig["out_" + kw.lower()] = val

        self.update_config(**outconfig)

    def get_executable(self):
        return config["executable_{}".format(self.version)]

    def diagnose_tcr_ecs(self, **kwargs):
        """Diagnose TCR and ECS

        The transient climate response (TCR), is the global-mean temperature response
        at time at which atmopsheric |CO2| concentrations double in a scenario where
        atmospheric |CO2| concentrations are increased at 1% per year from
        pre-industrial levels.

        The equilibrium climate sensitivity (ECS), is the equilibrium global-mean
        temperature response to an instantaneous doubling of atmospheric |CO2|
        concentrations.

        As MAGICC has no hysteresis in its equilibrium response to radiative forcing,
        we can diagnose TCR and ECS with one experiment. However, please note that
        sometimes the run length won't be long enough to allow MAGICC's oceans to
        fully equilibrate and hence the ECS value might not be what you expect (it
        should match the value of ``core_climatesensitivity``).

        Parameters
        ----------
        **kwargs
            parameter values to use in the diagnosis e.g. ``core_climatesensitivity=4``

        Returns
        -------
        dict
            Dictionary with keys: "ecs" - the diagnosed ECS; "tcr" - the diagnosed
            TCR; "timeseries" - the relevant model input and output timeseries used in
            the experiment i.e. atmospheric |CO2| concentrations, total radiative
            forcing and global-mean surface temperature
        """
        if self.version == 7:
            raise NotImplementedError("MAGICC7 cannot yet diagnose ECS and TCR")
        self._diagnose_tcr_ecs_config_setup(**kwargs)
        timeseries = self.run(
            scenario=None,
            only=[
                "Atmospheric Concentrations|CO2",
                "Radiative Forcing",
                "Surface Temperature",
            ]
        ).df
        tcr, ecs = self._get_tcr_ecs_from_diagnosis_results(timeseries)
        return {"tcr": tcr, "ecs": ecs, "timeseries": timeseries}

    def _diagnose_tcr_ecs_config_setup(self, **kwargs):
        self.set_years(
            startyear=1750, endyear=4200
        )  # 4200 seems to be the max I can push too without an error

        self.update_config(
            FILE_CO2_CONC="TCRECS_CO2_CONC.IN",
            RF_TOTAL_RUNMODUS="CO2",
            RF_TOTAL_CONSTANTAFTERYR=2000,
            **kwargs,
        )

    def _get_tcr_ecs_from_diagnosis_results(self, results_tcr_ecs_run):
        global_co2_concs = results_tcr_ecs_run[
            (results_tcr_ecs_run.variable == "Atmospheric Concentrations|CO2")
            & (results_tcr_ecs_run.region == "World")
        ]
        tcr_yr, ecs_yr = self._get_tcr_ecs_yr_from_CO2_concs(global_co2_concs)
        global_total_rf = results_tcr_ecs_run[
            (results_tcr_ecs_run.variable == "Radiative Forcing")
            & (results_tcr_ecs_run.region == "World")
        ]
        self._check_tcr_ecs_total_RF(global_total_rf, tcr_yr=tcr_yr, ecs_yr=ecs_yr)
        global_temp = results_tcr_ecs_run[
            (results_tcr_ecs_run.variable == "Surface Temperature")
            & (results_tcr_ecs_run.region == "World")
        ]
        self._check_tcr_ecs_temp(global_temp)
        tcr = global_temp[global_temp.time == tcr_yr].value.values[0]
        ecs = global_temp[global_temp.time == ecs_yr].value.values[0]
        return tcr, ecs

    def _get_tcr_ecs_yr_from_CO2_concs(self, df_co2_concs):
        co2_conc_0 = df_co2_concs.value.iloc[0]
        yr_start_rise = -1 + df_co2_concs[df_co2_concs.value > co2_conc_0].time.iloc[0]
        tcr_yr = yr_start_rise + 70
        spin_up_co2_concs = df_co2_concs[df_co2_concs.time < yr_start_rise].value.values
        if not (spin_up_co2_concs == co2_conc_0).all():
            raise ValueError(
                "The TCR/ECS CO2 concs look wrong, they are not constant before they start rising"
            )

        actual_rise_co2_concs = df_co2_concs[
            (df_co2_concs.time >= yr_start_rise)
            & (df_co2_concs.time <= (yr_start_rise + 70))
        ].value.values
        expected_rise_co2_concs = co2_conc_0 * 1.01 ** np.arange(71)
        rise_co2_concs_correct = np.isclose(
            actual_rise_co2_concs, expected_rise_co2_concs
        ).all()
        if not rise_co2_concs_correct:
            raise ValueError("The TCR/ECS CO2 concs look wrong during the rise period")

        co2_conc_final = max(expected_rise_co2_concs)
        eqm_co2_concs = df_co2_concs[df_co2_concs.time >= tcr_yr].value.values
        if not np.isclose(eqm_co2_concs, co2_conc_final).all():
            raise ValueError(
                "The TCR/ECS CO2 concs look wrong, they are not constant after 70 years of rising"
            )

        ecs_yr = df_co2_concs.time.iloc[-1]

        return tcr_yr, ecs_yr

    def _check_tcr_ecs_total_RF(self, df_total_rf, tcr_yr, ecs_yr):
        total_rf_values = df_total_rf.value.values
        if not (total_rf_values[df_total_rf.time <= (tcr_yr - 70)] == 0).all():
            raise ValueError(
                "The TCR/ECS total radiative forcing looks wrong, it is not all zero before concentrations start rising"
            )

        total_rf_max = total_rf_values.max()
        actual_rise_rf = total_rf_values[
            (df_total_rf.time >= (tcr_yr - 70)) & (df_total_rf.time <= tcr_yr)
        ]
        expected_rise_rf = total_rf_max / 70.0 * np.arange(71)
        rise_rf_correct = np.isclose(actual_rise_rf, expected_rise_rf).all()
        if not rise_rf_correct:
            raise ValueError(
                "The TCR/ECS total radiative forcing looks wrong during the rise period"
            )

        if not (total_rf_values[df_total_rf.time > tcr_yr] == total_rf_max).all():
            raise ValueError(
                "The TCR/ECS total radiative forcing looks wrong, it is not constant after concentrations are constant"
            )

    def _check_tcr_ecs_temp(self, df_temp):
        tmp_vls = df_temp.value.values
        tmp_minus_previous_yr = tmp_vls[1:] - tmp_vls[:-1]
        if not np.all(tmp_minus_previous_yr >= 0):
            raise ValueError(
                "The TCR/ECS surface temperature looks wrong, it decreases"
            )

    def set_emission_scenario_setup(self, scenario, config_dict):
        """Set the emissions flags correctly.

        Parameters
        ----------
        scenario : :obj:`pymagicc.io.MAGICCData`
            Scenario to run.

        config_dict : dict
            Dictionary with current input configurations which is to be validated and
            updated where necessary.

        Returns
        -------
        dict
            Updated configuration
        """
        self.write(scenario, self._scen_file_name)
        # can be lazy in this line as fix backwards key handles errors for us
        config_dict["file_emissionscenario"] = self._scen_file_name
        config_dict = self._fix_any_backwards_emissions_scen_key_in_config(config_dict)

        return config_dict


class MAGICC6(MAGICCBase):
    version = 6


class MAGICC7(MAGICCBase):
    version = 7
