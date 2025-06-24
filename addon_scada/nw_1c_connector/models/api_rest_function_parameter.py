# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ApiRestFunctionParameter(models.Model):
    _name = 'api.rest.function.parameter'
    _description = "Api Rest Function Parameter"

    path_id = fields.Many2one(
        'api.rest.path', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    sequence = fields.Integer()
    type = fields.Selection([
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('string', 'String'),
        ('array', 'Array'),
        ('object', 'Object (Dictionnary)'),
    ], required=True)
    description = fields.Char()
    required = fields.Boolean()
    default_value = fields.Char()

    @api.onchange('default_value')
    def _onchange_default_value(self):
        if self.default_value:
            self.required = False

    @api.onchange('required')
    def _onchange_required(self):
        if self.default_value:
            self.required = False
