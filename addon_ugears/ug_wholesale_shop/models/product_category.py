from odoo import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    guid = fields.Char(string='Guid 1C:Enterprise')