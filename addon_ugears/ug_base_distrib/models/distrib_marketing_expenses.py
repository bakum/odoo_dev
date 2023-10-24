from odoo import models, fields, api, _
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
    _description = 'Msrketing Expenses'
    _order = 'date_order desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
        string="Month",
        copy=False, index=True)
    year = fields.Char("Year", store=True, compute='_compute_year')

    def init(self):
        create_index(self._cr, 'distrib_marketing_date_order_id_idx', 'distrib_marketing_expenses',
                     ["date_order desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence_distrib_marketing_exp')
        return super(MarketingExpenses, self).create(vals_list)

    @api.depends('date_order')
    def _compute_year(self):
        for order in self:
            if order.date_order:
                order.year = order.date_order.strftime("%Y")
                order.month = order.date_order.strftime("%B").lower()
