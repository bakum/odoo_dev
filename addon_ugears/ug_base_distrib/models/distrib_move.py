from odoo import models, fields, api, _
from odoo.tools import create_index


class DistributorMove(models.Model):
    _name = 'distrib.distributors.move'
    _description = 'Distributors stock records'
    _order = 'date_order desc, id desc'

    name = fields.Char('Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        index=True, required=True)

    date_order = fields.Datetime(
        string="Order Date",
        required=True, readonly=False, copy=False,
        default=fields.Datetime.now)

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
            ('adjustements', _("Adjustements")),
            ('inc', _("Income")),
            ('out', _("Expenses")),
        ],
        required=True,
        string="Operation",
        copy=False, index=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        default=lambda self: self.env.user.id,
        readonly=False, index=True
    )

    def init(self):
        create_index(self._cr, 'distrib_move_date_order_id_idx', 'distrib_distributors_move', ["date_order desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals['operation'] == 'adjustements':
                vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.adj')
            elif  vals['operation'] == 'inc':
                vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.in')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.out')
        return super(DistributorMove, self).create(vals_list)
