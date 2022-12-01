"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "MarkupSafe",
    "Werkzeug",
    "click",
    "questionary",
    "pyyaml<6.0.0,>=5.3.1",
    "types-PyYAML",
    "copier==5.1.0",
    "Jinja2",
    "fsspec",
    "packaging",
    "colorama",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs"],
    "s3": ["s3fs"],
}

EXTRA_REQUIRE = {
    # DBT adapters
    "bigquery": ["dbt-bigquery"],
    "postgres": ["dbt-postgres"],
    "snowflake": ["dbt-snowflake"],
    "redshift": ["dbt-redshift"],
    # ---
    "docker": ["docker"],
    "datahub": ["acryl-datahub[dbt]"],
    "git": ["GitPython"],
    "looker": ["dbt2looker"],
    "tests": [
        "pytest",
        "pytest-cov",
        "pre-commit",
        "tox",
        "moto[s3]",
        "gcp-storage-emulator",
        "GitPython",
        "types-requests",
        *(
            [
                require
                for requires_list in EXTRA_FILESYSTEMS_REQUIRE.values()
                for require in requires_list
            ]
        ),
    ],
    "docs": [
        "sphinx",
        "sphinx-rtd-theme",
        "sphinx-click",
        "myst-parser",
        "GitPython",
        "colorama",
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
