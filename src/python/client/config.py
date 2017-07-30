# -*- coding: utf-8 -*-
import logging

from client.error import ClientError
from common.config import BaseConfig

logger = logging.getLogger(__name__)


class ClientConfigError(ClientError):
    pass


class ClientConfig(BaseConfig):
    """Client-specific configuration manager."""

    def __init__(self, *options, **kwargs):
        super().__init__(*options, **kwargs)
