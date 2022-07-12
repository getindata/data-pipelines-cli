``data-pipelines-cli``: CLI for data platform
==============================================

.. image:: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue.svg
   :target: https://github.com/getindata/data-pipelines-cli
   :alt: Python Version

.. image:: https://badge.fury.io/py/data-pipelines-cli.svg
   :target: https://pypi.org/project/data-pipelines-cli/
   :alt: PyPI Version

.. image:: https://pepy.tech/badge/data-pipelines-cli
   :target: https://pepy.tech/project/data-pipelines-cli
   :alt: Downloads

.. image:: https://api.codeclimate.com/v1/badges/e44ed9383a42b59984f6/maintainability
   :target: https://codeclimate.com/github/getindata/data-pipelines-cli/maintainability
   :alt: Maintainability

.. image:: https://api.codeclimate.com/v1/badges/e44ed9383a42b59984f6/test_coverage
   :target: https://codeclimate.com/github/getindata/data-pipelines-cli/test_coverage
   :alt: Test Coverage

Introduction
------------
Data Pipelines CLI is a command-line tool providing an easy way to build and manage data pipelines based on DBT
in an environment with GIT, Airflow, DataHub, VSCode, etc.

The tool can be used in any environment with access to shell and ``Python`` installed.

**data-pipelines-cli**'s main task is to cover technical complexities and provides an abstraction over all components
that take part in Data Pipelines creation and execution. Thanks to the integration with templating engine it allows Analytics
Engineers to create and configure new projects. The tool also simplifies automation as it handles deployments and
publications of created transformations.

Community
------------
Although the tools were created by GetInData and used in their project it is open-sourced and everyone is welcome
to use and contribute to making it better and more powerful.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installation
   setup_environment
   usage
   configuration
   integration
   cli
   api
   changelog
