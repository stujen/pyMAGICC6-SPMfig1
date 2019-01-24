Changelog
=========

master
------

- (`#190 <https://github.com/openclimatedata/pymagicc/pull/190>`_) Speed up diagnosis of TCR and ECS by removing writing of scenario file
- (`#191 <https://github.com/openclimatedata/pymagicc/pull/191>`_) Fixed bugs which meant config passed to MAGICC wasn't handled correctly and renamed `tests/test_api.py` to `tests/test_core.py`.
- (`#187 <https://github.com/openclimatedata/pymagicc/pull/187>`_) Added `pymagicc.io.join_timeseries` which simplifies joining/merging scenarios to create custom scenarios
- (`#185 <https://github.com/openclimatedata/pymagicc/pull/185>`_) Added ability to read RCP files from http://www.pik-potsdam.de/~mmalte/rcps/ as requested in `#176 <https://github.com/openclimatedata/pymagicc/issues/176>`_
- (`#184 <https://github.com/openclimatedata/pymagicc/pull/184>`_) Remove redundant mapping of region names for SCEN to SCEN7 conversions
- (`#183 <https://github.com/openclimatedata/pymagicc/pull/183>`_) Added ability to read MHALO files (see `#182 <https://github.com/openclimatedata/pymagicc/issues/182>`_)
- (`#180 <https://github.com/openclimatedata/pymagicc/pull/180>`_) Added reference which explains MAGICC's variables to docs
- (`#177 <https://github.com/openclimatedata/pymagicc/pull/177>`_) Fixed SCEN reading bug, can now read SCEN files with "YEAR" in first column rather than "YEARS"
- (`#170 <https://github.com/openclimatedata/pymagicc/pull/170>`_) Added pyam as a dependency and gave an example of how to integrate with it
- (`#173 <https://github.com/openclimatedata/pymagicc/pull/173>`_) Renamed
  ``pymagicc.api`` to ``pymagicc.core``
- (`#168 <https://github.com/openclimatedata/pymagicc/pull/168>`_) Added MAGICC7 compatibility
- (`#165 <https://github.com/openclimatedata/pymagicc/pull/165>`_) Moved to one unified backend for all run functionality. This one got a bit out of hand so also includes:
  - Breaking the API, hence requiring significantly re-writing the tests to match the new API, bumping the major version number and updating the examples.
  - Locking up Pymagicc so that it will only run if MAGICC's ``.CFG`` files are configured in the simplest way possible (see :ref:`MAGICC flags`). This required re-writing the ``pymagicc/MAGICC6/run/MAGCFG_USER.CFG`` file that ships with Pymagicc (although the result is the same, as confirmed by the fact that the outputs of the four RCPs are unchanged in ``tests/test_pymagicc.py``).
  - Adding a function to pull a single configuration file from a MAGICC ``PARAMETERS.OUT`` file to aid the transition to the change referred to above (i.e. one could run MAGICC with whatever config elsewhere and then get a single config file which can be used with Pymagicc from the resulting ``PARAMETERS.OUT`` file).
  - Tidying up the docs to make linking a bit simpler and more reusable.
  - Only passing ``filepath`` (i.e. the combination of path and name) to reading/writing functions to remove ambiguity in previous language which used ``file``, ``filepath``, ``path``, ``name`` and ``filename``, sometimes in a self-contradictory way.
- (`#167 <https://github.com/openclimatedata/pymagicc/pull/167>`_) Updated release instructions
- (`#162 <https://github.com/openclimatedata/pymagicc/pull/162>`_) Added basic tests of integration with MAGICC binaries
- (`#163 <https://github.com/openclimatedata/pymagicc/pull/163>`_) Confirmed HFC-245fa misnaming in MAGICC6. Accordingly, we:
  - fixed this naming in the SRES scenarios
  - removed ``pymagicc/MAGICC6/run/HISTRCP_HFC245ca_CONC.IN`` to avoid repeating this confusion
  - ensured that anyone who finds a file with "HFC-245ca" in it in future will get a warning, see ``tests/test_definitions.py``
- (`#164 <https://github.com/openclimatedata/pymagicc/pull/164>`_) Improved missing MAGICC binary message in tests as discussed in `#124 <https://github.com/openclimatedata/pymagicc/issues/124>`_
- (`#154 <https://github.com/openclimatedata/pymagicc/pull/154>`_) Change to using OpenSCM variables for all user facing data as well as preparing to move to using OpenSCM dataframes
  - Note that this change breaks previously considered direct access but that we will gain a lot of features once we start using the capabilities of pyam as part of an OpenSCM dataframe
- (`#160 <https://github.com/openclimatedata/pymagicc/pull/159>`_) Made notebooks CI more opinionated (`#158 <https://github.com/openclimatedata/pymagicc/issues/158>`_)
- (`#139 <https://github.com/openclimatedata/pymagicc/pull/139>`_) Added the ability to read all MAGICC output files/throw an explanatory error with ``pymagicc.io.MAGICCData``
- (`#135 <https://github.com/openclimatedata/pymagicc/pull/135>`_) Moved emissions definitions to a single csv and packaged all of the definitions files using the `data package standard <https://frictionlessdata.io/docs/creating-tabular-data-packages-in-python/>`_
- (`#79 <https://github.com/openclimatedata/pymagicc/pull/79>`_) Confirmed that keeping track of config state works and added example to TCR/ECS diagnosis notebook
- (`#146 <https://github.com/openclimatedata/pymagicc/pull/146>`_) Removed path alteration from docs buiding
- (`#143 <https://github.com/openclimatedata/pymagicc/pull/143>`_) Only read ``PARAMETERS.OUT`` file if it exists. ``MAGICCBase.config`` now defaults to ``None`` until a valid ``PARAMETERS.OUT`` file is read.
- (`#133 <https://github.com/openclimatedata/pymagicc/pull/133>`_) Put definitions of MAGICC6's expected emissions into a standalone module
- (`#102 <https://github.com/openclimatedata/pymagicc/pull/102>`_) Added ability to read and write SCEN7 files
- (`#108 <https://github.com/openclimatedata/pymagicc/pull/108>`_) Added ability to read all files in MAGICC6 run folder (``pymagicc/MAGICC6/run``) to a common format
    - Note that this change means that only files which follow the MAGICC6 or MAGICC7 naming convention are supported. These are very similar to MAGICC5 except that emissions files must be named in the form ``*.SCEN``, ``*.SCEN7`` or ``*EMISX.IN`` where ``X`` is ``I`` if the file contains fossil and industrial emissions and ``B`` if the file contains agriculture, land-use and land-use change emissions. The suffixes ``FOSSIL&IND`` and ``LANDUSE`` are no longer supported.
    - The renamed files are
        - ``pymagicc/MAGICC6/run/EDGAR_NOX_EMIS_LANDUSE.IN`` => ``pymagicc/MAGICC6/run/EDGAR_NOXB_EMIS.IN``
        - ``pymagicc/MAGICC6/run/EDGAR_NOX_EMIS_FOSSIL&IND.IN`` => ``pymagicc/MAGICC6/run/EDGAR_NOXI_EMIS.IN``
        - ``pymagicc/MAGICC6/run/HOUGHTON_CO2_EMIS_LANDUSE.IN`` => ``pymagicc/MAGICC6/run/HOUGHTON_CO2B_EMIS.IN``
        - ``pymagicc/MAGICC6/run/MARLAND_CO2_EMIS_FOSSIL&IND.IN`` => ``pymagicc/MAGICC6/run/MARLAND_CO2I_EMIS.IN``
    - Deleted ``pymagicc/MAGICC6/run/HIST_SEALEVEL_CHURCHWHITE2006_RF.IN`` as it's empty
    - Added ``scripts/check_run_dir_file_read.py`` so we can quickly check which files in a MAGICC ``run`` directory can be read by ``pymagicc``
    - Added new section to docs, ``docs/file_conventions.rst`` which will document all of the relevant information related to MAGICC's file conventions

1.3.2
-----

- add short-term solution for reading Carbon Cycle output
- add clear error if a valid executable is not configured/found
- remove ``_magiccbinary`` variable
- partial steps towards updated input/output, still not fully tested
- add examples of file input/writing in notebook
- add expectexception so that we can show errors in notebooks with
  sensible CI

1.3.1
-----

- add TCR diagnosis function
- improve testing of notebooks
- add documentation using MkDocs
- use Black for automatic code formatting
- add Python 3.7 testing

1.2.0
-----

- drop support for Python 2
- rename RCP3PD to RCP26 and RCP6 to RCP60 for consistency and MAGICC7
  compatibility
- introduce new API functions for setting up and running MAGICC
- introduce ``config`` module
- remove ``output_dir`` from ``run`` function, this can be achieved using the new API
- change directory structure of the MAGICC version shipped with Pymagicc
  to be more similar to MAGICC7's structure
- add ``--skip-slow`` option to tests

1.1.0
-----

- add reading of MAGICC_EXECUTABLE environment variable to simplify
  setting path of MAGICC package for testing and CI
  (thanks ``@lewisjared``)

1.0.2
-----

- interactive demo Notebook using Jupyter Notebook's appmode
  extension
- documentation improvements

1.0.1
-----

- Un-pin f90nml dependency, 0.23 is working with Pymagicc again

1.0.0
-----

- API Stable release

0.9.3
-----

- workaround for bug in Pandas
  (`<https://github.com/pandas-dev/pandas/issues/18692>`_) when reading
  some files from alternative MAGICC builds
- improve documentation

0.9.2
-----

- add Windows testing and fix running on Windows
- simplify configuration by only having optional config parameters

0.8.0
-----

- pin f90nml version because later release breaks with MAGICC output

0.7.0
-----

- switch to Dictionaries as results object and scenarios data
  structure since Pandas panel is being deprecated.

0.6.4
-----

- returning used parameters in MAGICC ``run`` function is optional
- fix versioning for PyPI installs

0.4
---

Initial release.
