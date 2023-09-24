from odoo import models, fields, api, _


class DistributorMoveLines(models.Model):
    _name = 'distrib.distributors.move.line'
    _description = 'Distributors stock record lines'
    _rec_names_search = ['name', 'move_id.name']
    _order = 'move_id, distrib_id asc, id'

    _sql_constraints = [
        ('quantity_check','CHECK(product_uom_qty>0)','Minimum 1 quantity allow')
    ]

    move_id = fields.Many2one(
        comodel_name='distrib.distributors.move',
        string="Distributor Move Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string="Sequence", default=10)

    # Order-related fields
    distrib_id = fields.Many2one(
        related='move_id.distrib_id',
        store=True, index=True, precompute=True)

    salesman_id = fields.Many2one(
        related='move_id.user_id',
        string="User",
        store=True, precompute=True)
    state = fields.Selection(
        related='move_id.state',
        string="Move Status",
        copy=False, store=True, precompute=True)
    operation = fields.Selection(
        related='move_id.operation',
        string="Move Operation",
        copy=False, store=True, precompute=True)
    display_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)

    # Generic configuration fields
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        required=True,
        domain="[('sale_ok', '=', True)]")

    product_template_id = fields.Many2one(
        string="Product Template",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
        domain=[('sale_ok', '=', True)])

    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])
    product_uom_qty = fields.Float(
        string="Quantity",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=0.0,
        store=True, readonly=False, required=True, precompute=True)
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        required=True,
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="[('category_id', '=', product_uom_category_id)]")

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            name = line.product_id.get_product_multiline_description_sale()
            line.name = name

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]

    @api.depends('product_id')
    def _compute_product_uom_qty(self):
        for line in self:
            line.product_uom_qty = 1.0

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom = line.product_id.uom_id
