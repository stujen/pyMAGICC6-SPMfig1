Pymagicc
========

+----------------+-----------------+
| |Build Status| | |AppVeyor|      |
+----------------+-----------------+
| |Codecov|      | |Launch Binder| |
+----------------+-----------------+
| |PyPI|         | |PyPI Version|  |
+----------------+-----------------+
| |JOSS|         | |Zenodo|        |
+----------------+-----------------+

.. sec-begin-index

Pymagicc is a Python wrapper around the reduced complexity climate model
`MAGICC6 <http://magicc.org/>`_. It wraps the CC-BY-NC-SA licensed
`MAGICC6 binary <http://www.magicc.org/download6>`_. Pymagicc itself is AGPL licensed.

MAGICC (Model for the Assessment of Greenhouse Gas Induced Climate Change)
is widely used in the assessment of future emissions pathways in climate policy analyses,
e.g. in the Fifth Assessment Report of the
Intergovernmental Panel on Climate Change or to model the physical aspects of climate change in Integrated Assessment Models (IAMs).

Pymagicc makes the MAGICC model easily installable and usable from Python and allows for the easy modification of all MAGICC model parameters and emissions scenarios directly from Python.
In climate research it can, for example, be used in the analysis of mitigation scenarios, in Integrated Assessment Models, complex climate model emulation, and uncertainty analyses, as well as in climate science education and communication.

See `www.magicc.org <http://www.magicc.org/>`_ and `Meinshausen et al. 2011 <https://doi.org/10.5194/acp-11-1417-2011>`_ for further information.

.. sec-end-index

Basic Usage
-----------

.. sec-begin-usage

.. code:: python

    import matplotlib.pyplot as plt

    import pymagicc
    from pymagicc import scenarios

    for name, scen in scenarios.items():
        results = pymagicc.run(scen)
        results_df = results.df
        results_df.set_index("time", inplace=True)

        global_temp_time_rows = (
            (results_df.variable == "Surface Temperature")
            & (results_df.region == "World")
        )

        temp = (
            results_df.value[global_temp_time_rows].loc[1850:]
            - results_df.value[global_temp_time_rows].loc[1850:1900].mean()
        )
        temp.plot(label=name)

    plt.legend()
    plt.title("Global Mean Temperature Projection")
    plt.ylabel("°C over pre-industrial (1850-1900 mean)");
    plt.legend(loc="best")
    # Run `plt.show()` to display the plot when running this example
    # interactively or add `%matplotlib inline` on top when in a Jupyter Notebook.


.. sec-begin-example-plot

.. image:: scripts/example-plot.png
    :align: center

.. sec-end-example-plot

For more example usage see this `Jupyter Notebook <https://github.com/openclimatedata/pymagicc/blob/master/notebooks/Example.ipynb>`_.
Thanks to the `Binder project <https://mybinder.org>`_ the `Notebook <https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?filepath=notebooks/Example.ipynb>`_ can be run and modified without installing anything locally. A small interactive `demo app <https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?urlpath=apps/notebooks/Demo.ipynb>`_ using Jupyter Notebook's `appmode extension <https://github.com/oschuett/appmode/>`_
is also available.

.. sec-end-usage
.. sec-begin-installation

Installation
------------

::

    pip install pymagicc

On Linux and OS X the original compiled Windows binary available on
`<http://www.magicc.org/>`_ and included in Pymagicc
can run using `Wine <https://www.winehq.org/>`_.

On modern 64-bit systems one needs to use the 32-bit version of Wine

::

    sudo dpkg --add-architecture i386
    sudo apt-get install wine32

On 32-bit systems Debian/Ubuntu-based systems ``wine`` can be installed with

::

    sudo apt-get install wine

On OS X ``wine`` is available in the Homebrew package manager:

::

    brew install wine

It should also be available in other package managers, as well as directly from the `Wine project <https://wiki.winehq.org/Download>`_.

Note that after the first install the first run of Pymagicc might be slow due
to setting up of the `wine` configuration and be accompanied by pop-ups or
debug output.

To run an example session using Jupyter Notebook and Python 3 you can run the
following commands to create a virtual environment ``venv`` and install an
editable version for local development:

.. code:: bash

    git clone https://github.com/openclimatedata/pymagicc.git

    cd pymagicc
    make venv
    ./venv/bin/pip install --editable .
    ./venv/bin/jupyter-notebook notebooks/Example.ipynb

.. sec-end-installation
.. sec-begin-development

Development
-----------

Setup
*****

For local development, install dependencies and an editable version of Pymagicc from a clone or download of the Pymagicc repository with

::

    make venv
    ./venv/bin/pip install --editable .

Running the tests
*****************

To run the tests run

::

    ./venv/bin/pytest tests --verbose

To skip tests which run MAGICC and take longer use

::

    ./venv/bin/pytest tests --skip-slow

To get a test coverage report, run

::

    ./venv/bin/pytest --cov

Conventions
***********

To unify coding style, allowing us to focus more on writing useful code and less time worrying about formatting, `black <https://github.com/ambv/black>`_ is used.

To format the files in ``pymagicc`` and ``tests`` as well as ``setup.py`` run

::

    make black

In our miscellaneous csv's, for example the definitional csv's, we follow the following conventions to make our lives easier:

- column names are all lower case, with underscores as separators (i.e. no spaces)

Building the documentation
**************************

The docs use Sphinx and can be rebuilt locally in ``docs/builds/html/`` with

::

    make docs

.. sec-end-development

More usage examples
-------------------

.. sec-begin-more-usage

Use an included scenario
************************

.. code:: python

    from pymagicc import rcp26

    rcp26.df.head()

Read a MAGICC scenario file
***************************

.. code:: python

    from pymagicc import read_scen_file

    scenario = read_scen_file("PATHWAY.SCEN")

Run MAGICC for a scenario
*************************

.. code:: python

    results = pymagicc.run(scenario)
    results_df = results.df
    results_df.set_index("time", inplace=True)

    global_temp_time_rows = (
        (results_df.variable == "Surface Temperature")
        & (results_df.region == "World")
    )

    temp = (
        results_df.value[global_temp_time_rows].loc[1850:]
        - results_df.value[global_temp_time_rows].loc[1850:1900].mean()
    )

Using a different MAGICC version
********************************

A custom version of MAGICC may be used with ``pymagicc`` using the
``MAGICC_EXECUTABLE_6`` and ``MAGICC_EXECUTABLE_7`` environment variables for MAGICC6
and MAGICC7 respectively. These environment variables should be set to the
location of the magicc executable (either ``magicc`` for linux/mac or
``magicc.exe`` for Windows).
For example, a custom MAGICC7 folder located at ``/tmp/magicc`` can be used on
under Linux by setting ``MAGICC_EXECUTABLE_7`` to ``/tmp/magicc/run/magicc``.

Example usage in Bash:

.. code:: bash

    MAGICC_EXECUTABLE_7=/tmp/magicc/run/magicc.exe make test

Or in a script:

.. code:: bash

    #!/bin/bash
    export MAGICC_EXECUTABLE_7=tmp/magicc/run/magicc.exe
    make test

.. sec-end-more-usage

Contributing
------------

.. sec-begin-contributing

Please report issues or discuss feature requests on Pymagicc's
`issue tracker <https://github.com/openclimatedata/pymagicc/issues>`_.

You can also contact the `pymagicc` authors via email:
`<mailto:robert.gieseke@pik-potsdam.de, zebedee.nicholls@climate-energy-college.org>`_

.. sec-end-contributing

.. sec-begin-license
License
-------


The `compiled MAGICC binary <http://www.magicc.org/download6>`_ by Tom Wigley,
Sarah Raper, and Malte Meinshausen included in this package is licensed under a `Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License <https://creativecommons.org/licenses/by-nc-sa/3.0/>`_.

See also the `MAGICC website <http://magicc.org/>`_ and
`Wiki <http://wiki.magicc.org/index.php?title=Main_Page>`_
for further information.

The ``pymagicc`` wrapper is free software under the GNU Affero General Public
License v3, see `LICENSE <./LICENSE>`_.

Citation
--------

If you make any use of MAGICC, its license requires citing of:

    M. Meinshausen, S. C. B. Raper and T. M. L. Wigley (2011). "Emulating coupled
    atmosphere-ocean and carbon cycle models with a simpler model, MAGICC6: Part I
    "Model Description and Calibration." Atmospheric Chemistry and Physics 11: 1417-1456.
    `https://doi.org/10.5194/acp-11-1417-2011 <https://dx.doi.org/10.5194/acp-11-1417-2011>`_

If you use Pymagicc in your research, please additionally cite

    R. Gieseke, S. N. Willner and M. Mengel, (2018). Pymagicc: A Python wrapper
    for the simple climate model MAGICC. Journal of Open Source Software, 3(22),
    516, `https://doi.org/10.21105/joss.00516 <https://doi.org/10.21105/joss.00516>`_

For proper reproducibility please reference the version of Pymagicc used. In
Python it can be printed with

.. code:: python

    import pymagicc
    print(pymagicc.__version__)


Pymagicc releases are archived at Zenodo and the version used should also be cited.

See https://doi.org/10.5281/zenodo.1111815

.. sec-end-license

.. |Build Status| image:: https://travis-ci.org/openclimatedata/pymagicc.svg?branch=master
    :target: https://travis-ci.org/openclimatedata/pymagicc
.. |AppVeyor| image:: https://img.shields.io/appveyor/ci/openclimatedata/pymagicc/master.svg
    :target: https://ci.appveyor.com/project/openclimatedata/pymagicc
.. |Codecov| image:: https://img.shields.io/codecov/c/github/openclimatedata/pymagicc.svg
    :target: https://codecov.io/gh/openclimatedata/pymagicc
.. |Launch Binder| image:: https://img.shields.io/badge/launch-binder-e66581.svg
    :target: https://mybinder.org/v2/gh/openclimatedata/pymagicc/master?filepath=notebooks/Example.ipynb
.. |PyPI| image:: https://img.shields.io/pypi/pyversions/pymagicc.svg
    :target: https://pypi.org/project/pymagicc/
.. |PyPI Version| image:: https://img.shields.io/pypi/v/pymagicc.svg
    :target: https://pypi.org/project/pymagicc/
.. |JOSS| image:: https://joss.theoj.org/papers/85eb9a9401fe968073bb429ea361924e/status.svg
    :target: https://joss.theoj.org/papers/85eb9a9401fe968073bb429ea361924e
.. |Zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.1111815.svg
    :target: https://zenodo.org/record/1111815

