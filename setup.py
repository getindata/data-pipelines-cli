"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "MarkupSafe==2.1.1",
    "Werkzeug==2.2.3",
    "click==8.1.3",
    "pyyaml==6.0.1",
    "types-PyYAML==6.0.12.2",
    "copier==7.0.1",
    "Jinja2==3.1.2",
    "fsspec==2022.11.0",
    "packaging==21.3",
    "colorama==0.4.5",
    "dbt-core==1.7.3",
    "pydantic<2",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs==2022.11.0"],
    "s3": ["s3fs==2022.11.0"],
}

EXTRA_REQUIRE = {
    # DBT adapters
    "bigquery": ["dbt-bigquery==1.7.2"],
    "postgres": ["dbt-postgres==1.7.3"],
    "snowflake": ["dbt-snowflake==1.7.1"],
    "redshift": ["dbt-redshift==1.7.1"],
    "glue": [
        "dbt-glue==1.7.0",
        "dbt-spark[session]==1.7.1"
    ],
    "databricks": ["dbt-databricks-factory>=0.1.1"],
    "dbt-all": [
        "dbt-bigquery==1.7.2",
        "dbt-postgres==1.7.3",
        "dbt-snowflake==1.7.1",
        "dbt-redshift==1.7.1",
        "dbt-glue==1.7.0",
    ],
    # ---
    "docker": ["docker==6.0.1"],
    "datahub": ["acryl-datahub[dbt]==0.10.4"],
    "git": ["GitPython==3.1.29"],
    "looker": ["dbt2looker==0.11.0"],
    "tests": [
        "pytest==7.2.0",
        "pytest-cov==4.0.0",
        "pre-commit==2.20.0",
        "tox==3.27.1",
        "tox-gh-actions==2.12.0",
        "moto[s3]==4.0.11",
        "gcp-storage-emulator==2022.6.11",
        "GitPython==3.1.29",
        "types-requests==2.28.11.5",
        "gcsfs==2022.11.0",
        "s3fs==2022.11.0",
    ],
    "docs": [
        "sphinx==5.3.0",
        "sphinx-rtd-theme==1.1.1",
        "sphinx-click==4.4.0",
        "myst-parser==0.18.1",
        "GitPython==3.1.29",
        "colorama==0.4.5",
        "pytz==2023.3",
    ],
    **EXTRA_FILESYSTEMS_REQUIRE,
}

setup(
    name="data_pipelines_cli",
    version="0.27.0",
    description="CLI for data platform",
    long_description=README,
    long_description_content_type="text/markdown",
    license="Apache Software License (Apache 2.0)",
    license_files=("LICENSE",),
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="dbt airflow cli",
    author="Andrzej Swatowski",
    author_email="andrzej.swatowski@getindata.com",
    url="https://github.com/getindata/data-pipelines-cli/",
    packages=find_packages(exclude=["docs", "tests"]),
    include_package_data=True,
    install_requires=INSTALL_REQUIREMENTS,
    extras_require=EXTRA_REQUIRE,
    entry_points={"console_scripts": ["dp=data_pipelines_cli.cli:cli"]},
)
