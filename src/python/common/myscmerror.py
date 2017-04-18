# -*- coding: utf-8 -*


class MySCMError(Exception):

    def __init__(self, message, internal_error=None):
        super().__init__(message)
        self.internal_error = internal_error

    def get_details(self):
        return str(self.internal_error)
