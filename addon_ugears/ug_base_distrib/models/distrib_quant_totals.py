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
    
    date = fields.Datetime('Incoming Date', readonly=True, index=True, required=True, default=fields.Datetime.today)
    valid_rec = fields.Boolean('Record is valid', readonly=True, required=True, default=False)

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
            record.quantity_end = record.quantity_begin + record.quantity_income - record.quantity_outcome   

    def _gather(self, product_id, distrib_id, date):
        removal_strategy_order = 'date DESC'

        domain = [('distrib_id', '=', distrib_id), ('product_id', '=', product_id), ('date', '=', date.strftime("%Y-%m-01 00:00:00"))]
        # domain = expression.AND([[('valid_rec', '=', False)], domain])

        return self.search(domain, order=removal_strategy_order)  

    def _recalculate_totals_by_monts(self):
        self = self.sudo()
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
                            TRUE AS VALID_REC
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
        # quants
        if stock_quant_result:
            for quant in stock_quant_result:
                quants = self._gather(quant['product_id'], distrib_id=quant['distrib_id'], date=quant['date'])  
                if quants and not quants.valid_rec:
                    quants.write(quant)
                elif not quants:
                    quants.create(quant)   