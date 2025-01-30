from odoo import api, models, _, fields


class PartnersDistrib(models.Model):
    _inherit = "res.partner"

    guid = fields.Char(string='Guid 1C:Enterprise')
    distrib_ids = fields.One2many('distrib.distributors', 'partner_id', string='Distributor')
