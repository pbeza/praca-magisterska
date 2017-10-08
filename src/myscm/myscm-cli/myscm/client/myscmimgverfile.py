# -*- coding: utf-8 -*-
import logging

from myscm.common.versionfile import EmptyFileVersionFileError
from myscm.common.versionfile import NotIntegerVersionFileError
from myscm.common.versionfile import OutOfAllowedRangeIntegerInFileVersionFileError
from myscm.common.versionfile import TooManyLinesVersionFileError
from myscm.common.versionfile import VersionFile
from myscm.common.versionfile import VersionFileError

logger = logging.getLogger(__name__)


class MySCMImgVersionFile(VersionFile):
    """Representation of file holding recently applied mySCM system image by
       running myscm-srv with --apply-img option."""

    IMG_VER_STARTING_VALUE = 0

    def __init__(self, path):
        super().__init__(path, starting_value=self.IMG_VER_STARTING_VALUE)

    def parse(self, create=False):
        m = None
        ver = None

        try:
            ver = super().parse(create)
        except EmptyFileVersionFileError:
            m = "'{}' is empty, but it should contain integer number "\
                "specifying version of the recently applied mySCM system "\
                "image".format(self.path)
        except TooManyLinesVersionFileError:
            m = "'{}' has too many lines. It is expected to have single line "\
                "with version of the recently applied mySCM system image"\
                .format(self.path)
        except NotIntegerVersionFileError as e:
            m = "First and only line of the '{}' file is supposed to be "\
                "integer corresponding to recently applied mySCM system "\
                "image version. Read value: '{}'".format(self.path, e.value)
        except OutOfAllowedRangeIntegerInFileVersionFileError as e:
            m = "Integer {} read from {} file that should contain integer "\
                "number corresponding to the recently applied mySCM system "\
                "image".format(e.value, self.path)
        except VersionFileError as e:
            m = "Failed to parse '{}'. Check if this file exists and has "\
                "sufficient read permissions".format(self.path)
            raise VersionFileError(m, e) from e

        if m:
            m = "{} (see --apply-img option)".format(m)
            raise VersionFileError(m)

        return ver
