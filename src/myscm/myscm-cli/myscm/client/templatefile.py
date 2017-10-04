# -*- coding: utf-8 -*-
import logging

from myscm.client.error import ClientError
from myscm.client.templatefilevars import get_templates_vars

logger = logging.getLogger(__name__)


class TemplateFileError(ClientError):
    pass


class TemplateFile:

    VAR_NAME_PLACEHOLDER = "$[{}]$"

    def __init__(self, template_path):
        self.template_path = template_path

    def replace_placeholders_with_values(self, output_path):
        computed_vars_values = dict()

        with open(self.template_path) as template_f:
            with open(output_path, "w") as out_f:
                for line in template_f:
                    self._append_line_to_file(line, out_f, computed_vars_values)

    def _get_full_var_name(self, var_name):
        return self.VAR_NAME_PLACEHOLDER.format(var_name)

    def _append_line_to_file(self, line, out_f, computed_vars_values):
        vars_mapping = get_templates_vars()

        for var_name, var_fun in vars_mapping.items():
            full_var_name = self._get_full_var_name(var_name)

            if full_var_name in line:
                var_value = computed_vars_values.get(var_name, var_fun())
                computed_vars_values[var_name] = var_value
                new_line = line.replace(full_var_name, var_value)
                out_f.write(new_line)
