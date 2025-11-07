Installation
------------

Use the package manager `pip <https://pip.pypa.io/en/stable/>`_ to
install `data-pipelines-cli <https://pypi.org/project/data-pipelines-cli/>`_ (requires Python 3.9-3.12).

You need to provide different flags in square brackets depending on the systems you want to integrate with. You can provide comma separated list of flags.

Required Flags
~~~~~~~~~~~~~~

**A dbt adapter must be installed** (provides ``dbt-core`` as transitive dependency). Depending on the data storage you have you can use:

* ``bigquery`` - Google BigQuery
* ``snowflake`` - Snowflake
* ``redshift`` - Amazon Redshift
* ``postgres`` - PostgreSQL
* ``databricks`` - Databricks

Example:

.. code-block:: bash

 pip install data-pipelines-cli[bigquery]

To pin a specific ``dbt-core`` version:

.. code-block:: bash

 pip install data-pipelines-cli[snowflake] 'dbt-core>=1.8.0,<1.9.0'

Optional Flags
~~~~~~~~~~~~~~

If you need git integration for loading packages published by other projects or publish them by yourself:

* ``git``

If you want to deploy created artifacts (docker images and DataHub metadata) add the following flags (these are not usually used by a person user):

* ``docker``
* ``datahub``

If you need Business Intelligence integration:

* ``looker``

For cloud storage deployment:

* ``gcs`` - Google Cloud Storage
* ``s3`` - AWS S3

Example with Multiple Flags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

 pip install data-pipelines-cli[bigquery,docker,datahub,gcs]

Troubleshooting
~~~~~~~~~~~~~~~

**Pre-release dbt versions**: data-pipelines-cli requires stable dbt-core releases. If you encounter errors with beta or RC versions, reinstall with stable versions:

.. code-block:: bash

 pip install --force-reinstall 'dbt-core>=1.7.3,<2.0.0'
