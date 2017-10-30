# -*- coding: utf-8 -*-
import logging
import os
import re

from myscm.client.error import ClientError
from myscm.client.templatefilevars import get_templates_vars

logger = logging.getLogger(__name__)


class TemplateFileError(ClientError):
    pass


class TemplateFile:
    """Representation of the configuration template file holding
       client-specific variable placeholders."""

    VAR_NAME_PLACEHOLDER = "<MYSCM:{}/>"
    ENV_VAR_NAME_REGEX_STR = "(<MYSCM:ENV:(.*?)/>)"

    def __init__(self, template_path):
        self.template_path = template_path
        self.env_var_name_regex = re.compile(self.ENV_VAR_NAME_REGEX_STR)

    def replace_placeholders_with_values(self, output_path):
        computed_vars_values = dict()

        with open(self.template_path) as template_f:
            with open(output_path, "w") as out_f:
                for line in template_f:
                    self._append_line_to_file(line, out_f, computed_vars_values)

    def _get_full_var_name(self, var_name):
        return self.VAR_NAME_PLACEHOLDER.format(var_name)

    def get_env_value(self, var_name):
        val = None

        try:
            val = os.environ[var_name]
        except KeyError as e:
            val = "${{{}}}".format(var_name)
            logger.error("'{}' environment variable is not recognized".format(
                         var_name))

        return val

    def _append_line_to_file(self, line, out_f, computed_vars_values):
        vars_mapping = get_templates_vars()

        for var_name, var_fun in vars_mapping.items():
            full_var_name = self._get_full_var_name(var_name)

            if full_var_name in line:
                var_value = computed_vars_values.get(var_name, var_fun())
                computed_vars_values[var_name] = var_value
                line = line.replace(full_var_name, var_value)

        match = re.findall(self.env_var_name_regex, line.strip())

        if match:
            for i in match:
                if len(i) != 2:
                    logger.warning("Tuple was expected")
                else:
                    full_var = i[0]
                    short_var = i[1].upper()
                    var_value = self.get_env_value(short_var)
                    line = line.replace(full_var, var_value)

        out_f.write(line)
