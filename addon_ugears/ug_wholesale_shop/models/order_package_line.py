from odoo import models, fields, api, _


class DistributorOrderPackageLine(models.Model):
    _name = 'distrib.order.package.line'
    _description = 'Packages orders record lines'
    _rec_names_search = ['name', 'order_id.name']
    _order = 'order_id, cartoon_id asc, id'

    _sql_constraints = [
        ('package_check', 'CHECK(package_qty>0)', 'Minimum 1 package allow')
    ]

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Order Reference",
        required=True, ondelete='cascade', index=True, copy=False)

    sequence = fields.Integer(string="Sequence", default=10)
    cartoon_id = fields.Many2one('distrib.packages.sizes', 'Cartoon', index=True, required=True)

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)

    package_qty = fields.Integer(
        string="Quantity",
        compute='_compute_package_qty',
        digits='Package Unit', default=0,
        store=True, readonly=True, required=True, precompute=True)

    # Order-related fields
    pallet_id = fields.Many2one(
        related='order_id.pallet_id',
        store=True, index=True, precompute=True)
    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True, index=True, precompute=True)
    order_partner_id = fields.Many2one(
        related='order_id.partner_id',
        string="Customer",
        store=True, index=True, precompute=True)
    salesman_id = fields.Many2one(
        related='order_id.user_id',
        string="Salesperson",
        store=True, precompute=True)
    state = fields.Selection(
        related='order_id.state',
        string="Order Status",
        copy=False, store=True, precompute=True)
    date = fields.Datetime(related='order_id.date_order', string="Order Data", store=True, precompute=True)

    @api.depends('cartoon_id')
    def _compute_package_qty(self):
        for line in self:
            line.package_qty = 1

    @api.depends('cartoon_id')
    def _compute_name(self):
        for line in self:
            if not line.cartoon_id:
                continue
            name = line.cartoon_id.type_of + ' - ' + line.cartoon_id.ref
            line.name = name

