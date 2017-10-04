from setuptools import setup, find_packages

__author__ = "Patryk Bęza"

# Useful commands:
#   python3 setup.py --command-packages=stdeb.command bdist_deb
#   python3 setup.py clean --all
#   dpkg -c deb_dist/python3-myscm-srv_0.9.0-1_all.deb

setup(
        name="myscm-cli",
        version="0.9.0",
        description=("Client side of the My Simple Software Configuration"
                     "Management (SCM) tool"),
        long_description="Client side of the Simple Software Configuration "
                         "Management (SCM) tool that is intended to apply "
                         "system images created with myscm-srv application "
                         "which is myscm-cli counterpart.",
        keywords="scm packaging software distribution",
        author="Patryk Bęza",
        author_email="patryk.beza@gmail.com",
        packages=["myscm.client"],
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
        license="GPLv3+",
        scripts=["myscm/myscm-cli.py"],
        install_requires=[
            "myscm-common", "argcomplete", "colorlog", "argparse",
            "configparser", "distro", "progressbar2", "pysftp", "pyyaml",
            "termcolor"
        ],
        data_files=[
            ("/etc/myscm-cli", ["myscm/client/config/config.ini"]),
            ("/etc/myscm-cli", ["myscm/client/config/log_config.yaml"]),
            ("/etc/ssl/private", ["myscm/client/config/security/myscm-srv.cert.pub.pem"]),
            ("/etc/ssl/private", ["myscm/client/config/security/myscm-srv.cert.pem"]),
            ("/var/lib/myscm-cli", ["myscm/client/config/img_ver.myscm-cli"]),
            ("/usr/share/man/man1", ["../../../../doc/man/myscm-cli.1.gz"])
        ]
)
