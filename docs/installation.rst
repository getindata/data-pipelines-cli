Installation
------------
Use the package manager `pip <https://pip.pypa.io/en/stable/>`_ to
install `data-pipelines-cli <https://pypi.org/project/data-pipelines-cli/>`_:


.. code-block:: bash

 pip install data-pipelines-cli[<flags>]

Depending on the systems that you want to integrate with you need to provide different flags in square brackets. You can provide comma separate list of flags, for example:

.. code-block:: bash

 pip install data-pipelines-cli[gcs,git,bigquery]


Depending on the data storage you have you can use:

* bigquery
* snowflake
* redshift
* postgres

If you need git integration for loading packages published by other projects or publish them by yourself you will need:

* git

If you want to deploy created artifacts (docker images and DataHub metadata) add the following flags:

* docker
* datahub

These are not usually used by a person user.

If you need Business Intelligence integration you can use following options:

* looker
