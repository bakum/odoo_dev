from odoo import fields, models
from odoo.tools import create_index


class DistributoPointOfRelevance(models.Model):
    _name = 'distrib.point.relevance'
    _description = 'Point of Relevance'
    _order = 'distrib_id, product_id, date'

    distrib_id = fields.Many2one(
        'distrib.distributors', 'Distributor',
        default=lambda self: self.env.user.distrib_id.id,
        index=True, required=True)
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('type', '!=', 'service')]",
        ondelete='restrict', required=True, index=True)
    date = fields.Datetime('Relevance Date', readonly=True,
                           index=True, required=True, default=fields.Datetime.today)

    def init(self):
        create_index(self._cr, 'distrib_relevance_date_idx', 'distrib_point_relevance',
                     ["distrib_id, product_id, date"])
        
    def _get_relevance_point(self, begin_of_month=False):
        if begin_of_month:
            domain = [('date', '<=', fields.Datetime.today().strftime("%Y-%m-%d"))]
        else:
            domain = [('date', '<', fields.Datetime.today().strftime("%Y-%m-%d"))]
        return self.search(domain, order='date asc')   

    def _set_relevance_point(self, distrib_id, product_id, in_date):
        last_date = self.search([('distrib_id', '=', distrib_id.id),
                                ('product_id', '=', product_id.id)], order='date asc', limit=1)
        if last_date:
            last = last_date.date.strftime("%Y-%m-01")
            current = in_date.strftime("%Y-%m-01")
            if current <= last:
                last_date.update(
                    {'date': in_date.strftime("%Y-%m-01 00:00:00")})
        else:
            last_date.create({
                'date': in_date.strftime("%Y-%m-01 00:00:00"),
                'distrib_id': distrib_id.id,
                'product_id': product_id.id,
                })

    def _set_relevance(self, distrib_id, product_id):
        last_date = self.search([('distrib_id', '=', distrib_id),
                                ('product_id', '=', product_id)], order='date asc', limit=1)
        now = fields.Datetime.today()
        if last_date:
            last_date.update({'date': now})
        else:
            last_date.create({
                'date': now,
                'distrib_id': distrib_id,
                'product_id': product_id,
                })
