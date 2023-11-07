from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import create_index

# LOCKED_FIELD_STATES = {
#     state: [('readonly', True)]
#     for state in {'done', 'cancel'}
# }


class DistributorMove(models.Model):
    _name = 'distrib.distributors.move'
    _description = 'Distributors stock records'
    _order = 'date_order desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
      #  states=LOCKED_FIELD_STATES,
        index=True, required=True, tracking=True)

    date_order = fields.Datetime(
        string="Operation Date",
       # states=LOCKED_FIELD_STATES,
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
       # states=LOCKED_FIELD_STATES,
        required=True,
        string="Operation",
        copy=True, index=True)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
       # states=LOCKED_FIELD_STATES,
        default=lambda self: self.env.user.id,
        readonly=False, index=True, tracking=True
    )
    channel_id = fields.Many2one(
        comodel_name='distrib.sales.channels',
        string="Sales Channel",
       # states=LOCKED_FIELD_STATES,
        readonly=False, index=True, tracking=True
    )
    move_line = fields.One2many(
        comodel_name='distrib.distributors.move.line',
        inverse_name='move_id',
        string="Move Lines",
       # states=LOCKED_FIELD_STATES,
        copy=True)

    posted_line = fields.One2many(
        comodel_name='distrib.distributors.move.line',
        inverse_name='move_id',
        # states=LOCKED_FIELD_STATES,
        string="Posted Lines"
       )

    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)

    amount_untaxed = fields.Monetary(string="Amount", store=True, compute='_compute_amounts')
    is_inventory = fields.Boolean('Inventory', default=False)
    is_manager = fields.Boolean(compute='_compute_is_manager')

    @api.depends_context('uid')
    @api.depends('operation', 'distrib_id')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")

    def init(self):
        create_index(self._cr, 'distrib_move_date_order_id_idx', 'distrib_distributors_move',
                     ["date_order desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'operation' in list(vals.keys()):
                if 'is_inventory' in list(vals.keys()) and vals['is_inventory']:
                    vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.adj')
                elif vals['operation'] == 'inc':
                    vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.in')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('distrib.distributors.move.out')
        return super(DistributorMove, self).create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            mls = self.move_line
            for ml in mls:
                if vals['state'] == 'done':
                    if ml.product_id.type != 'service':
                        Quant = self.env['distrib.quant']
                        quantity = ml.product_uom_id._compute_quantity(ml.balance, ml.product_id.uom_id,
                                                                       rounding_method='HALF-UP')
                        # in_date = None
                        # available_qty, in_date = Quant._update_available_quantity(ml.product_id, quantity,
                        #                                                           distrib_id=ml.distrib_id)
                        Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id)
                        # Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id, in_date=in_date)
                elif vals['state'] == 'cancel':
                    if ml.product_id.type != 'service':
                        Quant = self.env['distrib.quant']
                        quantity = ml.product_uom_id._compute_quantity(ml.balance, ml.product_id.uom_id,
                                                                       rounding_method='HALF-UP')
                        # in_date = None
                        # available_qty, in_date = Quant._update_available_quantity(ml.product_id, quantity,
                        #                                                           distrib_id=ml.distrib_id)
                        Quant._update_available_quantity(ml.product_id, -quantity, distrib_id=ml.distrib_id)
                        # Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id, in_date=in_date)

        res = super(DistributorMove, self).write(vals)

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
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.depends('move_line.price_total')
    def _compute_amounts(self):
        for order in self:
            # order_lines = order.move_line.filtered(lambda x: not x.display_type)
            order_lines = order.move_line
            amount_untaxed = sum(order_lines.mapped('price_total'))

            order.amount_untaxed = amount_untaxed
