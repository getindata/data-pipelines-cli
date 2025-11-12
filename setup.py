"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "click==8.1.3",
    "pyyaml==6.0.1",
    "types-PyYAML==6.0.12.2",
    "copier==7.0.1",
    "pyyaml-include<2",  # copier 7.0.1 requires pyyaml-include 1.x
    "pydantic<2",  # copier 7.0.1 requires pydantic 1.x
    "Jinja2>=3.1.3,<4",
    "fsspec>=2024.6.0,<2025.0.0",
    "packaging>=23.0",
    "colorama==0.4.5",
    # dbt-core removed: all adapters provide it as dependency, no valid workflow
    # exists without adapter. Users must install with adapter extra, e.g.:
    # pip install data-pipelines-cli[snowflake]
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs>=2024.6.0,<2025.0.0"],
    "s3": ["s3fs>=2024.6.0,<2025.0.0"],
}

EXTRA_REQUIRE = {
    # DBT adapters - version ranges support dbt 1.7.x through 1.10.x
    "bigquery": ["dbt-bigquery>=1.7.2,<2.0.0"],
    "postgres": ["dbt-postgres>=1.7.3,<2.0.0"],
    "snowflake": ["dbt-snowflake>=1.7.1,<2.0.0"],  # Primary adapter
    "redshift": ["dbt-redshift>=1.7.1,<2.0.0"],
    "glue": ["dbt-glue>=1.7.0,<2.0.0", "dbt-spark[session]>=1.7.1,<2.0.0"],
    "databricks": ["dbt-databricks-factory>=0.1.1"],
    "dbt-all": [
        "dbt-bigquery>=1.7.2,<2.0.0",
        "dbt-postgres>=1.7.3,<2.0.0",
        "dbt-snowflake>=1.7.1,<2.0.0",
        "dbt-redshift>=1.7.1,<2.0.0",
        "dbt-glue>=1.7.0,<2.0.0",
    ],
    # ---
    "docker": ["docker==6.0.1"],
    "datahub": ["acryl-datahub[dbt]==0.12.0.5"],
    "git": ["GitPython==3.1.29"],
    "looker": ["dbt2looker==0.11.0"],
    "tests": [
        "pytest==7.2.0",
        "pytest-cov==4.0.0",
        "pre-commit==2.20.0",
        "tox==3.27.1",
        "tox-gh-actions==2.12.0",
        "moto[server,s3]>=4.2.0,<5.0.0",
        "gcp-storage-emulator==2022.6.11",
        "GitPython==3.1.29",
        "types-requests==2.28.11.5",
        "gcsfs>=2024.6.0,<2025.0.0",
        "s3fs>=2024.6.0,<2025.0.0",
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
    version="0.32.0",
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
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
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
