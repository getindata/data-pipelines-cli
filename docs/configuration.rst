Project configuration
===========

**dp** as a tool depends on a few files in your project directory. It must be able to find a ``config`` directory with
a structure looking similar to this:

| config
| ├── base
| │   ├── dbt.yml
| │   ├── bigquery.yml
| │   └── ...
| ├── dev
| │   └── bigquery.yml
| │── local
| │   ├── dbt.yml
| │   └── bigquery.yml
| └── prod
|     └── bigquery.yml
|

Whenever you call **dp**'s command with the ``--env <ENV>`` flag, the tool will search for ``dbt.yml`` and
``<TARGET_TYPE>.yml`` files in ``base`` and ``<ENV>`` directory and parse important info out of them, with ``<ENV>``
settings taking precedence over those listed in ``base``. So, for example, for the following files:

.. code-block:: yaml

 # config/base/dbt.yml
 target: env_execution
 target_type: bigquery

 # config/base/bigquery.yml
 method: oauth
 project: my-gcp-project
 dataset: my-dataset
 threads: 1

 # cat config/dev/bigquery.yml
 dataset: dev-dataset

``dp test --env dev`` will run ``dp test`` command using values from those files, most notably with ``dataset: dev-dataset`` overwriting
``dataset: my-dataset`` setting.

**dp** synthesizes dbt's ``profiles.yml`` out of those settings among other things. However, right now it only creates
``local`` or ``env_execution`` profile, so if you want to use different settings amongst different environments, you
should rather use ``{{ env_var('VARIABLE') }}`` as a value and provide those settings as environment variables. E.g., by
setting those in your ``config/<ENV>/k8s.yml`` file, in ``envs`` dictionary:

.. code-block:: yaml

 # config/base/bigquery.yml
 method: oauth
 dataset: "{{ env_var('GCP_DATASET') }}"
 project: my-gcp-project
 threads: 1

 # config/base/execution_env.yml
 # ... General config for execution env ...

 # config/base/k8s.yml
 # ... Kubernetes settings ...

 # config/dev/k8s.yml
 envs:
   GCP_DATASET: dev-dataset

 # config/prod/k8s.yml
 envs:
    GCP_DATASET: prod-dataset

DBT configuration
++++++++++++++++++++++++++++++

The main configuration is in ``config/<ENV>/dbt.yml`` file. At the moment it allows setting two values:
* ``target`` - should be set either to ``local`` or ``env_execution`` depending on where the tool is used. Local means
running locally while ``env_execution`` means executing by the scheduler on the dev or prod environment.
* ``target_type`` - defines which backend DBT will use and what file **dp** will search for additional configuration
(example: ``bigquery`` or ``snowflake``).

Additionally, the backend configuration file should be provided with a name depending on the selected ``target_type``
(<target_type>.yml). For example setting ``target_type`` to ``bigquery`` **dp** will look for bigquery.yml files.
This file should consist of all configurations that will be used to build profile.yml. Example files for the production
environment:

.. code-block:: yaml

   method: service-account
   keyfile: "{{ env_var('GCP_KEY_PATH') }}"
   project: gid-dataops-labs
   dataset: presentation
   threads: 1
   timeout_seconds: 300
   priority: interactive
   location: europe-central2
   retries: 1

Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can put a dictionary of variables to be passed to ``dbt`` in your ``config/<ENV>/dbt.yml`` file, following the convention
presented in `the guide at the dbt site <https://docs.getdbt.com/docs/building-a-dbt-project/building-models/using-variables#defining-variables-in-dbt_projectyml>`_.
E.g., if one of the fields of ``config/<SNOWFLAKE_ENV>/snowflake.yml`` looks like this:

.. code-block:: yaml

 schema: "{{ var('snowflake_schema') }}"

you should put the following in your ``config/<SNOWFLAKE_ENV>/dbt.yml`` file:

.. code-block:: yaml

 vars:
   snowflake_schema: EXAMPLE_SCHEMA

and then run your ``dp run --env <SNOWFLAKE_ENV>`` (or any similar command).

You can also add "global" variables to your **dp** config file ``$HOME/.dp.yml``. Be aware, however, that those variables
get erased on every ``dp init`` call. It is a great idea to put *commonly used* variables in your organization's
``dp.yml.tmpl`` template and make **copier** ask for those when initializing **dp**. By doing so, each member of your
organization will end up with a list of user-specific variables reusable across different projects on its machine.
Just remember, **global-scoped variables take precedence over project-scoped ones.**

Airflow configuration
++++++++++++++++++++++++++++++

Airflow-related configuration is stored in ``config/<ENV>/airflow.yml`` file and is strongly connected to the Airflow plugin: ``dbt-airflow-factory``
More information about this configuration can be found here: https://dbt-airflow-factory.readthedocs.io/en/latest/configuration.html#airflow-yml-file

One important config from **dp** tool in this file is ``dags_path``. It sets the URL to blob storage that is responsible for
storing projects DAGs with other artifacts.

Execution environment configuration
++++++++++++++++++++++++++++++

All configuration about how DBT is executed on the Airflow side is kept in execution_env.yml and <env type>.yml. More
information about these settings can be found here: https://dbt-airflow-factory.readthedocs.io/en/latest/configuration.html#execution-env-yml-file

Publication configuration
++++++++++++++++++++++++++++++

``config/<ENV>/publish.yml`` file contains configuration about creating DBT packages for downstream projects and
publishing it to a git repository as a package registry.


TODO:
.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - repository
     - string
     - HTTPS link to repo that works as packages repository.
   * - branch
     - string
     - Branch of the selected repository where packages are published.
   * - username
     - string
     - User name that will be presented as package publisher in GIT.
   * - email
     - string
     - Email of the package publisher.

Data governance configuration
++++++++++++++++++++++++++++++

**dp** can sends DBT metadata to DataHub. All related configuration is stored in ``config/<ENV>/datahub.yml`` file.
More information about it can be found here: https://datahubproject.io/docs/metadata-ingestion#recipes
and https://datahubproject.io/docs/generated/ingestion/sources/dbt

