from setuptools import setup

__author__ = "Patryk Bęza"

setup(
        name="myscm-cli",
        version="0.9.0",
        description="Client side of the My Simple Software Configuration Management (SCM) tool",
        long_description="""Client side of the Simple Software Configuration Management (SCM) tool that is
intended to apply system images created with myscm-srv applicationwhich is
myscm-cli counterpart.""",
        keywords="scm packaging software distribution",
        author="Patryk Bęza",
        author_email="patryk.beza@gmail.com",
        packages=["myscm.client"],
        classifiers=[
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
        scripts=["myscm/myscm-cli"],
        install_requires=[
            "myscm-common", "aide", "openssl", "argcomplete", "colorlog",
            "argparse", "configparser", "distro", "progressbar2", "pysftp",
            "pyyaml", "termcolor", "diff-match-patch", "lockfile", "paramiko"
        ],
        data_files=[
            ("/etc/myscm-cli", ["myscm/client/config/config.ini"]),
            ("/etc/myscm-cli", ["myscm/client/config/log_config.yaml"]),
            ("/var/lib/myscm-cli", ["myscm/client/config/img_ver.myscm-cli"]),
            ("/usr/share/man/man1", ["myscm-cli.1.gz"]),
            ("/usr/share/doc/myscm-cli", ["copyright"])
            # ("/etc/ssl/private", ["myscm/client/config/security/myscm-srv.cert.pub.pem"]),
            # ("/etc/ssl/private", ["myscm/client/config/security/myscm-srv.cert.pem"]),
        ]
)
