from odoo import models, fields, api, _
from odoo.exceptions import UserError
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
    import_date = fields.Datetime('Date Import', readonly=True, required=False)
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
    last_count_date = fields.Date(compute='_compute_last_count_date', help='Last time the Quantity was Updated')
    inventory_quantity_set = fields.Boolean(store=True, compute='_compute_inventory_quantity_set', readonly=False,
                                            default=False)
    user_id = fields.Many2one(
        'res.users', 'Assigned To', help="User assigned to do product count.")

    currency_id = fields.Many2one(
        related='distrib_id.pricelist_id.currency_id',
        store=True, index=True, precompute=True)
    pricelist_item_id = fields.Many2one(
        comodel_name='product.pricelist.item',
        compute='_compute_pricelist_item_id')
    price_unit = fields.Float(
        string="Unit Price",
        compute='_compute_price_unit',
        digits='Product Price',
        store=True, readonly=False, required=True, precompute=True)
    rate = fields.Float(compute='_compute_current_rate', string='Current Cross-Rate', digits=0, store=True,
                        precompute=True, help='The rate of the currency to the currency of accounting')

    @api.model
    def _get_rate_for_move(self, currency_from_code, currency_to_code, date=None):
        if not currency_from_code or not currency_to_code:
            return False
        if currency_from_code == currency_to_code:
            return 1.0
        Currency = self.env["res.currency"].with_context({"active_test": False})
        currency_from = Currency.search([("name", "=", currency_from_code)])
        currency_to = Currency.search([("name", "=", currency_to_code)])
        if not currency_from or not currency_to:
            return 1.0
        company = self.env.company
        date = fields.Date.from_string(date) if date else fields.Date.context_today(self)
        return Currency._get_conversion_rate(currency_from, currency_to, company, date)

    @api.depends('currency_id', 'in_date','currency_id.rate_ids')
    def _compute_current_rate(self):
        currency_to = self.env['ir.config_parameter'].sudo().get_param('ug_base_distrib.default_currency_accounting',
                                                                       default='0')
        for currency in self:
            if int(currency_to) == 0:
                currency.rate = 1.0
            else:
                currency_to = self.env['res.currency'].sudo().search([('id', '=', int(currency_to))])
                if currency_to:
                    currency.rate = self._get_rate_for_move(currency.currency_id.display_name, currency_to.display_name,
                                                            date=currency.in_date)
                else:
                    currency.rate = 1.0

    @api.depends_context('uid')
    @api.depends('product_id', 'inventory_quantity')
    def _compute_is_manager(self):
        self.is_manager = self.env.user.has_group("ug_base_distrib.group_distrib_manager")

    def _compute_last_count_date(self):
        """ We look at the stock move lines associated with every quant to get the last count date.
        """
        self.last_count_date = False
        groups = self.env['distrib.distributors.move.line']._read_group(
            [
                ('state', '=', 'done'),
                ('is_inventory', '=', True),
                ('product_id', 'in', self.product_id.ids),
                ('distrib_id', 'in', self.distrib_id.ids),
            ],
            ['date:max', 'product_id', 'distrib_id'],
            ['product_id', 'distrib_id'],
            lazy=False)

        def _update_dict(date_by_quant, key, value):
            current_date = date_by_quant.get(key)
            if not current_date or value > current_date:
                date_by_quant[key] = value

        date_by_quant = {}
        for group in groups:
            move_line_date = group['date']
            distrib_id = group['distrib_id'] and group['distrib_id'][0]
            product_id = group['product_id'][0]
            _update_dict(date_by_quant, (product_id, distrib_id), move_line_date)
            # _update_dict(date_by_quant, (location_dest_id, package_id, product_id, lot_id, owner_id), move_line_date)
            # _update_dict(date_by_quant, (location_id, result_package_id, product_id, lot_id, owner_id), move_line_date)
            # _update_dict(date_by_quant, (location_dest_id, result_package_id, product_id, lot_id, owner_id), move_line_date)
        for quant in self:
            quant.last_count_date = date_by_quant.get((quant.product_id.id, quant.distrib_id.id))

    @api.depends('quantity')
    def _compute_inventory_quantity_auto_apply(self):
        for quant in self:
            quant.inventory_quantity_auto_apply = quant.quantity

    @api.depends('inventory_quantity')
    def _compute_inventory_diff_quantity(self):
        for quant in self:
            quant.inventory_diff_quantity = quant.inventory_quantity - quant.quantity

    @api.depends('inventory_quantity')
    def _compute_inventory_quantity_set(self):
        for quant in self:
            quant.inventory_quantity_set = (quant.inventory_quantity - quant.quantity) != 0

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
                'inventory_quantity': quant.quantity + quantity,
                'in_date': in_date,
            })
        else:
            self.create({
                'product_id': product_id.id,
                'quantity': quantity,
                'inventory_quantity': quantity,
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

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Override to set the `inventory_quantity` field if we're in "inventory mode" as well
        as to compute the sum of the `available_quantity` field.
        """
        if 'available_quantity' in fields:
            if 'quantity' not in fields:
                fields.append('quantity')
        if 'inventory_quantity_auto_apply' in fields and 'quantity' not in fields:
            fields.append('quantity')
        result = super(DistributorQuant, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                          orderby=orderby, lazy=lazy)
        for group in result:
            if 'available_quantity' in fields:
                group['available_quantity'] = group['quantity']
            if 'inventory_quantity_auto_apply' in fields:
                group['inventory_quantity_auto_apply'] = group['quantity']
        return result

    def _get_inventory_move_values(self, qty, out=False, date=None):
        self.ensure_one()
        if fields.Float.is_zero(qty, 0, precision_rounding=self.product_uom_id.rounding):
            name = _('Product Quantity Confirmed')
        else:
            name = _('Product Quantity Updated')

        return {
            'name': self.env.context.get('inventory_name') or name,
            'distrib_id': self.distrib_id.id,
            'state': 'done',
            'is_inventory': True,
            'operation': 'out' if out else 'inc',
            'date_order': date if date else fields.Datetime.now(),
            'move_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom_id.id,
                'distrib_id': self.distrib_id.id,
                'product_uom_qty': qty,
                'operation': 'out' if out else 'inc',
            })]
        }

    def action_apply_inventory(self):
        self._apply_inventory()
        self.inventory_quantity_set = False

    def action_view_inventory(self):
        # self = self._set_view_context()
        ctx = dict(self.env.context or {})
        action = {
            'name': _('Inventory Adjustments'),
            'view_mode': 'list',
            'view_id': self.env.ref('ug_base_distrib.view_distributors_quants_tree').id,
            'res_model': 'distrib.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            # 'domain': [('location_id.usage', 'in', ['internal', 'transit'])],
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                </p><p>
                    {} <span class="fa fa-long-arrow-right"/> {}</p>
                """.format(_('Your stock is currently empty'),
                           _('Press the CREATE button to define quantity for each product in your stock or import them from a spreadsheet throughout Favorites'),
                           _('Import')),
        }
        return action

    def _apply_inventory(self):
        move_vals = []
        if not self.inventory_quantity_set:
            raise UserError(_('inventory quantity is not set.'))
        if not self.user_has_groups('ug_base_distrib.group_distrib_user'):
            raise UserError(_('Only a stock manager can validate an inventory adjustment.'))

        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(quant._get_inventory_move_values(quant.inventory_diff_quantity))
            elif float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) < 0:
                move_vals.append(quant._get_inventory_move_values(-quant.inventory_diff_quantity, out=True))
            else:
                self.write({'inventory_quantity': quant.quantity, 'user_id': False})
                self.write({'inventory_diff_quantity': 0})
                return
        moves = self.env['distrib.distributors.move']
        moves.with_context(inventory_mode=False).create(move_vals)
        # moves.action_done()
        self.write({'inventory_quantity': self.quantity, 'user_id': False, 'import_date': False})
        self.write({'inventory_diff_quantity': 0})

    def action_inventory_history(self):
        self.ensure_one()
        action = {
            'name': _('History'),
            'view_mode': 'list,form',
            'res_model': 'distrib.distributors.move.line',
            'views': [(self.env.ref('ug_base_distrib.view_distributors_distrib_move_line_tree').id, 'list'),
                      (False, 'form')],
            'type': 'ir.actions.act_window',
            # 'context': {
            #     'default_order': 'date'
            #     # 'search_default_inventory': 1,
            #     # 'search_default_done': 1,
            #     # 'search_default_product_id': self.product_id.id,
            # },
            'domain': [
                ('product_id', '=', self.product_id.id),
                ('state', '=', 'done'),
                # ('is_inventory', '=', True),
                ('distrib_id', '=', self.distrib_id.id),
            ],
        }
        return action

    def _get_pricelist_price(self):
        """Compute the price given by the pricelist for the given line information.

        :return: the product sales price in the order currency (without taxes)
        :rtype: float
        """
        self.ensure_one()
        self.product_id.ensure_one()

        pricelist_rule = self.pricelist_item_id
        order_date = fields.Date.today()
        product = self.product_id
        qty = 1.0
        uom = self.product_id.uom_id

        price = pricelist_rule._compute_price(
            product, qty, uom, order_date, self.distrib_id.pricelist_id.currency_id)

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

        # base_price = self._get_pricelist_price_before_discount()

        # negative discounts (= surcharge) are included in the display price
        return pricelist_price

    @api.depends('product_id')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if not line.product_uom_id or not line.product_id or not line.distrib_id.pricelist_id:
                line.price_unit = 0.0
            else:
                # price = line.with_company(line.company_id)._get_display_price()
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

    @api.depends('product_id')
    def _compute_pricelist_item_id(self):
        for line in self:
            if not line.product_id or not line.distrib_id.pricelist_id:
                line.pricelist_item_id = False
            else:
                line.pricelist_item_id = line.distrib_id.pricelist_id._get_product_rule(
                    line.product_id,
                    1.0,
                    uom=line.product_uom_id,
                    date=line.in_date,
                )
