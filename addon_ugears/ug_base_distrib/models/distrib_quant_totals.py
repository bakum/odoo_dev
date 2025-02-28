from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import create_index
from datetime import timedelta


class DistributorQuantHistory(models.Model):
    _name = 'distrib.quant.totals'
    _description = 'Quants Totals'
    _order = 'distrib_id, product_id, date desc'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '!=', 'service')]",
        ondelete='restrict', required=True, index=True)

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
    valid_rec = fields.Boolean(
        'Record is valid', readonly=True, required=True, default=False)

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

    def init(self):
        create_index(self._cr, 'distrib_quant_totals_date_idx', 'distrib_quant_totals',
                     ["distrib_id, product_id, date desc"])
        create_index(self._cr, 'distrib_quant_totals_date_asc_idx', 'distrib_quant_totals',
                     ["distrib_id, product_id, date"])
        create_index(self._cr, 'distrib_quant_totals_distrib_product_idx', 'distrib_quant_totals',
                     ["distrib_id, product_id"])

    @api.depends('product_id', 'distrib_id', 'date', 'quantity_income', 'quantity_outcome')
    def _compute_quantity_begin(self):
        for record in self:
            prev = self.env['distrib.quant.totals']
            domain = [('distrib_id', '=', record.distrib_id.id), ('product_id', '=', record.product_id.id),
                      ('date', '<', record.date)]
            rec = prev.search(domain, order='date desc', limit=1)
            record.quantity_begin = 0.0 if not rec else rec.quantity_end
            record.quantity_end = record.quantity_begin + \
                record.quantity_income - record.quantity_outcome

    def _gather(self, product_id, distrib_id, date, valid=False):
        removal_strategy_order = 'date DESC'

        domain = [('distrib_id', '=', distrib_id), ('product_id', '=',
                                                    product_id), ('date', '=', date.strftime("%Y-%m-01 00:00:00"))]

        if valid:
            domain = expression.AND([[('valid_rec', '=', False)], domain])

        return self.search(domain, order=removal_strategy_order)

    def _month_range_list(self, start_date, end_date):
        # Return generator for a list datetime.date objects (inclusive) between start_date and end_date (inclusive).
        curr_date = start_date.replace(day=1, hour=0, minute=0, second=0)
        end_date = end_date.replace(day=1, hour=0, minute=0, second=0)
        while curr_date <= end_date:
            yield curr_date
            curr_date = (curr_date + timedelta(days=31)
                         ).replace(day=1, hour=0, minute=0, second=0)

    def _recalc_results(self, product_id=None, distrib_id=None, from_date=None, with_validate=True, begining_balance=0.0):
        self = self.sudo()

        domain = []
        strategy_order = 'distrib_id,product_id,date'
        if product_id:
            domain.append(('product_id', '=', product_id.id))
        if distrib_id:
            domain.append(('distrib_id', '=', distrib_id.id))
        begining_next_step = begining_balance
        date_range = self._month_range_list(from_date, fields.Datetime.today())
        for date in date_range:
            doma = domain.copy()
            doma.append(
                ('date', '=', date.strftime("%Y-%m-01 00:00:00")))
            quants = self.search(domain, order=strategy_order, limit=1)
            turnover = self._get_turnover_by_month(
                product_id, distrib_id, date)
            if not quants:
                turnover = self._get_turnover_by_month(
                    product_id, distrib_id, date)
                self.create({
                    'product_id': product_id.id,
                    'date': date,
                    'distrib_id': distrib_id.id,
                    'quantity_begin': begining_next_step,
                    'quantity_income': turnover['quantity_income'],
                    'quantity_outcome': turnover['quantity_outcome'],
                    'quantity_end': begining_next_step + turnover['quantity_income'] - turnover['quantity_outcome'],
                    'valid_rec': with_validate,
                })
                begining_next_step = begining_next_step + \
                    turnover['quantity_income'] - turnover['quantity_outcome']
            else:
                quants.write({
                    'quantity_begin': begining_next_step,
                    'quantity_income': turnover['quantity_income'],
                    'quantity_outcome': turnover['quantity_outcome'],
                    'quantity_end': begining_next_step + turnover['quantity_income'] - turnover['quantity_outcome'],
                    'valid_rec': with_validate,
                })
                begining_next_step = begining_next_step + \
                    turnover['quantity_income'] - turnover['quantity_outcome']
            doma = []

    def _recalculate_results(self, product_id=None, distrib_id=None, from_date=None, with_validate=True, begining_balance=0.0):
        return self._recalc_results(product_id=product_id, distrib_id=distrib_id, from_date=from_date, begining_balance=begining_balance)
        self = self.sudo()

        domain = []
        strategy_order = 'distrib_id,product_id,date'
        if product_id:
            domain.append(('product_id', '=', product_id.id))
        if distrib_id:
            domain.append(('distrib_id', '=', distrib_id.id))
        if from_date:
            domain.append(
                ('date', '>=', from_date.strftime("%Y-%m-01 00:00:00")))
        quants = self.search(domain, order=strategy_order)
        begining_next_step = begining_balance
        date_range = self._month_range_list(from_date, fields.Datetime.today())
        if not quants:
            for date in date_range:
                turnover = self._get_turnover_by_month(
                    product_id, distrib_id, date)
                self.create({
                    'product_id': product_id.id,
                    'date': date,
                    'distrib_id': distrib_id.id,
                    'quantity_begin': begining_next_step,
                    'quantity_income': turnover['quantity_income'],
                    'quantity_outcome': turnover['quantity_outcome'],
                    'quantity_end': begining_next_step + turnover['quantity_income'] - turnover['quantity_outcome'],
                    'valid_rec': with_validate,
                })
                begining_next_step = begining_next_step + \
                    turnover['quantity_income'] - turnover['quantity_outcome']
        for quant in quants:
            turnover = self._get_turnover_by_month(
                product_id, distrib_id, quant.date)
            quant.write({
                'quantity_begin': begining_next_step,
                'quantity_income': turnover['quantity_income'],
                'quantity_outcome': turnover['quantity_outcome'],
                'quantity_end': begining_next_step + turnover['quantity_income'] - turnover['quantity_outcome'],
                'valid_rec': with_validate,
            })
            begining_next_step = begining_next_step + \
                turnover['quantity_income'] - turnover['quantity_outcome']

    def _get_turnover_by_month(self, product_id, distrib_id, date):
        history = self.env['distrib.quant.history'].sudo()
        sql = "select id from DISTRIB_QUANT_HISTORY where product_id=%s and distrib_id=%s and date_trunc('month',date)::date='%s'" % (
            product_id.id, distrib_id.id, date.strftime("%Y-%m-01"))
        self._cr.execute(sql)
        stock_quant_result = self._cr.fetchall()
        if stock_quant_result:
            domain = [('id', 'in', list(entry[0]
                       for entry in stock_quant_result))]
            turnover = history.read_group(domain, [
                                          'product_id', 'distrib_id', 'quantity_income:sum', 'quantity_outcome:sum'], ['product_id', 'distrib_id'])
            if len(turnover) > 0:
                return {
                    'quantity_income': turnover[0]['quantity_income'],
                    'quantity_outcome': turnover[0]['quantity_outcome']
                }

            return {
                'quantity_income': 0.0,
                'quantity_outcome': 0.0
            }

    def _recalculate_totals(self):
        self = self.sudo()
        relevance = self.env['distrib.point.relevance'].sudo()
        all_totals = self.search_count([])
        if all_totals == 0:
            quants = None
            self._cr.execute("""
                            SELECT
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE) AS DATE,
                                FIRST (QUANTITY_BEGIN) QUANTITY_BEGIN,
                                SUM(QUANTITY_INCOME) QUANTITY_INCOME,
                                SUM(QUANTITY_OUTCOME) QUANTITY_OUTCOME,
                                LAST (QUANTITY_END) QUANTITY_END,
                                TRUE as valid_rec
                            FROM
                                DISTRIB_QUANT_HISTORY
                            GROUP BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            ORDER BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            """)
            stock_quant_result = self._cr.dictfetchall()
            self.search([]).unlink()
            if stock_quant_result:
                for quant in stock_quant_result:
                    quants = self._gather(
                        quant['product_id'], distrib_id=quant['distrib_id'], date=quant['date'])
                    quants.create(quant)
                    relevance._set_relevance(
                        quant['distrib_id'], quant['product_id'])

        else:
            sql = """
                            SELECT
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE) AS DATE,
                                FIRST (QUANTITY_BEGIN) QUANTITY_BEGIN,
                                SUM(QUANTITY_INCOME) QUANTITY_INCOME,
                                SUM(QUANTITY_OUTCOME) QUANTITY_OUTCOME,
                                LAST (QUANTITY_END) QUANTITY_END,
                                TRUE as valid_rec
                            FROM
                                DISTRIB_QUANT_HISTORY
                            where product_id=%s and DISTRIB_ID = %s and DATE_TRUNC('MONTH', date)::date >= '%s'
                            GROUP BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            ORDER BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            """
            
            all_relevance = relevance._get_relevance_point()
            for quants in all_relevance:
                sql1 = sql % (quants.product_id.id, quants.distrib_id.id, quants.date.strftime("%Y-%m-01"))
                domain = [('product_id', '=', quants.product_id.id),('distrib_id', '=', quants.distrib_id.id),('date', '>=', quants.date.strftime("%Y-%m-01"))]
                strategy_order = 'distrib_id,product_id,date'
                self.search(domain,order=strategy_order).unlink()
                self._cr.execute(sql1)
                stock_quant_result = self._cr.dictfetchall()
                if stock_quant_result:
                    for quant in stock_quant_result:
                        self.create(quant)
                relevance._set_relevance(quants.distrib_id.id, quants.product_id.id)  
                
    def _recalculate_totals_by_monts(self):
        return self._recalculate_totals()
        self = self.sudo()
        start_totals = self.search([], limit=1, order='date')
        history = self.env['distrib.quant.history'].sudo()
        start_history = history.search([], limit=1, order='date')
        back_number = True
        if start_history and start_totals:
            start_totals_date = start_totals.date.strftime("%Y-%m-01")
            start_history_date = start_history.date.strftime("%Y-%m-01")
            back_number = start_totals_date != start_history_date

        products_set_totals = self.read_group(
            [], fields=['product_id'], groupby=['product_id'])
        ids = list(entry['product_id'][0] for entry in products_set_totals)
        div = history.read_group([('product_id', 'not in', ids)], fields=[
                                 'product_id'], groupby=['product_id'])
        all_totals = self.search_count([])
        # there were no records or they were retroactive or there was no product(s) in the totals
        if all_totals == 0 or back_number or len(div) > 0 or True:
            quants = None
            self._cr.execute("""
                            SELECT
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE) AS DATE,
                                FIRST (QUANTITY_BEGIN) QUANTITY_BEGIN,
                                SUM(QUANTITY_INCOME) QUANTITY_INCOME,
                                SUM(QUANTITY_OUTCOME) QUANTITY_OUTCOME,
                                LAST (QUANTITY_END) QUANTITY_END,
                                TRUE as valid_rec
                            FROM
                                DISTRIB_QUANT_HISTORY
                            GROUP BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            ORDER BY
                                DISTRIB_ID,
                                PRODUCT_ID,
                                DATE_TRUNC('MONTH', DATE)
                            """)
            stock_quant_result = self._cr.dictfetchall()
            self.search([]).unlink()
            # quants
            if stock_quant_result:
                for quant in stock_quant_result:
                    quants = self._gather(
                        quant['product_id'], distrib_id=quant['distrib_id'], date=quant['date'])
                    # if quants and not quants.valid_rec:
                    #     quants.write(quant)
                    # elif not quants:
                    quants.create(quant)
                    relevance = self.env['distrib.point.relevance'].sudo()
                    relevance._set_relevance(
                        quant['distrib_id'], quant['product_id'])
            return

        not_valid_totals = self.search(
            [('valid_rec', '=', False)], order='distrib_id,product_id,date asc')
        begin_ost = 0
        for counter, tot in enumerate(not_valid_totals):
            begin_ost = tot.quantity_begin if counter == 0 else begin_ost
            sql = "select id from DISTRIB_QUANT_HISTORY where product_id=%s and distrib_id=%s and date_trunc('month',date)::date='%s'" % (
                tot.product_id.id, tot.distrib_id.id, tot.date.strftime("%Y-%m-01"))
            self._cr.execute(sql)
            stock_quant_result = self._cr.fetchall()
            if stock_quant_result:
                domain = [('id', 'in', list(entry[0]
                           for entry in stock_quant_result))]

                turnover = history.read_group(domain, [
                                              'product_id', 'distrib_id', 'quantity_income:sum', 'quantity_outcome:sum'], ['product_id', 'distrib_id'])
                if len(turnover) > 0:
                    end_ost = begin_ost + \
                        turnover[0]['quantity_income'] - \
                        turnover[0]['quantity_outcome']
                    tot.write({
                        'quantity_begin': begin_ost,
                        'quantity_income': turnover[0]['quantity_income'],
                        'quantity_outcome': turnover[0]['quantity_outcome'],
                        'quantity_end': end_ost,
                        'valid_rec': True,
                    })
                else:
                    end_ost = begin_ost
                    tot.write({
                        'quantity_begin': begin_ost,
                        'quantity_income': 0,
                        'quantity_outcome': 0,
                        'quantity_end': end_ost,
                        'valid_rec': True,
                    })
                begin_ost = end_ost
