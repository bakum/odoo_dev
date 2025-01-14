from odoo import models, fields, api


class DistribMove(models.Model):
    _inherit = "distrib.distributors.move"
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Line', index='btree_not_null')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order', index='btree_not_null')

    order_count = fields.Integer(string="Order Count", compute='_get_order_count')

    @api.depends('sale_order_id')
    def _get_order_count(self):
        for move in self:
            if move.sale_order_id:
                move.order_count = 1
            else:
                move.order_count = 0

    def action_view_order(self):
        self.ensure_one()
        source_orders = self.sale_order_id
        result = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        if len(source_orders) > 1:
            result['domain'] = [('id', 'in', source_orders.ids)]
        elif len(source_orders) == 1:
            result['views'] = [(self.env.ref('sale.view_order_form', False).id, 'form')]
            result['res_id'] = source_orders.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result