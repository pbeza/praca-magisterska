# -*- coding: utf-8 -*-
import logging
import os

from myscm.common.error import MySCMError


logger = logging.getLogger(__name__)


class VersionFileError(MySCMError):
    pass


class DetailedVersionFileError(VersionFileError):

    def __init__(self, msg, value, *args):
        super().__init__(msg, *args)
        self.value = value


class EmptyFileVersionFileError(VersionFileError):
    pass


class TooManyLinesVersionFileError(VersionFileError):
    pass


class NotIntegerVersionFileError(DetailedVersionFileError):
    pass


class NegativeIntegerInFileVersionFileError(DetailedVersionFileError):
    pass


class VersionFile:
    """Representation of the file holding single integer in single line."""

    DEFAULT_STARTING_VALUE = 0

    def __init__(self, path, starting_value=None):
        self.path = path
        self.version = None
        if starting_value is None:
            self.starting_value = self.DEFAULT_STARTING_VALUE
        else:
            self.starting_value = starting_value

    def get_version(self, create=False):
        return self.parse(create)

    def parse(self, create=False):
        if create and not self.exist():
            return self.create()

        first_line = None
        second_line = None

        try:
            with open(self.path) as f:
                first_line = f.readline().strip()
                second_line = f.readline()
        except OSError as e:
            raise VersionFileError("Failed to open file", e) from e

        if not first_line:
            raise EmptyFileVersionFileError("Empty file")

        if second_line:
            raise TooManyLinesVersionFileError("Too many lines in file")

        try:
            ver = first_line.strip()
            ver = int(first_line)
        except:
            raise NotIntegerVersionFileError("Integer was expected", ver)

        if ver < 0:
            raise NegativeIntegerInFileVersionFileError(
                                           "Positive number was expected", ver)

        self.version = ver

        return ver

    def increment(self, create=False):
        if create and not self.exist():
            self.create()

        old_ver = self.parse()
        new_ver = old_ver + 1
        self.set_value(new_ver)

        return new_ver

    def set_value(self, val):
        try:
            with open(self.path, "w+") as f:
                f.write(str(val))
        except OSError as e:
            raise VersionFileError("Failed to open file for writing", e) from e

        self.version = val

        return val

    def exist(self):
        return os.path.isfile(self.path)

    def create(self):
        return self.set_value(self.starting_value)
