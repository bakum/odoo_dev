from odoo import api, models, _, fields


class PricelistsDistrib(models.Model):
    _inherit = "product.pricelist"

    guid = fields.Char(string='Guid 1C:Enterprise')
