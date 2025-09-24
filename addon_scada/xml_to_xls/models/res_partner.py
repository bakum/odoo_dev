from odoo import api, models, _, fields


class PartnersDistrib(models.Model):
    _inherit = "res.partner"

    guid = fields.Char(string='Guid 1C:Enterprise')
    okpo_code= fields.Char(string='OKPO Code')
    name_eng = fields.Char(string='Name in English')
    address_eng = fields.Text(string='Address in English')
    is_organization = fields.Boolean(string='Is Organization', default=False)