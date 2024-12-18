from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order.line"

    cartoon_id = fields.Many2one(
        related='product_template_id.cartoon_id',
        string="Cartoon ID",
        store=True, precompute=True)