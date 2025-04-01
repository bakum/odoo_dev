import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import create_index

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class MarketingExpenses(models.Model):
    _name = 'distrib.marketing.expenses'
    _description = 'Marketing Expenses'
    _order = 'year desc, id desc'
    _inherit = ['mail.thread']

    def _default_month(self):
        dt = datetime.datetime.now()
        return dt.strftime("%B").lower()

    # def _default_year(self):
    #     dt = datetime.datetime.now()
    #     return dt.strftime("%Y")

    name = fields.Char('Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
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
    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
        states=LOCKED_FIELD_STATES,
        default=lambda self: self.env.user.id,
        readonly=False, index=True, tracking=True
    )
    month = fields.Datetime(
        string="Month",
        states=LOCKED_FIELD_STATES,
        tracking=True, store=True, compute='_compute_year')
    # month = fields.Selection(
    #     selection=[
    #         ('january', _('January')),
    #         ('february', _('February')),
    #         ('march', _('March')),
    #         ('april', _('April')),
    #         ('may', _('May')),
    #         ('june', _('June')),
    #         ('july', _('July')),
    #         ('august', _('August')),
    #         ('september', _('September')),
    #         ('october', _('October')),
    #         ('november', _('November')),
    #         ('december', _('December')),
    #     ],
    #     states=LOCKED_FIELD_STATES,
    #     required=False,
    #     string="Month",
    #     copy=False, index=True, tracking=True)
    month_str = fields.Char("Month", compute='_compute_year')
    year = fields.Char("Year", store=True, tracking=True, compute='_compute_year')
    move_line = fields.One2many(
        comodel_name='distrib.marketing.expenses.line',
        inverse_name='move_id',
        string="Expenses Lines",
        states=LOCKED_FIELD_STATES,
        copy=True)
    posted_line = fields.One2many(
        comodel_name='distrib.marketing.expenses.line',
        inverse_name='move_id',
        string="Posted Lines",
        states=LOCKED_FIELD_STATES)
    amount_untaxed = fields.Monetary(string="Amount", store=True, compute='_compute_amounts')
    is_manager = fields.Boolean(compute='_compute_is_manager')

    rate = fields.Float(compute='_compute_current_rate', string='Current Cross-Rate', digits=0, store=True,
                        precompute=True, help='The rate of the currency to the currency of accounting')

    @api.depends('currency_id', 'date_order', 'currency_id.rate_ids')
    def _compute_current_rate(self):
        currency_to = self.env['ir.config_parameter'].sudo().get_param('ug_base_distrib.default_currency_accounting',
                                                                       default='0')
        for currency in self:
            if int(currency_to) == 0:
                currency.rate = 1.0
            else:
                currency_to = self.env['res.currency'].sudo().search([('id', '=', int(currency_to))])
                if currency_to:
                    currency.rate = self._get_rate_for_move(currency.currency_id.display_name, currency_to.display_name,
                                                            date=currency.date_order)
                else:
                    currency.rate = 1.0

    @api.model
    def _get_rate_for_move(self, currency_from_code, currency_to_code, date=None):
        if not currency_from_code or not currency_to_code:
            return False
        if currency_from_code == currency_to_code:
            return 1.0
        Currency = self.env["res.currency"].with_context({"active_test": False})
        currency_from = Currency.search([("name", "=", currency_from_code)])
        currency_to = Currency.search([("name", "=", currency_to_code)])
        if not currency_from or not currency_to:
            return 1.0
        company = self.env.company
        date = fields.Date.from_string(date) if date else fields.Date.context_today(self)
        return Currency._get_conversion_rate(currency_from, currency_to, company, date)

    @api.depends_context('uid')
    @api.depends('distrib_id')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")

    def init(self):
        create_index(self._cr, 'distrib_marketing_date_order_id_idx', 'distrib_marketing_expenses',
                     ["year desc, id desc"])

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_or_cancel(self):
        for ml in self:
            if ml.state in ('done'):
                raise UserError(_('You can not delete the moves if is done.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('distrib.marketing.exp')
        return super(MarketingExpenses, self).create(vals_list)

    def write(self, vals):
        restrict_date = fields.Datetime.from_string(
            self.env['ir.config_parameter'].sudo().get_param('distrib.restrict_date', default='1970-01-01 00:00:00')
        )
        for record in self:
            if 'state' in vals and vals['state'] in ('done', 'cancel') and self.date_order <= restrict_date:
                raise UserError(
                    _('You cannot change the state if the date is before the restriction date.'))
        return super(MarketingExpenses, self).write(vals)

    @api.depends('date_order')
    def _compute_year(self):
        for order in self:
            if order.date_order:
                order.year = order.date_order.strftime("%Y")
                first_day = order.date_order.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                order.month_str = order.date_order.strftime("%B").lower()
                order.month = first_day

    @api.depends('move_line.expense_total')
    def _compute_amounts(self):
        for order in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            order_lines = order.move_line
            amount_untaxed = sum(order_lines.mapped('expense_total'))

            order.amount_untaxed = amount_untaxed

    def action_done(self):
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
                    'message': _('Expenses successfully accepted!'),
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
                    'message': _('Error occurred while accepting the expense!'),
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
                    'message': _('Expenses successfully accepted!'),
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
                    'message': _('Error occurred while accepting the expense!'),
                    'sticky': False,
                }
            }
