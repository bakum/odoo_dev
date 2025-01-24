from odoo import models, fields, _, api
from odoo.exceptions import UserError
from odoo.tools import create_index

LOCKED_FIELD_STATES = {
    state: [('readonly', True)] for state in {'done', 'cancel'}
}


class DistributorSaleBudget(models.Model):
    _name = 'distrib.budget.move'
    _description = 'Distributors sales budget'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Ref', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        states=LOCKED_FIELD_STATES,
        index=True, required=True, tracking=True)
    date = fields.Datetime(
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
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="User",
        states=LOCKED_FIELD_STATES,
        default=lambda self: self.env.user.id,
        readonly=False, index=True, tracking=True
    )
    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)
    year = fields.Char("Year", store=True, tracking=True, compute='_compute_year')
    is_manager = fields.Boolean(compute='_compute_is_manager')
    move_line = fields.One2many(
        comodel_name='distrib.budget.move.line',
        inverse_name='move_id',
        string="Move Lines",
        states=LOCKED_FIELD_STATES,
        copy=True)
    posted_line = fields.One2many(
        comodel_name='distrib.budget.move.line',
        inverse_name='move_id',
        string="Posted Lines",
        states=LOCKED_FIELD_STATES)

    @api.depends_context('uid')
    @api.depends('distrib_id')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")

    @api.depends('date')
    def _compute_year(self):
        for order in self:
            if order.date:
                order.year = order.date.strftime("%Y")
                # order.month = order.date_order.strftime("%B").lower()

    def init(self):
        create_index(self._cr, 'distrib_budget_date_id_idx', 'distrib_budget_move',
                     ["date desc", "id desc"])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('distrib.sale.budget')

        created = super(DistributorSaleBudget, self).create(vals_list)
        if created:
            created.move_line = self._create_move_line()
        return created

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_or_cancel(self):
        for ml in self:
            if ml.state in ('done'):
                raise UserError(_('You can not delete the budget if is done.'))

    def name_get(self):
        # if self._context.get('sale_show_partner_name'):
        res = []
        for order in self:
            name = order.name
            if order.distrib_id.name:
                name = '%s - %s' % (name, order.distrib_id.name)
            res.append((order.id, name))
        return res
        # return super().name_get()

    def _prepare_move_line_value(self, product):
        return {
            'display_type': 'product',
            'product_id': product.id
        }

    def _search_products(self):
        Products = self.env['product.product']
        domain = [('is_published', '=', True)]
        return Products.search(domain)

    def _create_move_line(self):
        products_list = []
        products = self._search_products()
        for product in products:
            products_list.append((0, 0, self._prepare_move_line_value(product)))
        return products_list

    def action_view_budget(self):
        self.ensure_one()
        action = {
            'name': _('Distributor sales plan - %s' % self.name),
            'type': 'ir.actions.act_url',
            'view_mode': 'list,form',
            'res_model': 'distrib.budget.move.line',
            'views': [(self.env.ref('ug_base_distrib.view_distrib_budgets_line_tree').id, 'list'),
                      (False, 'form')],
            'type': 'ir.actions.act_window',
            # 'context': {
            #     'default_order': 'date'
            #     # 'search_default_inventory': 1,
            #     # 'search_default_done': 1,
            #     # 'search_default_product_id': self.product_id.id,
            # },
            'domain': [
                ('move_id', '=', self.id),
                # ('state', '=', 'done'),
                # ('is_inventory', '=', True),
                ('distrib_id', '=', self.distrib_id.id),
            ],
        }
        return action

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})