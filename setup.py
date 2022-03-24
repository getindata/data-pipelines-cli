"""data_pipelines_cli module."""

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

INSTALL_REQUIREMENTS = [
    "MarkupSafe==2.0.1",  # https://markupsafe.palletsprojects.com/en/2.1.x/changes/#version-2-1-0
    "dbt-core>=1.0.2",
    "click>=8.0.3,<9.0",
    "questionary==1.10.0",
    "pyyaml>=5.1, <6.0",
    "types-PyYAML>=6.0",
    "copier==5.1.0",
    "Jinja2>=2.11,<2.12",
    "fsspec",
    "packaging>=20.4,<21.0",
]

EXTRA_FILESYSTEMS_REQUIRE = {
    "gcs": ["gcsfs"],
    "s3": ["s3fs"],
}

EXTRA_REQUIRE = {
    "docker": ["docker>=5.0"],
    "datahub": ["acryl-datahub>=0.8.17, <0.8.18"],
    "git": ["GitPython==3.1.26"],
    "tests": [
        "pytest>=6.2.2, <7.0.0",
        "pytest-cov>=2.8.0, <3.0.0",
        "pre-commit==2.15.0",
        "tox==3.21.1",
        "moto[s3]==3.0.7",
        "gcp-storage-emulator==2021.12.2",
        "GitPython==3.1.26",
        *(
            [
                require
                for requires_list in EXTRA_FILESYSTEMS_REQUIRE.values()
                for require in requires_list
            ]
        ),
    ],
    "docs": [
        "sphinx==4.3.1",
        "sphinx-rtd-theme==1.0.0",
        "sphinx-click>=3.1,<3.2",
        "myst-parser>=0.16, <0.17",
        "GitPython==3.1.26",
    ],
    **EXTRA_FILESYSTEMS_REQUIRE,
}

setup(
    name="data_pipelines_cli",
    version="0.16.0",
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
    packages=find_packages(exclude=["docs", "tests"]),
    include_package_data=True,
    install_requires=INSTALL_REQUIREMENTS,
    extras_require=EXTRA_REQUIRE,
    entry_points={"console_scripts": ["dp=data_pipelines_cli.cli:cli"]},
)
