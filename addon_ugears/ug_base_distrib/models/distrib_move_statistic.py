from odoo import models, fields, api, _, tools


class DistributorMoveLinesStatistic(models.Model):
    _name = 'distrib.distributors.move.statistic'
    _auto = False

    distrib_id = fields.Many2one('distrib.distributors', 'Distributor',
                                 readonly=True)

    product_id = fields.Many2one(comodel_name='product.product',
                                 string="Product",
                                 readonly=True)
    product_category_id = fields.Many2one(comodel_name='product.category',
                                 string="Category",
                                 readonly=True)
    begin_ost = fields.Float('Begin', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance = fields.Float('Balance', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'distrib_distributors_move_statistic')
        self._cr.execute(
        """
        create or replace view distrib_distributors_move_statistic as (
        select min(quant.id) as id,
            line.distrib_id,
            line.product_id,
            line.product_category_id,
            max(quant.quantity) - sum(line.debit) +  sum(line.credit) as begin_ost,
            sum(line.debit) as debit,
            sum(line.credit) as credit,
            max(quant.quantity) as balance
        from distrib_distributors_move_line as line
        left join distrib_quant as quant
            on quant.product_id=line.product_id
                and quant.distrib_id=line.distrib_id
        where line.state='done'
        group by line.distrib_id, line.product_id,line.product_category_id
        order by line.product_id
        )""")
