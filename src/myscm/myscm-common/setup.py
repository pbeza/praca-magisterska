from setuptools import setup, find_packages

__author__ = "Patryk Bęza"

setup(
        name="myscm-common",
        version="0.9.0",
        description=("Base of the Simple Software Configuration Management "
                     "(SCM) tool"),
        long_description="Base library of the Simple Software Configuration "
                         "Management (SCM) tool, specifically myscm-cli and "
                         "myscm-srv applications",
        keywords="scm packaging software distribution",
        author="Patryk Bęza",
        author_email="patryk.beza@gmail.com",
        packages=["myscm.common"],
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
            "Topic :: Utilities"
        ],
        platforms="POSIX",
        license="GPLv3",
        install_requires=[
            "myscm-common", "argcomplete", "colorlog", "argparse",
            "configparser", "distro", "progressbar2", "pysftp", "pyyaml",
            "termcolor", "diff-match-patch", "lockfile"
        ]
)
