from odoo import api, models, _, fields
from odoo.tools import float_round


class PublicProduct(models.Model):
    _inherit = "product.template"

    guid = fields.Char(string='Guid 1C:Enterprise')


class ProductCategory(models.Model):
    _inherit = 'product.category'
    guid = fields.Char(string='Guid 1C:Enterprise')


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    guid = fields.Char(string='Guid 1C:Enterprise')
    brand = fields.Char(string='Brand')
    active = fields.Boolean(default=True)