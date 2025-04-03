from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import create_index

import time
import threading

import logging
_logger = logging.getLogger(__name__)

LOCKED_FIELD_STATES = {
    state: [('readonly', True)] for state in {'done', 'cancel'}
}


class DistributorMove(models.Model):
    _name = 'distrib.distributors.move'
    _description = 'Distributors stock records'
    _order = 'date_order desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Ref', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        states=LOCKED_FIELD_STATES,
        index=True, required=True, tracking=True)

    date_order = fields.Datetime(
        string="Operation Date",
        states=LOCKED_FIELD_STATES,
        required=True, readonly=False, copy=False,
        default=fields.Datetime.now, tracking=True)

    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('done', "Locked"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        default='draft')

    operation = fields.Selection(
        selection=[
            ('inc', _("Income")),
            ('out', _("Expenses")),
        ],
        states=LOCKED_FIELD_STATES,
        required=True,
        string="Operation",
        copy=True, index=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
        states=LOCKED_FIELD_STATES,
        default=lambda self: self.env.user.id,
        readonly=False, index=True, tracking=True
    )
    channel_id = fields.Many2one(
        comodel_name='distrib.sales.channels',
        string="Sales Channel",
        states=LOCKED_FIELD_STATES,
        readonly=False, index=True, tracking=True
    )
    move_line = fields.One2many(
        comodel_name='distrib.distributors.move.line',
        inverse_name='move_id',
        string="Move Lines",
        states=LOCKED_FIELD_STATES,
        copy=True)

    posted_line = fields.One2many(
        comodel_name='distrib.distributors.move.line',
        inverse_name='move_id',
        string="Posted Lines",
        states=LOCKED_FIELD_STATES)

    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)

    amount_untaxed = fields.Monetary(
        string="Amount", store=True, compute='_compute_amounts')
    amount_qty = fields.Float(string="Total quantity",
                              store=True, compute='_compute_quantity_amount')
    is_inventory = fields.Boolean('Inventory', default=False)
    is_manager = fields.Boolean(compute='_compute_is_manager')
    rate = fields.Float(compute='_compute_current_rate', string='Current Cross-Rate', digits=0, store=True,
                        precompute=True, help='The rate of the currency to the currency of accounting')

    discount_total = fields.Monetary(
        compute="_compute_discount_total",
        string="Discount Subtotal",
        currency_field="currency_id",
        store=True,
    )
    price_total_no_discount = fields.Monetary(
        compute="_compute_discount_total",
        string="Subtotal Without Discount",
        currency_field="currency_id",
        store=True,
    )

    def apply_discount_if_needed(self):
        if self.state != 'done':
            self._apply_discount_if_needed()

    def _apply_discount_if_needed(self):
        self.ensure_one()
        if self.operation == 'out':
            return
        discount_setting = self.env.user.has_group('product.group_discount_per_so_line')
        if not discount_setting:
            return

        distrib_id = self.distrib_id
        if not distrib_id.discount_available:
            return
        if self.price_total_no_discount < distrib_id.discount_after:
            self.move_line.update({'discount' : 0})
        else:
            for line in self.move_line:
                Rules = self.env['distrib.discount.rules']
                excluded = Rules._excluded_position(line)
                if excluded:
                    line.update({'discount': 0})
                    continue
                line.update({'discount': distrib_id.discount_value})
            # self.move_line.update({'discount' : distrib_id.discount_value})

    @api.depends("move_line.discount_total", "move_line.price_total_no_discount")
    def _compute_discount_total(self):
        for order in self:
            discount_total = sum(order.move_line.mapped("discount_total"))
            price_total_no_discount = sum(
                order.move_line.mapped("price_total_no_discount")
            )
            order.update(
                {
                    "discount_total": discount_total,
                    "price_total_no_discount": price_total_no_discount,
                }
            )

    @api.depends('move_line.product_uom_qty')
    def _compute_quantity_amount(self):
        for order in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            order_lines = order.move_line
            amount_qty = sum(order_lines.mapped('product_uom_qty'))

            order.amount_qty = amount_qty

    @api.model
    def _get_rate_for_move(self, currency_from_code, currency_to_code, date=None):
        if not currency_from_code or not currency_to_code:
            return False
        if currency_from_code == currency_to_code:
            return 1.0
        Currency = self.env["res.currency"].with_context(
            {"active_test": False})
        currency_from = Currency.search([("name", "=", currency_from_code)])
        currency_to = Currency.search([("name", "=", currency_to_code)])
        if not currency_from or not currency_to:
            return 1.0
        company = self.env.company
        date = fields.Date.from_string(
            date) if date else fields.Date.context_today(self)
        return Currency._get_conversion_rate(currency_from, currency_to, company, date)

    @api.depends('currency_id', 'date_order', 'currency_id.rate_ids')
    def _compute_current_rate(self):
        currency_to = self.env['ir.config_parameter'].sudo().get_param('ug_base_distrib.default_currency_accounting',
                                                                       default='0')
        for currency in self:
            if int(currency_to) == 0:
                currency.rate = 1.0
            else:
                currency_to = self.env['res.currency'].sudo().search(
                    [('id', '=', int(currency_to))])
                if currency_to:
                    currency.rate = self._get_rate_for_move(currency.currency_id.display_name, currency_to.display_name,
                                                            date=currency.date_order)
                else:
                    currency.rate = 1.0

    @api.onchange('channel_id')
    def _on_change_channel(self):
        if self.move_line:
            for move in self.move_line:
                if not move.channel_id:
                    move.channel_id = self.channel_id

    @api.depends_context('uid')
    @api.depends('operation', 'distrib_id')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group(
            "ug_base_distrib.group_distrib_manager")

    def init(self):
        create_index(self._cr, 'distrib_move_date_order_id_idx', 'distrib_distributors_move',
                     ["date_order desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'operation' in list(vals.keys()):
                if 'is_inventory' in list(vals.keys()) and vals['is_inventory']:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'distrib.distributors.move.adj')
                elif vals['operation'] == 'inc':
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'distrib.distributors.move.in')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'distrib.distributors.move.out')
            # if 'channel_id' in list(vals.keys()):
            #     mls = vals['move_line'][0][2]
            #     if 'channel_id' in mls:
            #         if not mls['channel_id'] and vals['channel_id']:
            #             mls['channel_id'] = vals['channel_id']
        return super(DistributorMove, self).create(vals_list)

    def write(self, vals):
        restrict_date_str = self.env['ir.config_parameter'].sudo().get_param('distrib.restrict_date', default='1970-01-01 00:00:00')
        restrict_date = fields.Datetime.from_string(restrict_date_str)
        context = dict(self.env.context or {})
        recalc_totals = context.get('recalc_totals', False)
        if 'state' in vals:
            mls = self.move_line
            for ml in mls:
                if vals['state'] == 'done':
                    if self.date_order <= restrict_date:
                        raise UserError(_('You cannot change the state if the date is before the restriction date.'))
                    if ml.product_id.type != 'service':
                        Quant = self.env['distrib.quant']
                        quantity = ml.product_uom_id._compute_quantity(ml.balance, ml.product_id.uom_id,
                                                                       rounding_method='HALF-UP')
                        # in_date = None
                        # available_qty, in_date = Quant._update_available_quantity(ml.product_id, quantity,
                        #                                                           distrib_id=ml.distrib_id)
                        Quant._update_available_quantity(
                            ml.product_id, quantity, distrib_id=ml.distrib_id)
                        # Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id, in_date=in_date)
                        QuantHistory = self.env['distrib.quant.history']
                        QuantHistory.with_context(recalc_totals=recalc_totals)._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id,
                                                                                                          in_out=ml.operation,
                                                                                                          in_date=ml.date, is_inventory=ml.is_inventory)
                elif vals['state'] == 'cancel':
                    if self.date_order <= restrict_date:
                        raise UserError(_('You cannot change the state if the date is before the restriction date.'))
                    if ml.product_id.type != 'service':
                        Quant = self.env['distrib.quant']
                        quantity = ml.product_uom_id._compute_quantity(ml.balance, ml.product_id.uom_id,
                                                                       rounding_method='HALF-UP')
                        # in_date = None
                        # available_qty, in_date = Quant._update_available_quantity(ml.product_id, quantity,
                        #                                                           distrib_id=ml.distrib_id)
                        Quant._update_available_quantity(
                            ml.product_id, -quantity, distrib_id=ml.distrib_id)
                        # Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id, in_date=in_date)
                        QuantHistory = self.env['distrib.quant.history']
                        QuantHistory.with_context(recalc_totals=recalc_totals)._update_available_quantity(ml.product_id, -quantity, distrib_id=ml.distrib_id,
                                                                                                          in_out=ml.operation,
                                                                                                          in_date=ml.date, is_inventory=ml.is_inventory)
            # if vals['state'] in ['done','cancel']:
            #     if self.date_order <= restrict_date:
            #         raise UserError(_('You cannot change the state if the date is before the restriction date.'))
            #     mls._recompute_related_beginning_stock()
        if 'channel_id' in vals:
            if self.date_order <= restrict_date:
                raise UserError(_('You cannot change the state if the date is before the restriction date.'))
            mls = self.move_line
            for ml in mls:
                if not ml.channel_id and vals['channel_id']:
                    ml.channel_id = vals['channel_id']

        res = super(DistributorMove, self).write(vals)

        if recalc_totals:
            self._run_recalculate_job(thread=True)

        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_or_cancel(self):
        for ml in self:
            if ml.state in ('done'):
                raise UserError(_('You can not delete the moves if is done.'))

    def name_get(self):
        if self._context.get('sale_show_partner_name'):
            res = []
            for order in self:
                name = order.name
                if order.distrib_id.name:
                    name = '%s - %s' % (name, order.distrib_id.name)
                res.append((order.id, name))
            return res
        return super().name_get()

    def action_done(self):
        self._apply_discount_if_needed()
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_done_multi(self):
        moves = []
        # context = dict(self.env.context or {})
        # recalc_totals = context.get('recalc_totals', False)
        for order in self:
            if order.state == 'draft':
                res = order.write({'state': 'done'})
                if res:
                    moves.append(order)

        if len(moves) > 0:
            # if not recalc_totals:
            #     self._run_recalculate_job(thread=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('Move successfully accepted!'),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Warning!'),
                    'message': _('Error occurred while accepting the move!'),
                    'sticky': False,
                }
            }
    def action_cancel_multi(self):
        moves = []
        # context = dict(self.env.context or {})
        # recalc_totals = context.get('recalc_totals', False)
        for order in self:
            if order.state == 'done':
                res = order.write({'state': 'cancel'})
                if res:
                    moves.append(order)

        if len(moves) > 0:
            # if not recalc_totals:
            #     self._run_recalculate_job(thread=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('Move successfully accepted!'),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Warning!'),
                    'message': _('Error occurred while accepting the move!'),
                    'sticky': False,
                }
            }

    def action_repost(self):
        moves = []
        for order in self:
            if order.state == 'done':
                res = order.write({'state': 'cancel'})
                if res:
                    reposted = order.write({'state': 'done'})
                    if reposted:
                        moves.append(order)
        if len(moves) > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('Move successfully reposted!'),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': _('Warning!'),
                    'message': _('Error occurred while reposting the move!'),
                    'sticky': False,
                }
            }

    @api.depends('move_line.price_total')
    def _compute_amounts(self):
        for order in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            order_lines = order.move_line
            amount_untaxed = sum(order_lines.mapped('price_total'))

            order.amount_untaxed = amount_untaxed

    def _recalculate_thread_job(self):
        time.sleep(3)
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            by_days = self.env['distrib.quant.history'].with_env(
                self.env(cr=new_cr)).sudo()
            _logger.info("job %s starting", 'by_days')
            by_days._recalculate_totals_by_days()
            _logger.info("job %s updated and released", 'by_days')
            new_cr.commit()
           
            by_months = self.env['distrib.quant.totals'].with_env(
                self.env(cr=new_cr)).sudo()
            _logger.info("job %s starting", 'by_months')
            by_months._recalculate_totals_by_monts()
            _logger.info("job %s updated and released", 'by_months')
            new_cr.commit()
            
            new_cr.close()
            return {}

    def run_recalculate_job(self, thread=True):
        self._run_recalculate_job(thread)

    def run_recalculate_job_once_month(self):
        self._run_recalculate_job_no_thread_once_by_month()

    def _run_recalculate_job(self, thread=True):
        if thread:
            threaded_calculation = threading.Thread(
                target=self._recalculate_thread_job)
            threaded_calculation.start()
        else:
            self._run_recalculate_job_no_thread()

    def _run_recalculate_job_no_thread(self):
        by_days = self.env['distrib.quant.history']
        by_months = self.env['distrib.quant.totals']
        _logger.info("posting %s starting", 'by_days')
        # by_days._invalidate_last_records()
        # self._cr.commit()

        by_days._recalculate_totals_by_days()
        _logger.info("posting %s updated and released", 'by_days')
        self._cr.commit()

        _logger.info("posting %s starting", 'by_months')
        by_months._recalculate_totals_by_monts()
        _logger.info("posting %s updated and released", 'by_months')
        return {}

    def _run_recalculate_job_no_thread_once_by_month(self):
        by_days = self.env['distrib.quant.history']
        by_months = self.env['distrib.quant.totals']
        _logger.info("posting %s starting", 'by_days')
        # by_days._invalidate_last_records()
        # self._cr.commit()

        by_days._recalculate_totals_by_days()
        _logger.info("posting %s updated and released", 'by_days')
        self._cr.commit()

        _logger.info("posting %s starting", 'by_months')
        by_months._recalculate_totals_by_monts(begin_of_month=True)
        _logger.info("posting %s updated and released", 'by_months')
        return {}
