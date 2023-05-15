"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "MarkupSafe==2.1.1",
    "Werkzeug==2.2.2",
    "click==8.1.3",
    "pyyaml==6.0",
    "types-PyYAML==6.0.12.2",
    "copier==7.0.1",
    "Jinja2==3.1.2",
    "fsspec==2022.11.0",
    "packaging==21.3",
    "colorama==0.4.5",
    "dbt-core==1.3.1",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs==2022.11.0"],
    "s3": ["s3fs==2022.11.0"],
}

EXTRA_REQUIRE = {
    # DBT adapters
    "bigquery": ["dbt-bigquery==1.3.0"],
    "postgres": ["dbt-postgres==1.3.1"],
    "snowflake": ["dbt-snowflake==1.3.0"],
    "redshift": ["dbt-redshift==1.3.0"],
    "dbt-all": [
        "dbt-bigquery==1.3.0",
        "dbt-postgres==1.3.1",
        "dbt-snowflake==1.3.0",
        "dbt-redshift==1.3.0",
    ],
    # ---
    "docker": ["docker==6.0.1"],
    "datahub": ["acryl-datahub[dbt]==0.9.3.2"],
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
    ],
    **EXTRA_FILESYSTEMS_REQUIRE,
}

setup(
    name="data_pipelines_cli",
    version="0.25.0",
    description="CLI for data platform",
    long_description=README,
    long_description_content_type="text/markdown",
    license="Apache Software License (Apache 2.0)",
    license_files=("LICENSE",),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3.8",
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
