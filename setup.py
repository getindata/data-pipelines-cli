"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "click<8.0",
    "questionary==1.10.0",
    "pyyaml>=5.1, <6.0",
    "types-PyYAML>=6.0",
    "copier==5.1.0",
    "dbt>=0.21, <0.22",
    "fsspec",
    "dbt-airflow-manifest-parser>=0.14.0,<0.15",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcp": ["gcsfs"],
    "s3": ["s3fs"],
}

EXTRA_REQUIRE = {
    "docker": ["docker>=5.0"],
    "datahub": ["acryl-datahub>=0.8.17, <0.8.18"],
    "tests": [
        "pytest>=6.2.2, <7.0.0",
        "pytest-cov>=2.8.0, <3.0.0",
        "pre-commit==2.15.0",
        "tox==3.21.1",
        "moto[s3]==2.2.16",
        "gcp-storage-emulator==2021.12.2",
        *(
            [
                require
                for requires_list in EXTRA_FILESYSTEMS_REQUIRE.values()
                for require in requires_list
            ]
        ),
    ],
    **EXTRA_FILESYSTEMS_REQUIRE,
}

setup(
    name="data_pipelines_cli",
    version="0.3.0",
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
    author=u"Andrzej Swatowski",
    author_email="andrzej.swatowski@getindata.com",
    url="https://github.com/getindata/data-pipelines-cli/",
    packages=find_packages(exclude=["examples", "tests"]),
    include_package_data=True,
    install_requires=INSTALL_REQUIREMENTS,
    extras_require=EXTRA_REQUIRE,
    entry_points={"console_scripts": ["dp=data_pipelines_cli.cli:cli"]},
)
