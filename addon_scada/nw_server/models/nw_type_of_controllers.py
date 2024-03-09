from odoo import models, fields


class TypesOfControllers(models.Model):
    _name = 'nw.types.controllers'
    _description = 'Types of controllers'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(default=True)
