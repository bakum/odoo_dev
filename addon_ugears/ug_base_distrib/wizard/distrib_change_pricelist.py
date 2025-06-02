from odoo import models, fields


class DistribChangePricelist(models.TransientModel):
    _name = "distrib.change.pricelist"
    _description = "Change Distributor Pricelist"

    distrib_id = fields.Many2one('distrib.distributors', 'Distributor', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)

    def save_pricelist(self):
        if (self.distrib_id.pricelist_id.id == self.pricelist_id.id):
            return
        sql = """
            UPDATE distrib_distributors
            SET pricelist_id = %s
            WHERE id = %s
        """ % (self.pricelist_id.id, self.distrib_id.id)
        self._cr.execute(sql)
        self._cr.commit()
