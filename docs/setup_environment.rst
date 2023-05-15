Setup an environment
=====

This section is for Data Engineers who will be preparing and administrating the whole environment.
It describes steps that should be done to prepare the DP tool to be used in an organization with full potential.

Create Data Pipeline project template
----------------

The first thing that you need to do is to create a git repository with a project template used later to create multiple
projects. The template should contain the whole directory structure and files used in your projects.
Additionally, it should have a connection configuration to all components in your environment, CICD, and all other
aspects specific to your company. Here you can find templates examples that you can adjust to your need:
https://github.com/getindata/data-pipelines-template-example . Based on the template The Data Pipelines CLI will ask a user
a series of questions to build the final project.

Thanks to the ``copier`` you can leverage Jinja template syntax to create easily modifiable configuration templates.
Just create a ``copier.yml`` and configure the template questions (read more at
`copier documentation <https://copier.readthedocs.io/en/stable/configuring/#the-copieryml-file/>`_).

Create a template to setup a local environment
----------------

Working with Data Pipelines usually requires local variables to be set to run and test avoiding messing in shared environments (DEV, STAGE, PROD). To simplify working environment preparation we also
decided to use templates that will ask a series of questions and generate local configuration in a home directory.

It requires a repository with a global configuration template file that you or your organization will be using.
The repository should contain ``dp.yml.tmpl`` file looking similar to this:

.. code-block:: yaml

  _templates_suffix: ".tmpl"
  _envops:
    autoescape: false
    block_end_string: "%]"
    block_start_string: "[%"
    comment_end_string: "#]"
    comment_start_string: "[#"
    keep_trailing_newline: true
    variable_end_string: "]]"
    variable_start_string: "[["

 templates:
   my-first-template:
     template_name: my-first-template
     template_path: https://github.com/<YOUR_USERNAME>/<YOUR_TEMPLATE>.git
 vars:
   username: [[ YOUR_USERNAME ]]

The file must contain a list of available templates. The templates will be displayed and available for selection in
Data Pipelines CLI. The next section contains variables that will be passed to the project whenever running in the configured environment. The
same rules apply in template creation as for project templates.
