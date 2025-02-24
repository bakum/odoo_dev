from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import create_index


class DistributorQuantHistory(models.Model):
    _name = 'distrib.quant.totals'
    _description = 'Quants Totals'
    _order = 'distrib_id, product_id, date desc'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '!=', 'service')]",
        ondelete='restrict', required=True, index=True)

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

    def _recalculate_totals_by_monts(self):
        self = self.sudo()
        start_totals = self.search([], limit=1, order='date')
        history = self.env['distrib.quant.history'].sudo()
        start_history = history.search([], limit=1, order='date')
        back_number = True
        if start_history and start_totals:
            start_totals_date = start_totals.date.strftime("%Y-%m-01")
            start_history_date = start_history.date.strftime("%Y-%m-01")
            back_number = start_totals_date != start_history_date

        all_totals = self.search_count([])
        if all_totals == 0 or back_number:
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
            self.unlink()
            # quants
            if stock_quant_result:
                for quant in stock_quant_result:
                    quants = self._gather(
                        quant['product_id'], distrib_id=quant['distrib_id'], date=quant['date'])
                    if quants and not quants.valid_rec:
                        quants.write(quant)
                    elif not quants:
                        quants.create(quant)
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
