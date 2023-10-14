from odoo import models, fields, tools


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


class MoveLinesChannelsStatistic(models.Model):
    _name = 'distrib.move.channels.statistic'
    _auto = False

    distrib_id = fields.Many2one('distrib.distributors', 'Distributor',
                                 readonly=True)

    product_id = fields.Many2one(comodel_name='product.product',
                                 string="Product",
                                 readonly=True)
    product_category_id = fields.Many2one(comodel_name='product.category',
                                          string="Category",
                                          readonly=True)
    currency_id = fields.Many2one(comodel_name='res.currency',
                                          string="Currency",
                                          readonly=True)
    channel_id = fields.Many2one(comodel_name='distrib.sales.channels',
                                          string="Sales Channel",
                                          readonly=True)
    qtt = fields.Float('Quantity', readonly=True)
    total = fields.Float('Total', readonly=True)
    avg_price = fields.Float('Average Price', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'distrib_move_channels_statistic')
        self._cr.execute(
            """
            create or replace view distrib_move_channels_statistic as (
            select min(line.id) as id,
                line.distrib_id,
                line.product_id,
                line.product_category_id,
                line.currency_id,
                line.channel_id,
                sum(line.credit) as qtt,
                sum(line.price_total) as total,
                case
                    when sum(line.credit) = 0 then 0
                else
                    sum(line.price_total)/sum(line.credit)
                end as avg_price
            from distrib_distributors_move_line as line
            where line.state='done' and line.operation='out'
            group by line.distrib_id, line.product_id,line.product_category_id, line.currency_id, line.channel_id
            order by line.product_id
            )""")

