# -*- coding: utf-8 -*-


class MySCMError(Exception):
    """Representation of the mySCM error."""

    def __init__(self, message, internal_error=None, verbose=True):
        super().__init__(message)
        self.internal_error = internal_error
        self.verbose = verbose

    def get_details(self, verbose=True):
        return self.internal_error

    def __str__(self):
        errmsg = super().__str__()
        details = self.get_details()

        if self.verbose and details is not None:
            errmsg += ". {}".format(details)

        return errmsg
