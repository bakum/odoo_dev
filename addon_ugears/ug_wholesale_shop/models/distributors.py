from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "distrib.distributors"

    pallet_id = fields.Many2one('distrib.packages.sizes', 'Pallet', required=True)
