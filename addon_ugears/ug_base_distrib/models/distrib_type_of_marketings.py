from odoo import models, fields


class TypesOfMarketings(models.Model):
    _name = 'distrib.types.marketings'
    _description = 'Types of marketings'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
