Project configuration
===========

**dp** as a tool depends on a few files in your project directory. It must be able to find a ``config`` directory with
a structure looking similar to this:

| config
| ├── base
| │   ├── dbt.yml
| │   ├── bigquery.ymldbt2
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

dbt configuration
++++++++++++++++++++++++++++++

The main configuration is in ``config/<ENV>/dbt.yml`` file. At the moment it allows setting two values:
* ``target`` - should be set either to ``local`` or ``env_execution`` depending on where the tool is used. Local means
running locally while ``env_execution`` means executing by the scheduler on the dev or prod environment.
* ``target_type`` - defines which backend **dbt** will use and what file **dp** will search for additional configuration
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
``dp.yml.jinja`` template and make **copier** ask for those when initializing **dp**. By doing so, each member of your
organization will end up with a list of user-specific variables reusable across different projects on its machine.
Just remember, **global-scoped variables take precedence over project-scoped ones.**

Airflow configuration
++++++++++++++++++++++++++++++

Airflow-related configuration is stored in ``config/<ENV>/airflow.yml`` file and is strongly connected to the Airflow plugin: ``dbt-airflow-factory``
More information about this configuration can be found `here <https://dbt-airflow-factory.readthedocs.io/en/latest/configuration.html#airflow-yml-file>`_

One important config from **dp** tool in this file is ``dags_path``. It sets the URL to blob storage that is responsible for
storing projects DAGs with other artifacts.

Execution environment configuration
++++++++++++++++++++++++++++++

All configuration about how **dbt** is executed on the Airflow side is kept in execution_env.yml and <env type>.yml. More
information about these settings can be found `here <https://dbt-airflow-factory.readthedocs.io/en/latest/configuration.html#execution-env-yml-file>`_

Publication configuration
++++++++++++++++++++++++++++++

``config/<ENV>/publish.yml`` file contains configuration about creating **dbt** packages for downstream projects and
publishing it to a git repository as a package registry.

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

**dp** can sends **dbt** metadata to DataHub. All related configuration is stored in ``config/<ENV>/datahub.yml`` file.
More information about it can be found `here <https://datahubproject.io/docs/metadata-ingestion#recipes>`_ and `here <https://datahubproject.io/docs/generated/ingestion/sources/dbt>`_.

Data ingestion configuration
++++++++++++++++++++++++++++++

Ingestion configuration is divided into two levels:

- General: ``config/<ENV>/ingestion.yml``
- Ingestion tool related: e.g. ``config/<ENV>/airbyte.yml``

``config/<ENV>/ingestion.yml`` contains basic configuration of ingestion:

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - enable
     - bool
     - Flag for enable/disable ingestion option in **dp**.
   * - engine
     - enum string
     - Ingestion tool you would like to integrate with (currently the only supported value is ``airbyte``).

``config/<ENV>/airbyte.yml`` must be present if engine of your choice is ``airbyte``. It consists of two parts:

1. First part is required by `dbt-airflow-factory <https://github.com/getindata/dbt-airflow-factory>`_
   and must be present in order to create ingestion tasks preceding dbt rebuild in Airflow. When you choose to manage
   Airbyte connections with `dp` tool, ``connectionId`` is unknown at the time of coding however `dp` tool is ready to
   handle this case. For detailed info reference example ``airbyte.yml`` at the end of this section.

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - airbyte_connection_id
     - string
     - Name of Airbyte connection in Airflow
   * - tasks
     - array<*task*>
     - Configurations of Airflow tasks used by `dbt-airflow-factory <https://github.com/getindata/dbt-airflow-factory>`_.
       Allowed *task* options are documented `here <https://dbt-airflow-factory.readthedocs.io/en/latest/configuration.html#id3>`_.

2. Second part is used directly by `dp` tool to manage (insert or update) connections in Airbyte. It is **not** required
   unless you would like to manage Airbyte connections with `dp` tool.

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - airbyte_url
     - string
     - Https address of Airbyte deployment that allows to connect to Airbyte API
   * - workspace_id
     - uuid
     - Optional ID of the workspace that contains connections defined in the config. If not provided, it will be automatically fetched from Airbyte API.
   * - connections
     - array<*connection*>
     - Configurations of Airbyte connections that should be upserted during CI/CD. Minimal connection schema is documented below.
       These configurations are passed directly to Airbyte API to the `connections/create` or `connections/update` endpoint.
       Please reference
       `Airbyte API reference <https://airbyte-public-api-docs.s3.us-east-2.amazonaws.com/rapidoc-api-docs.html#post-/v1/connections/create>`_
       for more detailed configuration.

.. code-block:: text

  YOUR_CONNECTION_NAME: string
    name: string                              Optional name of the connection
    sourceId: uuid                            UUID of Airbyte source used for this connection
    destinationId: uuid                       UUID of Airbyte destination used for this connection
    namespaceDefinition: enum                 Method used for computing final namespace in destination
    namespaceFormat: string                   Used when namespaceDefinition is 'customformat'
    status: enum                              `active` means that data is flowing through the connection. `inactive` means it is not
    syncCatalog: object                       Describes the available schema (catalog).
      streams: array
      - stream: object
          name: string                        Stream's name
          jsonSchema: object                  Stream schema using Json Schema specs.
        config:
          syncMode: enum                      Allowed: full_refresh | incremental
          destinationSyncMode: enum           Allowed: append | overwrite | append_dedup
          aliasName: string                   Alias name to the stream to be used in the destination

Example ``airbyte.yml`` might look like the following. Notice (highlighted lines) how connection name in ``connections``
array has the same name as the environmental variable in `task[0].connection_id` attribute. During CI/CD, after the
connection creation in Airbyte, variable ``${POSTGRES_BQ_CONNECTION}`` is substituted by the received Airbyte
connection UUID and passed in config to dbt-airflow-factory tool.

.. code-block:: yaml
   :linenos:
   :emphasize-lines: 6,13

   # dbt-airflow-factory configuration properties:
   airbyte_connection_id: airbyte_connection_id
   tasks:
     - api_version: v1
       asyncronous: false
       connection_id: ${POSTGRES_BQ_CONNECTION}
       task_id: postgres_bq_connection_sync_task
       timeout: 600
       wait_seconds: 3
   # Airbyte connection managing properties:
   airbyte_url: https://airbyte-dev.company.com
   connections:
     POSTGRES_BQ_CONNECTION:
       name: postgres_bq_connection
       sourceId: c3aa49f0-90dd-4c8e-9641-505a2f6cb65c
       destinationId: 3f47dbf1-11f3-41b0-945f-9463c82f711b
       namespaceDefinition: customformat
       namespaceFormat: ingestion_pg
       status: active
       syncCatalog:
         streams:
          - stream:
              name: raw_orders
              jsonSchema:
                properties:
                  id:
                    airbyte_type: integer
                    type: number
                  order_date:
                    format: date
                    type: string
                  status:
                    type: string
                  user_id:
                    airbyte_type: integer
                    type: number
                type: object
            config:
              syncMode: full_refresh
              destinationSyncMode: append
              aliasName: raw_orders

Business Intelligence configuration
++++++++++++++++++++++++++++++

BI configuration is divided into two levels:

- General: ``config/<ENV>/bi.yml`` file
- BI tool related: e.g. ``config/<ENV>/looker.yml``

``config/<ENV>/bi.yml`` contains basic configuration about BI integration:

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - is_bi_enabled
     - bool
     - Flag for enable/disable BI option in **dp**.
   * - bi_target
     - string
     - BI tool you want to working with (currently only Looker is supported).
   * - is_bi_compile
     - bool
     - Whether generate BI code in compile phase?
   * - is_bi_deploy
     - bool
     - Whether deploy and push BI codes?

``config/<ENV>/looker.yml`` contains more detailed configuration related to BI tool:

.. list-table::
   :widths: 25 20 55
   :header-rows: 1

   * - Parameter
     - Data type
     - Description
   * - looker_repository
     - string
     - Git repository used by Looker project you want to integrate.
   * - looker_repository_username
     - string
     - Git config - username for operating with repository
   * - looker_repository_email
     - string
     - Git config - user email for operating with repository
   * - looker_project_id
     - string
     - Looker's project ID
   * - looker_webhook_secret
     - string
     - Looker's project webhook secret for deployment
   * - looker_repository_branch
     - string
     - Looker's repository branch for deploy new codes
   * - looker_instance_url
     - string
     - URL for you Looker instance

Example ``looker.yml`` file might look like this:

.. code-block:: yaml
   :linenos:

   looker_repository: git@gitlab.com:company/looker/pipeline-example-looker.git
   looker_repository_username: "{{ env_var('LOOKER_REPO_USERNAME') }}"
   looker_repository_email: name-surname@company.com
   looker_project_id: my_looker_project
   looker_webhook_secret: "{{ env_var('LOOKER_WEBHOOK_SECRET') }}"
   looker_repository_branch: main
   looker_instance_url: https://looker.company.com/