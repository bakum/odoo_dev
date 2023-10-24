import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import create_index

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}
MONTHS = [
    ('january', _('January')),
    ('february', _('February')),
    ('march', _('March')),
    ('april', _('April')),
    ('may', _('May')),
    ('june', _('June')),
    ('july', _('July')),
    ('august', _('August')),
    ('september', _('September')),
    ('october', _('October')),
    ('november', _('November')),
    ('december', _('December')),
]


class MarketingExpenses(models.Model):
    _name = 'distrib.marketing.expenses'
    _description = 'Marketing Expenses'
    _order = 'year desc, month desc, id desc'
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
    month = fields.Selection(
        selection=MONTHS,
        states=LOCKED_FIELD_STATES,
        required=True,
        string="Month", default=_default_month,
        copy=False, index=True, tracking=True)
    year = fields.Char("Year", store=True, tracking=True, compute='_compute_year')
    move_line = fields.One2many(
        comodel_name='distrib.marketing.expenses.line',
        inverse_name='move_id',
        string="Expenses Lines",
        states=LOCKED_FIELD_STATES,
        copy=True)
    amount_untaxed = fields.Monetary(string="Amount", store=True, compute='_compute_amounts')

    def init(self):
        create_index(self._cr, 'distrib_marketing_date_order_id_idx', 'distrib_marketing_expenses',
                     ["year desc, month desc, id desc"])

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

    @api.depends('date_order')
    def _compute_year(self):
        for order in self:
            if order.date_order:
                order.year = order.date_order.strftime("%Y")
                order.month = order.date_order.strftime("%B").lower()

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
