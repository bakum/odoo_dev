from odoo import models, fields, api, _
from odoo.tools import create_index

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class DistributorMove(models.Model):
    _name = 'distrib.distributors.move'
    _description = 'Distributors stock records'
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

    operation = fields.Selection(
        selection=[
            ('inc', _("Income")),
            ('out', _("Expenses")),
        ],
        states=LOCKED_FIELD_STATES,
        required=True,
        string="Operation",
        copy=False, index=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
        states=LOCKED_FIELD_STATES,
        default=lambda self: self.env.user.id,
        readonly=False, index=True, tracking=True
    )
    move_line = fields.One2many(
        comodel_name='distrib.distributors.move.line',
        inverse_name='move_id',
        string="Move Lines",
        states=LOCKED_FIELD_STATES,
        copy=True, auto_join=True)

    def init(self):
        create_index(self._cr, 'distrib_move_date_order_id_idx', 'distrib_distributors_move',
                     ["date_order desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals['operation'] == 'inc':
                vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.in')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.out')
        return super(DistributorMove, self).create(vals_list)

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
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})
