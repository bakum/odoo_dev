from odoo import models, fields, api, _


class DistributorMoveLines(models.Model):
    _name = 'distrib.distributors.move.line'
    _description = 'Distributors stock record lines'
    _rec_names_search = ['name', 'move_id.name']
    _order = 'move_id, distrib_id asc, id'

    _sql_constraints = [
        ('quantity_check', 'CHECK(product_uom_qty>0)', 'Minimum 1 quantity allow')
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

    currency_id = fields.Many2one(
        related='move_id.distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)

    date = fields.Datetime(related='move_id.date_order', string="Move Data", store=True, precompute=True)
    salesman_id = fields.Many2one(
        related='move_id.user_id',
        string="User",
        store=True, precompute=True)
    state = fields.Selection(
        related='move_id.state',
        string="Move Status",
        copy=False, store=True, precompute=True)
    is_inventory = fields.Boolean(
        related='move_id.is_inventory',
        string="Inventory",
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

    product_category_id = fields.Many2one(related='product_id.categ_id', copy=False, store=True, precompute=True,
                                          depends=['product_id'])
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
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure', required=True, domain="[('category_id', '=', product_uom_category_id)]",
        compute="_compute_product_uom_id", store=True, readonly=False, precompute=True,
    )
    product_no_variant_attribute_value_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        relation='distrib_attribute_value_ids',
        string="Extra Values",
        compute='_compute_no_variant_attribute_values',
        store=True, readonly=False, precompute=True, ondelete='restrict')
    balance = fields.Float(
        string='Balance',
        compute='_compute_balance', store=True, readonly=False, precompute=True,
    )
    debit = fields.Float(
        string='Debit',
        compute='_compute_debit_credit', store=True, readonly=False, precompute=True,
    )
    credit = fields.Float(
        string='Credit',
        compute='_compute_debit_credit', store=True, readonly=False, precompute=True,
    )
    # Tech field caching pricelist rule used for price & discount computation
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        compute='_compute_pricelist_item_id')

    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        digits='Product Price',
        store=True, readonly=False, required=True, precompute=True)

    price_total = fields.Monetary(
        string="Total",
        compute='_compute_amount',
        store=True, precompute=True)

    @api.depends('product_uom_id.category_id', 'product_id.uom_id.category_id', 'product_id.uom_id')
    def _compute_product_uom_id(self):
        for line in self:
            if not line.product_uom_id or line.product_uom_id.category_id != line.product_id.uom_id.category_id:
                line.product_uom_id = line.product_id.uom_id.id

    @api.model_create_multi
    def create(self, vals_list):
        mls = super().create(vals_list)

        for ml, vals in zip(mls, vals_list):
            if ml.state == 'done':
                if ml.product_id.type != 'service':
                    Quant = self.env['distrib.quant']
                    quantity = ml.product_uom_id._compute_quantity(ml.balance, ml.product_id.uom_id,
                                                                   rounding_method='HALF-UP')
                    # in_date = None
                    # available_qty, in_date = Quant._update_available_quantity(ml.product_id, quantity,
                    #                                                           distrib_id=ml.distrib_id)
                    Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id)
                    # Quant._update_available_quantity(ml.product_id, quantity, distrib_id=ml.distrib_id, in_date=in_date)

        return mls

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

    @api.depends('operation', 'product_uom_qty')
    def _compute_balance(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note'):
                line.balance = False
            elif line.operation == 'out':
                line.balance = -line.product_uom_qty
            else:
                # Only act as a default value when none of balance/debit/credit is specified
                # balance is always the written field because of `_sanitize_vals`
                line.balance = line.product_uom_qty

    @api.depends('balance')
    def _compute_debit_credit(self):
        for line in self:
            line.debit = line.balance if line.balance > 0.0 else 0.0
            line.credit = -line.balance if line.balance < 0.0 else 0.0

    @api.depends('product_id')
    def _compute_no_variant_attribute_values(self):
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = line.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
            # remove the no_variant attributes that don't belong to this template
            for ptav in line.product_no_variant_attribute_value_ids:
                if ptav._origin not in valid_values:
                    line.product_no_variant_attribute_value_ids -= ptav

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_pricelist_item_id(self):
        for line in self:
            if not line.product_id or not line.distrib_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                line.pricelist_item_id = line.distrib_id.pricelist_id._get_product_rule(
                    line.product_id,
                    line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.move_id.date_order,
                )

    def _get_product_price_context(self):
        """Gives the context for product price computation.

        :return: additional context to consider extra prices from attributes in the base product price.
        :rtype: dict
        """
        self.ensure_one()
        res = {}

        # It is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in self.product_id.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            res['no_variant_attributes_price_extra'] = tuple(no_variant_attributes_price_extra)

        return res

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        pricelist_rule = self.pricelist_item_id
        order_date = self.move_id.date_order or fields.Date.today()
        product = self.product_id.with_context(**self._get_product_price_context())
        qty = self.product_uom_qty or 1.0
        uom = self.product_uom or self.product_id.uom_id

        price = pricelist_rule._compute_price(
            product, qty, uom, order_date, self.distrib_id.pricelist_id.currency_id)

        return price

    def _get_pricelist_price_before_discount(self):
        """Compute the price used as base for the pricelist price computation.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        pricelist_rule = self.pricelist_item_id
        order_date = self.move_id.date_order or fields.Date.today()
        product = self.product_id.with_context(**self._get_product_price_context())
        qty = self.product_uom_qty or 1.0
        uom = self.product_uom

        if pricelist_rule:
            pricelist_item = pricelist_rule
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                # Find the lowest pricelist rule whose pricelist is configured
                # to show the discount to the customer.
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    rule_id = pricelist_item.base_pricelist_id._get_product_rule(
                        product, qty, uom=uom, date=order_date)
                    pricelist_item = self.env['product.pricelist.item'].browse(rule_id)

            pricelist_rule = pricelist_item

        price = pricelist_rule._compute_base_price(
            product,
            qty,
            uom,
            order_date,
            target_currency=self.distrib_id.pricelist_id.currency_id,
        )

        return price

    def _get_display_price(self):
        """Compute the displayed unit price for a given line.

        Overridden in custom flows:
        * where the price is not specified by the pricelist
        * where the discount is not specified by the pricelist

        Note: self.ensure_one()
        """
        self.ensure_one()

        pricelist_price = self._get_pricelist_price()

        if self.distrib_id.pricelist_id.discount_policy == 'with_discount':
            return pricelist_price

        if not self.pricelist_item_id:
            # No pricelist rule found => no discount from pricelist
            return pricelist_price

        base_price = self._get_pricelist_price_before_discount()

        # negative discounts (= surcharge) are included in the display price
        return max(base_price, pricelist_price)

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if not line.product_uom or not line.product_id or not line.distrib_id.pricelist_id:
                line.price_unit = 0.0
            else:
                #price = line.with_company(line.company_id)._get_display_price()
                price = line._get_display_price()
                line.price_unit = price
                # line.price_unit = line.product_id._get_tax_included_unit_price(
                #     line.company_id,
                #     line.order_id.currency_id,
                #     line.order_id.date_order,
                #     'sale',
                #     fiscal_position=line.order_id.fiscal_position_id,
                #     product_price_unit=price,
                #     product_currency=line.currency_id
                # )

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_total = line.price_unit * line.product_uom_qty
