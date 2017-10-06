from setuptools import setup

__author__ = "Patryk Bęza"

setup(
        name="myscm-srv",
        version="0.9.0",
        description="Server side of the Simple Software Configuration Management (SCM) tool",
        long_description="""Server side of the Simple Software Configuration Management (SCM) tool that is
intended to create system images that will be applied by the myscm-cli which is
myscm-srv counterpart.""",
        keywords="scm packaging software distribution",
        author="Patryk Bęza",
        author_email="patryk.beza@gmail.com",
        packages=["myscm.server"],
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
        scripts=["myscm/myscm-srv"],
        install_requires=[
            "myscm-common", "openssl", "argcomplete", "colorlog", "argparse",
            "configparser", "distro", "progressbar2", "pysftp", "pyyaml",
            "termcolor", "diff-match-patch", "lockfile"
        ],
        data_files=[
            ("/etc/myscm-srv", ["myscm/server/config/aide.conf"]),
            ("/etc/myscm-srv", ["myscm/server/config/config.ini"]),
            ("/etc/myscm-srv", ["myscm/server/config/log_config.yaml"]),
            ("/var/lib/myscm-srv", ["myscm/server/config/db_ver.myscm-srv"]),
            ("/usr/share/man/man1", ["myscm-srv.1.gz"]),
            ("/usr/share/doc/myscm-srv", ["copyright"])
            # ("/etc/ssl/private", ["myscm/server/config/security/myscm-srv.cert.priv.pem"]),
            # ("/etc/ssl/private", ["myscm/server/config/security/myscm-srv.cert.pub.pem"]),
            # ("/etc/ssl/private", ["myscm/server/config/security/myscm-srv.cert.pem"]),
        ]
)
