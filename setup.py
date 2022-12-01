"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "MarkupSafe==2.0.1",
    "Werkzeug==2.1.2",
    "click==8.1.3",
    "questionary==1.10.0",
    "pyyaml==5.4.1",
    "types-PyYAML==6.0.12.2",
    "copier==5.1.0",
    "Jinja2==2.11.3",
    "fsspec==2022.11.0",
    "packaging==20.9",
    "colorama==0.4.5",
    "dbt-core==1.2.3",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs==2022.11.0"],
    "s3": ["s3fs==2022.11.0"],
}

EXTRA_REQUIRE = {
    # DBT adapters
    "bigquery": ["dbt-bigquery==1.2.0"],
    "postgres": ["dbt-postgres==1.2.3"],
    "snowflake": ["dbt-snowflake==1.2.0"],
    "redshift": ["dbt-redshift==1.2.1"],
    # ---
    "docker": ["docker==6.0.1"],
    "datahub": ["acryl-datahub[dbt]==0.9.3"],
    "git": ["GitPython==3.1.29"],
    "looker": ["dbt2looker"],
    "tests": [
        "pytest==7.2.0",
        "pytest-cov==4.0.0",
        "pre-commit==2.20.0",
        "tox==3.27.1",
        "moto[s3]==4.0.11",
        "gcp-storage-emulator==2022.6.11",
        "GitPython==3.1.29",
        "types-requests==2.28.11.5",
        *(
            [
                require
                for requires_list in EXTRA_FILESYSTEMS_REQUIRE.values()
                for require in requires_list
            ]
        ),
    ],
    "docs": [
        "sphinx==5.1.1",
        "sphinx-rtd-theme==1.1.1",
        "sphinx-click==4.3.0",
        "myst-parser==0.18.1",
        "GitPython==3.1.29",
        "colorama==0.4.5",
    ],
    **EXTRA_FILESYSTEMS_REQUIRE,
}

setup(
    name="data_pipelines_cli",
    version="0.23.0",
    description="CLI for data platform",
    long_description=README,
    long_description_content_type="text/markdown",
    license="Apache Software License (Apache 2.0)",
    license_files=("LICENSE",),
    python_requires=">=3",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
