from odoo import api, models, _, fields


class PartnersDistrib(models.Model):
    _inherit = "res.partner"

    guid = fields.Char(string='Guid 1C:Enterprise')
    distrib_ids = fields.One2many('distrib.distributors', 'partner_id', string='Distributor')

    def get_distributor_region(self):
        """Возвращает region_id первого дистрибутора, если он есть"""
        self.ensure_one()
        distributor = self.distrib_ids[:1]  # можно добавить фильтрацию, если нужно
        return distributor.region_id if distributor else False