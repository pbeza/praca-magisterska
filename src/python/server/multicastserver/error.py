# -*- coding: utf-8 -*

from common.myscmerror import MySCMError


class MulticastServerError(MySCMError):
    pass


class MulticastServerParserError(MulticastServerError):
    pass
