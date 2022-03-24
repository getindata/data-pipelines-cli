Usage
=====

First, create a repository with a global configuration file that you or your organization will be using. The repository
should contain ``dp.yml.tmpl`` file looking similar to this:

.. code-block:: yaml

 templates:
   my-first-template:
     template_name: my-first-template
     template_path: https://github.com/<YOUR_USERNAME>/<YOUR_TEMPLATE>.git
 vars:
   username: YOUR_USERNAME

Thanks to the `copier <https://copier.readthedocs.io/en/stable/>`_, you can leverage Jinja template syntax to create
easily modifiable configuration templates. Just create a ``copier.yml`` file next to the ``dp.yml.tmpl`` one and configure
the template questions (read more at `copier documentation <https://copier.readthedocs.io/en/stable/configuring/>`_).

Then, run ``dp init <CONFIG_REPOSITORY_URL>`` to initialize **dp**. You can also drop ``<CONFIG_REPOSITORY_URL>`` argument,
**dp** will get initialized with an empty config.

Project creation
----------------

You can use ``dp create <NEW_PROJECT_PATH>`` to choose one of the templates added before and create the project in the
``<NEW_PROJECT_PATH>`` directory.

You can also use ``dp create <NEW_PROJECT_PATH> <LINK_TO_TEMPLATE_REPOSITORY>`` to point directly to a template
repository. If ``<LINK_TO_TEMPLATE_REPOSITORY>`` proves to be the name of the template defined in **dp**'s config file,
``dp create`` will choose the template by the name instead of trying to download the repository.

``dp template-list`` lists all added templates.

Project update
--------------

To update your pipeline project use ``dp update <PIPELINE_PROJECT-PATH>``. It will sync your existing project with updated
template version selected by ``--vcs-ref`` option (default ``HEAD``).

Project configuration
---------------------

**dp** as a tool depends on a few files in your project directory. In your project directory, it must be able to find a
``config`` directory with a structure looking similar to this:

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

``target`` and ``target_type``
++++++++++++++++++++++++++++++

* ``target`` setting in ``config/<ENV>/dbt.yml`` should be set either to ``local`` or ``env_execution``;
* ``target_type`` defines which backend dbt will use and what file **dp** will search for; example ``target_types`` are ``bigquery`` or ``snowflake``.

Variables
+++++++++

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

dbt sources and models creation
-------------------------------

With the help of `dbt-codegen <https://hub.getdbt.com/dbt-labs/codegen/>`_ and
`dbt-profiler <https://hub.getdbt.com/data-mie/dbt_profiler/>`_, one can easily generate ``source.yml``, source's base
model SQLs, and model-related YAMLs. **dp** offers a convenient CLI wrapper around those functionalities.

First, add the **dbt-codegen** package to your ``packages.yml`` file:

.. code-block:: yaml

 packages:
   - package: dbt-codegen
     version: 0.5.0  # or newer

Then, run ``dp generate source-yaml YOUR_DATASET_NAME`` to generate ``source.yml`` file in ``models/source`` directory.
You can list more than one dataset, divided by space. After that, you are free to modify this file.

When you want to generate SQLs for your sources, run ``dp generate source-sql``. It will save those SQLs in the directory
``models/staging/YOUR_DATASET_NAME``.

Finally, when you have all your models prepared (in the form of SQLs), run ``dp generate model-yaml MODELS_DIR`` to
generate YAML files describing them (once again, you are not only free to modify them but also encouraged to do so!).
E.g., given such a directory structure:

| models
| ├── staging
| │   └── my_source
| │       ├── stg_table1.sql
| │       └── stg_table2.sql
| ├── intermediate
| │   ├── intermediate1.sql
| │   ├── intermediate2.sql
| │   └── intermediate3.sql
| └── presentation
|     └── presentation1.sql
|

``dp generate model-yaml models/`` will create ``models/staging/my_source/my_source.yml``,
``models/staging/intermediate/intermediate.yml``, and ``models/presentation/presentation.yml``. Beware, however, this
command WILL NOT WORK if you do not have those models created in your data warehouse already. So remember to run
``dp run`` (or a similar command) beforehand.

If you add the **dbt-profiler** package to your ``packages.yml`` file too, you can call
``dp generate model-yaml --with-meta MODELS_DIR``. **dbt-profiler** will add a lot of profiling metadata to
descriptions of your models.

Project compilation
-------------------

``dp compile`` prepares your project to be run on your local machine and/or deployed on a remote one.

Local run
---------

When you get your project configured, you can run ``dp run`` and ``dp test`` commands.

* ``dp run`` runs the project on your local machine,
* ``dp test`` run tests for your project on your local machine.

Project deployment
------------------

``dp deploy`` will sync with your bucket provider. The provider will be chosen automatically based on the remote URL.
Usually, it is worth pointing ``dp deploy`` to a JSON or YAML file with provider-specific data like access tokens or project
names. The *provider-specific data* should be interpreted as the ``**kwargs`` (keyword arguments) expected by a specific
`fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_'s FileSystem implementation. One would most likely want to
look at the `S3FileSystem <https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem>`_ or
`GCSFileSystem <https://gcsfs.readthedocs.io/en/latest/api.html#gcsfs.core.GCSFileSystem>`_ documentation.

E.g., to connect with Google Cloud Storage, one should run:

.. code-block:: bash

 echo '{"token": "<PATH_TO_YOUR_TOKEN>", "project_name": "<YOUR_PROJECT_NAME>"}' > gs_args.json
 dp deploy --dags-path "gs://<YOUR_GS_PATH>" --blob-args gs_args.json

However, in some cases, you do not need to do so, e.g. when using **gcloud** with properly set local credentials. In such
a case, you can try to run just the ``dp deploy --dags-path "gs://<YOUR_GS_PATH>"`` command and let ``gcsfs`` search for
the credentials.
Please refer to the documentation of the specific ``fsspec``'s implementation for more information about the required
keyword arguments.

``dags-path`` as config argument
++++++++++++++++++++++++++++++++

You can also list your path in the ``config/base/airflow.yml`` file, as a ``dags_path`` argument:

.. code-block:: yaml

 dags_path: gs://<YOUR_GS_PATH>
 # ... rest of the 'airflow.yml' file

In such a case, you do not have to provide a ``--dags-path`` flag, and you can just call ``dp deploy`` instead.

Packing and publishing
----------------------

The built project can be processed to a **dbt** package by calling ``dp publish``. ``dp publish`` parses ``manifest.json``
and prepares a package that lists models outputted by transformations, saving it in the ``build/package`` directory.

Preparing dbt environment
-------------------------

Sometimes you would like to use standalone **dbt** or an application that interfaces with it (like VS Code plugin).
``dp prepare-env`` prepares your local environment to be more conformant with standalone **dbt** requirements, e.g.,
by saving ``profiles.yml`` in the home directory.

However, be aware that most of the time you do not need to do so, and you can comfortably use ``dp run`` and ``dp test``
commands to interface with the **dbt** instead.

Clean project
-------------

When finished, call ``dp clean`` to remove compilation-related directories.
