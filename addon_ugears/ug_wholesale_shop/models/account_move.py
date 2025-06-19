from odoo import models, fields, api


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'utm.mixin']

    bank_customer_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_bank_customer_id',
        help='Technical field to get the domain on the bank',
    )

    customer_bank_id = fields.Many2one(
        'res.partner.bank',
        string='Customer Bank',
        compute='_compute_customer_bank_id', store=True, readonly=False,
        help="Bank Account Number from which the invoice will be paid. "
             "A Customer bank account if this is a Customer Invoice",
        tracking=True,
    )

    def get_source_orders(self):
        self.ensure_one()
        source_orders = self.line_ids.sale_line_ids.order_id[:1]
        return source_orders

    @api.depends('commercial_partner_id')
    def _compute_bank_customer_id(self):
        for move in self:
            if not move.is_inbound():
                move.bank_customer_id = move.company_id.partner_id
            else:
                move.bank_customer_id = move.commercial_partner_id

    @api.depends('customer_bank_id')
    def _compute_customer_bank_id(self):
        for move in self:
            bank_ids = move.bank_customer_id.bank_ids.filtered(
                lambda bank: not bank.company_id and bank.partner_id == move.commercial_partner_id)
            move.customer_bank_id = bank_ids[0] if bank_ids else False