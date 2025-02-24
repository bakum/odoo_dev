from odoo.tools import create_index
from odoo.osv import expression
from odoo import models, fields, api
from datetime import timedelta


class DistributorQuantHistory(models.Model):
    _name = 'distrib.quant.history'
    _description = 'Quants History'
    _order = 'distrib_id, product_id, date desc'

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

    date = fields.Datetime('Incoming Date', readonly=True,
                           index=True, required=True, default=fields.Datetime.today)

    quantity_begin = fields.Float(
        'Beginning Quantity',
        readonly=True, compute='_compute_quantity_begin', store=True, precompute=True)
    quantity_income = fields.Float(
        'Incoming Quantity',
        readonly=True)
    quantity_outcome = fields.Float(
        'Outcoming Quantity',
        readonly=True)
    quantity_end = fields.Float(
        'Ending Quantity',
        readonly=True, compute='_compute_quantity_begin', store=True, precompute=True)
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

    valid_rec = fields.Boolean(
        'Record is valid', readonly=True, required=True, default=False)

    def init(self):
        create_index(self._cr, 'distrib_quant_history_date_idx', 'distrib_quant_history',
                     ["distrib_id, product_id, date desc"])
        create_index(self._cr, 'distrib_quant_history_date_asc_idx', 'distrib_quant_history',
                     ["distrib_id, product_id, date"])
        create_index(self._cr, 'distrib_quant_history_distrib_product_idx', 'distrib_quant_history',
                     ["distrib_id, product_id"])

    @api.model
    def _get_rate_for_move(self, currency_from_code, currency_to_code, date=None):
        if not currency_from_code or not currency_to_code:
            return False
        if currency_from_code == currency_to_code:
            return 1.0
        Currency = self.env["res.currency"].with_context(
            {"active_test": False})
        currency_from = Currency.search([("name", "=", currency_from_code)])
        currency_to = Currency.search([("name", "=", currency_to_code)])
        if not currency_from or not currency_to:
            return 1.0
        company = self.env.company
        date = fields.Date.from_string(
            date) if date else fields.Date.context_today(self)
        return Currency._get_conversion_rate(currency_from, currency_to, company, date)

    @api.depends('currency_id', 'date', 'currency_id.rate_ids')
    def _compute_current_rate(self):
        currency_to = self.env['ir.config_parameter'].sudo().get_param('ug_base_distrib.default_currency_accounting',
                                                                       default='0')
        for currency in self:
            if int(currency_to) == 0:
                currency.rate = 1.0
            else:
                currency_to = self.env['res.currency'].sudo().search(
                    [('id', '=', int(currency_to))])
                if currency_to:
                    currency.rate = self._get_rate_for_move(currency.currency_id.display_name, currency_to.display_name,
                                                            date=currency.date)
                else:
                    currency.rate = 1.0

    @api.depends('product_id', 'distrib_id', 'date', 'quantity_income', 'quantity_outcome')
    def _compute_quantity_begin(self):
        for record in self:
            prev = self.env['distrib.quant.history']
            domain = [('distrib_id', '=', record.distrib_id.id), ('product_id', '=', record.product_id.id),
                      ('date', '<', record.date)]
            rec = prev.search(domain, order='date desc', limit=1)
            if rec:
                record.quantity_begin = rec.quantity_end
            else:
                record.quantity_begin = 0.0
            record.quantity_end = record.quantity_begin + \
                record.quantity_income - record.quantity_outcome

    # @api.depends('quantity_begin', 'quantity_income', 'quantity_outcome')
    # def _compute_quantity_end(self):
    #     for record in self:
    #         record.quantity_end = record.quantity_begin + record.quantity_income - record.quantity_outcome

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
                    date=line.date,
                )

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

    def _date_range_list(self, start_date, end_date):
        # Return generator for a list datetime.date objects (inclusive) between start_date and end_date (inclusive).
        curr_date = start_date
        while curr_date <= end_date:
            yield curr_date
            curr_date += timedelta(days=1)

    def _gather(self, product_id, distrib_id, date):
        removal_strategy_order = 'date DESC'

        domain = ['&', ('product_id', '=', product_id.id),
                  ('date', '=', date.strftime("%Y-%m-%d 00:00:00"))]
        domain = expression.AND([[('distrib_id', '=', distrib_id.id)], domain])

        # domain = expression.AND([[], domain])

        return self.search(domain, order=removal_strategy_order)

    def _quants_for_all_days(self, distrib_id, product_id, from_date):
        # report_period = self.env['ir.config_parameter'].sudo().get_param('distrib.report_distrib_quantity_period',
        #                                                                  default='12')
        # new_date = fields.Datetime.now() + relativedelta(months=int(report_period))
        # date_range = self._date_range_list(from_date, new_date)
        date_range = self._date_range_list(from_date, fields.Datetime.now())
        strategy_order = 'distrib_id,product_id,date'
        for date in date_range:
            domain = [('product_id', '=', product_id.id), ('distrib_id', '=', distrib_id.id),
                      ('date', '=', date.strftime("%Y-%m-%d 00:00:00"))]
            quants = self.search(domain, order=strategy_order)
            if not quants:
                quants.create({
                    'product_id': product_id.id,
                    'quantity_income': 0.0,
                    'quantity_outcome': 0.0,
                    'distrib_id': distrib_id and distrib_id.id,
                    'date': date.strftime("%Y-%m-%d 00:00:00"),
                })

    def _validate_totals(self, product_id, distrib_id, from_date):
        result = False
        totals = self.env['distrib.quant.totals'].sudo()
        all_totals = totals.search_count([])
        if all_totals == 0:
            return True
        strategy_order = 'distrib_id,product_id, date desc'
        domain = [('product_id', '=', product_id.id), ('distrib_id', '=',
                                                       distrib_id.id), ('date', '>=', from_date.strftime("%Y-%m-01 00:00:00"))]
        quants = totals.search(domain, order=strategy_order)
        for quant in quants:
            result = quant.write({'valid_rec': False})

        return result

    def _recalculate_results(self, product_id=None, distrib_id=None, from_date=None, with_validate=True):
        self = self.sudo()

        domain = []
        strategy_order = 'distrib_id,product_id,date'
        if product_id:
            domain.append(('product_id', '=', product_id.id))
        if distrib_id:
            domain.append(('distrib_id', '=', distrib_id.id))
        if from_date:
            domain.append(
                ('date', '>=', from_date.strftime("%Y-%m-%d 00:00:00")))
        quants = self.search(domain, order=strategy_order)
        begining_next_step = 0.0
        for counter, quant in enumerate(quants):
            if counter == 0:
                begining_next_step = quant.quantity_end
                quant.write({'valid_rec': with_validate, })
                continue
            quant.write({
                'quantity_begin': begining_next_step,
                'quantity_end': begining_next_step + quant.quantity_income - quant.quantity_outcome,
                'valid_rec': with_validate,
            })
            begining_next_step = begining_next_step + \
                quant.quantity_income - quant.quantity_outcome

        # self._validate_totals(product_id, distrib_id, from_date)

    @api.model
    def _update_available_quantity(self, product_id, quantity, distrib_id, in_out='inc', in_date=None):
        self = self.sudo()
        context = dict(self.env.context or {})
        recalc_totals = context.get('recalc_totals', False)
        quants = self._gather(product_id, distrib_id=distrib_id, date=in_date)
        quant = None
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute(
                "SELECT id FROM distrib_quant_history WHERE id IN %s ORDER BY date LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED",
                [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])

        dt = in_date or fields.Date.today()
        if in_date:
            dt = fields.Datetime.context_timestamp(self, in_date)

        was_valid = not self._validate_totals(
            product_id, distrib_id, in_date)

        if quant:
            quant.write({
                'quantity_income': quant.quantity_income + quantity if in_out == 'inc' else quant.quantity_income,
                'quantity_outcome': quant.quantity_outcome - quantity if in_out == 'out' else quant.quantity_outcome,
                'date': dt.strftime("%Y-%m-%d 00:00:00") if in_date else fields.Datetime.today,
                'valid_rec': was_valid,
            })
        else:
            self.create({
                'product_id': product_id.id,
                'quantity_income': quantity if in_out == 'inc' else 0.0,
                'quantity_outcome': -quantity if in_out == 'out' else 0.0,
                'distrib_id': distrib_id and distrib_id.id,
                'date': dt.strftime("%Y-%m-%d 00:00:00") if in_date else fields.Datetime.today,
                'valid_rec': was_valid,
            })

        # if with_all_days:
        #     self._quants_for_all_days(distrib_id, product_id, in_date)
        if not recalc_totals:
            self._recalculate_results(
            product_id=product_id, distrib_id=distrib_id, from_date=in_date, with_validate=False)   

    def balance_product_on_date(self, product_id, distrib_id, on_date=None):
        self = self.sudo()
        domain = []
        strategy_order = 'distrib_id,product_id,date desc'
        domain.append(('product_id', '=', product_id.id))
        domain.append(('distrib_id', '=', distrib_id.id))
        if on_date:
            domain.append(
                ('date', '<=', on_date.strftime("%Y-%m-%d 00:00:00")))

        quant = None
        quants = self.search(domain, order=strategy_order)
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute(
                "SELECT id FROM distrib_quant_history WHERE id IN %s ORDER BY distrib_id,product_id,date desc LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED",
                [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])

        if quant:
            return quant.quantity_end

        return 0.0

    def _recalculate_totals_by_days(self):
        self = self.sudo()
        quants = None
        self._cr.execute("""
                         SELECT FIRST (ID) AS ID
                            FROM
                                (
                                    SELECT
                                        ID,
                                        DISTRIB_ID,
                                        PRODUCT_ID,
                                        DATE
                                    FROM
                                        distrib_quant_history
                                    WHERE
			                            NOT VALID_REC
                                    ORDER BY
                                        DISTRIB_ID,
                                        PRODUCT_ID,
                                        DATE ASC
                                    FOR NO KEY UPDATE SKIP LOCKED
                                ) AS MAIN
                            GROUP BY
                                DISTRIB_ID,
                                PRODUCT_ID
                         """)
        stock_quant_result = self._cr.fetchall()
        if stock_quant_result:
            for quant in stock_quant_result:
                quants = self.browse(quant)
                self._quants_for_all_days(
                    quants.distrib_id, quants.product_id, quants.date)
                self._recalculate_results(
                    product_id=quants.product_id, distrib_id=quants.distrib_id, from_date=quants.date)
