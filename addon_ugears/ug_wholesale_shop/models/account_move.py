from odoo import models, fields, api
import re

from odoo.tools import float_round, formatLang


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'utm.mixin']

    def _compute_bank_beneficiary_id(self):
        default_beneficiary = self.env['ir.config_parameter'].sudo().get_param('distrib.default_beneficiary',
                                                                               default=False)
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

    date_facture = fields.Date(
        string="Invoice date",
        required=False, readonly=False, copy=False,
        tracking=True)

    number_facture = fields.Char('Invoice number', required=False, readonly=False, copy=False,
                                 tracking=True)

    amount_qty = fields.Float(string="Total quantity",
                              store=True, compute='_compute_quantity_amount')
    
    source_order_name = fields.Char(
        string="Source Order",
        compute='_compute_source_order_name',
        store=True,
        readonly=True,
        help="Source sales order number"
    )

    delivery_note_order = fields.Char(
        string='Order',
        copy=False,
        tracking=True,
        help='Order reference printed on the Delivery Note',
    )
    delivery_note_shipping_date = fields.Date(
        string='Shipping Date',
        copy=False,
        tracking=True,
        help='Shipping date printed on the Delivery Note',
    )
    delivery_note_carrier = fields.Char(
        string='Carrier',
        copy=False,
        tracking=True,
        help='Carrier printed on the Delivery Note',
    )

    @api.depends('invoice_line_ids.quantity')
    def _compute_quantity_amount(self):
        for move in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            move_lines = move.invoice_line_ids
            amount_qty = sum(move_lines.mapped('quantity'))

            move.amount_qty = amount_qty
    
    @api.depends('line_ids.sale_line_ids.order_id')
    def _compute_source_order_name(self):
        for move in self:
            source_order = move.get_source_orders()
            move.source_order_name = source_order.name if source_order else False

    def format_amount(self, amount, currency=None):
        """Форматирует сумму с валютой."""
        self.ensure_one()
        currency = currency or self.currency_id
        return formatLang(self.env, amount, currency_obj=currency)

    def is_internal_invoice(self):
        if self.partner_id and self.bank_beneficiary_id:
            if self.partner_id.country_id and self.bank_beneficiary_id.country_id:
                return self.partner_id.country_id == self.bank_beneficiary_id.country_id
        return False

    def get_invoice_totals(self):
        self.ensure_one()
        precision = 2  # или взять из валюты: self.currency_id.decimal_places
        total_wo_vat = float_round(self.amount_total, precision_digits=precision)
        vat = float_round(total_wo_vat * self.partner_id.vat_value / 100, precision_digits=precision)
        total_w_vat = float_round(total_wo_vat + vat, precision_digits=precision)

        return {
            'total_wo_vat': total_wo_vat,
            'vat': vat,
            'total_w_vat': total_w_vat,
            'vat_value': self.partner_id.vat_value,
        }

    def migrate_invoice_prefix(self, old_prefix='INV/', new_prefix='PI/'):
        # убедимся, что это строки
        old_prefix = str(old_prefix)
        new_prefix = str(new_prefix)

        moves = self.search([
            ('move_type', '=', 'out_invoice'),
            ('name', 'like', old_prefix + '%'),
            ('state', '!=', 'cancel'),
        ])

        pattern = re.compile(rf'^{re.escape(old_prefix)}(?P<rest>.+)$')
        count = 0

        for move in moves:
            m = pattern.match(move.name)
            if not m:
                continue

            new_name = new_prefix + m.group('rest')
            move.name = new_name
            move.sequence_prefix = new_prefix
            count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Migration complete",
                'message': f"{count} invoices updated from {old_prefix} to {new_prefix}",
                'sticky': False,
            }
        }

    @api.onchange('number_facture')
    def onchange_number_facture(self):
        for vals in self:
            vals.payment_reference = vals['number_facture'] if vals[
                'number_facture'] else vals._get_invoice_computed_reference()

    def convert_invoice_to_proforma(self):
        """
        Преобразует номер из INV/... в PI/...
        """
        # if self.name.startswith("INV/"):
        #     return self.name.replace("INV/", "PI/", 1)
        # return self.name
        return self.source_order_name

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

    @api.depends('bank_customer_id', 'currency_id')
    def _compute_customer_bank_id(self):
        for move in self:
            # Не пересчитываем, если уже есть значение и bank_customer_id не менялся
            if move.customer_bank_id and move.customer_bank_id.partner_id == move.bank_customer_id:
                continue
            
            bank_ids = move.bank_customer_id.bank_ids.filtered(
                lambda
                    bank: bank.partner_id == move.commercial_partner_id and bank.currency_id == move.currency_id)
            move.customer_bank_id = bank_ids[0] if bank_ids else False

    @api.depends('bank_beneficiary_id', 'currency_id')
    def _compute_beneficiary_bank_id(self):
        for move in self:
            # Не пересчитываем, если уже есть значение и bank_beneficiary_id не менялся
            if move.beneficiary_bank_id and move.beneficiary_bank_id.partner_id == move.bank_beneficiary_id:
                continue
            
            bank_ids = move.bank_beneficiary_id.bank_ids.filtered(
                lambda
                    bank: bank.partner_id == move.bank_beneficiary_id and bank.currency_id == move.currency_id)
            move.beneficiary_bank_id = bank_ids[0] if bank_ids else False

    @api.onchange('bank_beneficiary_id')
    def _onchange_bank_beneficiary_id(self):
        self.beneficiary_bank_id = False

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        return []

    def api_generate_invoice_pdf(self, is_factura=True, **kwargs):
        return {
            "report_pdf": True,
            "report_xmlid": "ug_wholesale_shop.action_report_distrib_invoice" if not is_factura else "ug_wholesale_shop.action_report_distrib_invoice_factura",  # xml_id отчета
            "ids": self.ids,
            "filename": f"invoice_{self.id}.pdf"
        }
