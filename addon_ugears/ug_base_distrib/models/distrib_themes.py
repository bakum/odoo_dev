from odoo import models, fields


class ProductThemes(models.Model):
    _name = 'distrib.product.theme'
    _description = 'Product theme'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(default=True)
    guid = fields.Char(string='Guid 1C:Enterprise')
    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='theme_id',
        string="Theming Products")
