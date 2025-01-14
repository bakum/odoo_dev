from odoo import models, fields, api, _


class DistributorMoveLines(models.Model):
    _inherit = 'distrib.distributors.move.line'

    sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_incoming_rel',
        'incoming_line_id', 'order_line_id',
        string='Sales Order Lines', readonly=True, copy=False)