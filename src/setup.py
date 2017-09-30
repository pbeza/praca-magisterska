from setuptools import setup, find_packages

__author__ = "Patryk Bęza"

# https://setuptools.readthedocs.io/en/latest/setuptools.html#new-and-changed-setup-keywords

setup(
        name="myscm",
        version="0.9.0",
        description=("Server side of the Simple Software Configuration Management (SCM) tool for "
                     "managing software and configuration of the clients "
                     "running GNU/Linux distributions"),
        long_description="",
        keywords="scm packaging software distribution",
        author="Patryk Bęza",
        author_email="patryk.beza@gmail.com",
        url="",
        packages=["myscm-cli", "myscm-srv"],
        # packages=find_packages(exclude=['contrib', 'docs', 'tests']),
        packages_dir={"hello_py": "hello_py"}
        classifiers = [
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: System Administrators",
            "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
            "Natural Language :: English",
            "Operating System :: POSIX :: Linux",
            "Programming Language :: Python :: 3",
            "Topic :: System :: Archiving :: Packaging",
            "Topic :: System :: Installation/Setup",
            "Topic :: System :: Software Distribution",
            "Topic :: Utilities",
        ],
        platforms="POSIX",
        license="MIT",
        #scripts=["scripts/hello"],
        entry_points={
            "console_scripts": [
                "myscm-srv=test.myscm-srv:main"
            ]
        },
        install_requires=[
            "test"
        ],
        extras_require={
            'dev': ['check-manifest'],
            'test': ['coverage'],
        },
        package_data={
            'sample': ['package_data.dat'],
        },
        data_files=[('my_data', ['data/data_file'])],
        include_package_data=True,
        exclude_package_data={}
)

# python setup.py --command-packages=stdeb.command bdist_deb
# python3 setup.py install --install-layout=deb
# python setup.py <some_command> <options>
# python setup.py --help-commands
