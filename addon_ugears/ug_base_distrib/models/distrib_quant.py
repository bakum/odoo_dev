from odoo import models, fields, api, _
from odoo.tools import float_compare
from odoo.osv import expression


class DistributorQuant(models.Model):
    _name = 'distrib.quant'
    _description = 'Quants'

    _sql_constraints = [
        (
            'unique_product',
            'unique(product_id, distrib_id)',
            "Cannot Use one distribution's product twice!\nPlease, select a different product or distributor"
        )
    ]

    # def _distrib_readonly(self):
    #     distrib_id = self.user.distrib_id.id
    #     if distrib_id:
    #         return True
    #     return False

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '!=', 'service')]",
        ondelete='restrict', required=True, index=True)

    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        related='product_id.product_tmpl_id')
    product_categ_id = fields.Many2one(related='product_tmpl_id.categ_id')

    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        readonly=True, related='product_id.uom_id')

    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        index=True, required=True,
        help='This is the owner of the quant')
    in_date = fields.Datetime('Incoming Date', readonly=True, required=True, default=fields.Datetime.now)
    quantity = fields.Float(
        'Quantity',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True, digits='Product Unit of Measure')
    # Inventory Fields
    inventory_quantity = fields.Float(
        'Counted Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")
    inventory_quantity_auto_apply = fields.Float(
        'Inventoried Quantity', digits='Product Unit of Measure',
        compute='_compute_inventory_quantity_auto_apply',
        inverse='_set_inventory_quantity',
        # groups='stock.group_stock_manager'
    )
    inventory_diff_quantity = fields.Float(
        'Difference', compute='_compute_inventory_diff_quantity', store=True,
        help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
        readonly=True, digits='Product Unit of Measure')
    inventory_date = fields.Date(
        'Scheduled Date', compute='_compute_inventory_date', store=True, readonly=False,
        help="Next date the On Hand Quantity should be counted.")
    is_manager = fields.Boolean(compute='_compute_is_manager')

    @api.depends_context('uid')
    @api.depends('product_id', 'inventory_quantity')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")

    @api.depends('quantity')
    def _compute_inventory_quantity_auto_apply(self):
        for quant in self:
            quant.inventory_quantity_auto_apply = quant.quantity

    @api.depends('inventory_quantity')
    def _compute_inventory_diff_quantity(self):
        for quant in self:
            quant.inventory_diff_quantity = quant.inventory_quantity - quant.quantity

    @api.model
    def _is_inventory_mode(self):
        """ Used to control whether a quant was written on or created during an
        "inventory session", meaning a mode where we need to create the stock.move
        record necessary to be consistent with the `inventory_quantity` field.
        """
        return self.env.context.get('inventory_mode') and self.user_has_groups('ug_base_distrib.group_distrib_user')

    @api.model
    def _get_removal_strategy(self, product_id):
        # if product_id.categ_id.removal_strategy_id:
        #     return product_id.categ_id.removal_strategy_id.method
        # else:
        return 'fifo'

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'fifo':
            return 'in_date ASC, id'
        else:
            return 'in_date DESC, id DESC'

    def _gather(self, product_id, distrib_id, strict=False):
        removal_strategy = self._get_removal_strategy(product_id)
        removal_strategy_order = self._get_removal_strategy_order(removal_strategy)

        domain = [('product_id', '=', product_id.id)]
        if not strict:
            domain = expression.AND([[('distrib_id', '=', distrib_id.id)], domain])
        else:
            domain = expression.AND([[('distrib_id', '=', distrib_id and distrib_id.id or False)], domain])

        return self.search(domain, order=removal_strategy_order).sorted(lambda q: not q.distrib_id)

    @api.model
    def _update_available_quantity(self, product_id, quantity, distrib_id, in_date=None):
        self = self.sudo()
        quants = self._gather(product_id, distrib_id=distrib_id, strict=True)
        incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                          float_compare(quant.quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0]

        if in_date:
            incoming_dates += [in_date]

        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute(
                "SELECT id FROM distrib_quant WHERE id IN %s ORDER BY distrib_id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED",
                [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])

        if quant:
            quant.write({
                'quantity': quant.quantity + quantity,
                'in_date': in_date,
            })
        else:
            self.create({
                'product_id': product_id.id,
                'quantity': quantity,
                'distrib_id': distrib_id and distrib_id.id,
                'in_date': in_date,
            })
        return self._get_available_quantity(product_id, distrib_id=distrib_id, strict=False,
                                            allow_negative=True), in_date

    @api.model
    def _get_available_quantity(self, product_id, distrib_id, strict=False, allow_negative=False):
        self = self.sudo()
        quants = self._gather(product_id, distrib_id=distrib_id, strict=strict)
        rounding = product_id.uom_id.rounding

        available_quantity = sum(quants.mapped('quantity'))
        if allow_negative:
            return available_quantity
        else:
            return available_quantity if float_compare(available_quantity, 0.0,
                                                       precision_rounding=rounding) >= 0.0 else 0.0

    # TODO: implement a function
    @api.depends('distrib_id')
    def _compute_inventory_date(self):
        pass
