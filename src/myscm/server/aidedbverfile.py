# -*- coding: utf-8 -*-
import logging

from myscm.common.versionfile import EmptyFileVersionFileError
from myscm.common.versionfile import NegativeIntegerInFileVersionFileError
from myscm.common.versionfile import NotIntegerVersionFileError
from myscm.common.versionfile import TooManyLinesVersionFileError
from myscm.common.versionfile import VersionFile
from myscm.common.versionfile import VersionFileError

logger = logging.getLogger(__name__)


class MySCMDatabaseVersionFile(VersionFile):
    """Representation of file holding recently created mySCM AIDE database by
       running myscm-srv with --scan option."""

    DB_VER_STARTING_VALUE = 0

    def __init__(self, path):
        super().__init__(path, starting_value=self.DB_VER_STARTING_VALUE)

    def parse(self, create=False):
        m = None
        ver = None

        try:
            ver = super().parse(create)
        except EmptyFileVersionFileError:
            m = "'{}' is empty, but it should contain integer number "\
                "specifying version of the recently generated mySCM AIDE "\
                "database".format(self.path)
        except TooManyLinesVersionFileError:
            m = "'{}' has too many lines. It is expected to have single line "\
                "with version of the recently generated mySCM AIDE database"\
                .format(self.path)
        except NotIntegerVersionFileError as e:
            m = "First and only line of the '{}' file is supposed to be "\
                "integer corresponding to recently generated mySCM AIDE "\
                "database version. Read value: '{}'".format(self.path, e.value)
        except NegativeIntegerInFileVersionFileError as e:
            m = "Negative integer {} read from {} file that should contain "\
                "integer number corresponding to the recently generated "\
                "mySCM AIDE database".format(e.value, self.path)
        except VersionFileError as e:
            m = "Failed to parse '{}'. Check if this file exists and has "\
                "sufficient read permissions".format(self.path)
            raise VersionFileError(m, e) from e

        if m:
            m = "{} (see --scan option)".format(m)
            raise VersionFileError(m)

        return ver
