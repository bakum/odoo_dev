from odoo import models, fields, api


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'utm.mixin']

    def _compute_bank_beneficiary_id(self):
        default_beneficiary = self.env['ir.config_parameter'].sudo().get_param('distrib.default_beneficiary', default=False)
        return int(default_beneficiary) if default_beneficiary else self.company_id.partner_id.id

    bank_customer_id = fields.Many2one(
        comodel_name='res.partner',
        compute='_compute_bank_customer_id',
        help='Technical field to get the domain on the bank',
    )

    bank_beneficiary_id = fields.Many2one(
        comodel_name='res.partner',
        string='Beneficiary',
        default=_compute_bank_beneficiary_id,
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
    beneficiary_bank_id = fields.Many2one(
        'res.partner.bank',
        string='Beneficiary Bank',
        compute='_compute_beneficiary_bank_id', store=True, readonly=False,
        help="Bank Account Number to which the invoice will be paid. "
             "A Company or bank account if this is a Customer Invoice",
        tracking=True,
    )

    @api.depends('commercial_partner_id', 'company_id')
    def _compute_bank_partner_id(self):
        for move in self:
            if move.is_inbound():
                move.bank_partner_id = move.company_id.partner_id
                move.bank_beneficiary_id = move.company_id.partner_id if not move.bank_beneficiary_id else move.bank_beneficiary_id
            else:
                move.bank_partner_id = move.commercial_partner_id

    @api.depends('bank_partner_id')
    def _compute_partner_bank_id(self):
        for move in self:
            bank_ids = move.bank_partner_id.bank_ids.filtered(
                lambda
                    bank: bank.partner_id == move.company_id.partner_id and bank.currency_id == move.currency_id)
            move.partner_bank_id = bank_ids[0] if bank_ids else False

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
                move.bank_customer_id = move.partner_id

    @api.depends('bank_customer_id')
    def _compute_customer_bank_id(self):
        for move in self:
            bank_ids = move.bank_customer_id.bank_ids.filtered(
                lambda
                    bank: bank.partner_id == move.commercial_partner_id and bank.currency_id == move.currency_id)
            move.customer_bank_id = bank_ids[0] if bank_ids else False

    @api.depends('bank_beneficiary_id')
    def _compute_beneficiary_bank_id(self):
        for move in self:
            bank_ids = move.bank_beneficiary_id.bank_ids.filtered(
                lambda
                    bank: bank.partner_id == move.bank_beneficiary_id and bank.currency_id == move.currency_id)
            move.beneficiary_bank_id = bank_ids[0] if bank_ids else False

    @api.onchange('bank_beneficiary_id')
    def _onchange_bank_beneficiary_id(self):
        self.beneficiary_bank_id = False
