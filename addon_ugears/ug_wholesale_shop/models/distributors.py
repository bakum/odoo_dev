from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "distrib.distributors"

    pallet_id = fields.Many2one('distrib.packages.sizes', 'Pallet', required=True)

    discount_available = fields.Boolean('Volume discount', default=False)
    discount_after = fields.Integer('Discount After', default=50000)
    discount_value = fields.Float('Discount Value, %', digits = (10, 3), default=2.0)
