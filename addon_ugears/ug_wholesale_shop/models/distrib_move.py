from odoo import models, fields


class DistribMove(models.Model):
    _inherit = "distrib.distributors.move"
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Line', index='btree_not_null')