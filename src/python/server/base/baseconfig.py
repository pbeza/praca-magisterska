# -*- coding: utf-8 -*-


class BaseServerConfig:

    def __init__(self, *options, **kwargs):
        # http://stackoverflow.com/q/2466191/1321680
        for d in options:
            for key in d:
                setattr(self, key, d[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
