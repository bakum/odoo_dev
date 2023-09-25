from odoo import models, fields, api, _, tools


class DistributorMoveLines(models.Model):
    _name = 'distrib.distributors.move.statistic'
    _auto = False

    distrib_id = fields.Many2one('distrib.distributors', 'Distributor',
                                 readonly=True)

    product_id = fields.Many2one(comodel_name='product.product',
                                 string="Product",
                                 readonly=True)
    date = fields.Date('Date', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    balance = fields.Float('Balance', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'distrib_distributors_move_statistic')
        self._cr.execute(
        """
        create or replace view distrib_distributors_move_statistic as (
        select min(id) as id,
            max(date::TIMESTAMP::DATE) as date,
            distrib_id, 
            product_id,
            sum(debit) as debit,
            sum(credit) as credit,
            sum(balance) as balance
        from distrib_distributors_move_line
        where state='done'
        group by distrib_id,product_id
        order by date
        )""")
