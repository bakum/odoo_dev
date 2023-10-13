from odoo import models, fields


class ProductThemes(models.Model):
    _name = 'distrib.sales.channels'
    _description = 'Sales Channels'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
    guid = fields.Char(string='Guid 1C:Enterprise')
