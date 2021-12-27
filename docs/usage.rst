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
should rather use ``{{ env_var('VARIABLE') }}` as a value and provide those settings as environment variables. E.g., by
setting those in your ``config/<ENV>/k8s.yml`` file, in ``envs`` dictionary:

.. code-block:: yaml

 # config/base/bigquery.yml
 method: oauth
 dataset: "{{ env_var('GCP_DATASET') }}"
 project: my-gcp-project
 threads: 1

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
Just remember, **project-scoped variables take precedence over global-scoped ones.**

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
``dp deploy`` also requires the user to point to JSON or YAML file with provider-specific data like access tokens or project
names. The *provider-specific data* should be interpreted as the ``**kwargs`` (keyword arguments) expected by a specific
`fsspec <https://filesystem-spec.readthedocs.io/en/latest/>`_'s FileSystem implementation. One would most likely want to
look at the `S3FileSystem <https://s3fs.readthedocs.io/en/latest/api.html#s3fs.core.S3FileSystem>`_ or
`GCSFileSystem <https://gcsfs.readthedocs.io/en/latest/api.html#gcsfs.core.GCSFileSystem>`_ documentation.

E.g., to connect with Google Cloud Storage, one should run:

.. code-block:: bash

 echo '{"token": "<PATH_TO_YOUR_TOKEN>", "project_name": "<YOUR_PROJECT_NAME>"}' > gs_args.json
 dp deploy "gs://<YOUR_GS_PATH>" --blob-args gs_args.json

Clean project
-------------

When finished, call ``dp clean`` to remove compilation-related directories.
