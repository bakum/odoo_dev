from odoo import models


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'utm.mixin']

    def get_source_orders(self):
        self.ensure_one()
        source_orders = self.line_ids.sale_line_ids.order_id[:1]
        return source_orders